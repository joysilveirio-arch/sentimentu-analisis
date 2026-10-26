"""Dataset import, cleaning, and validation tests.

Covers:
- CSV import (valid, duplicate, missing, malformed)
- Multiline text preservation
- Multilingual text handling (Tetum, Indonesian, English, Portuguese)
- Emoji, URLs, mentions, hashtags
- Gender normalization
- Numeric conversion
- Date parsing
- Empty text handling
- Duplicate detection
- Column mapping
"""

import os
import io
import tempfile
import pytest
from datetime import datetime

from backend import db
from backend.models.facebook_record import FacebookRecord
from backend.models.import_history import ImportHistory
from backend.services.data_service import import_csv
from backend.services.cleaning_service import (
    clean_text, detect_language, normalize_gender,
)
from backend.utils.validators import safe_int, safe_float


# ═══════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════

@pytest.fixture
def sample_csv(tmp_path):
    """Create a small multilingual CSV for testing."""
    content = (
        '"id","commentId","author/name","author/id","author/gender",'
        '"postTitle","text","date","likesCount","commentsCount",'
        '"facebookUrl","profileName","attachments/0/__typename","parentComment/id"\n'
        '"c1","cmt1","Maria","u1","FEMALE","First Look","Furak los! Diak tebes 🥰",'
        '"2026-10-01T10:00:00.000Z","12","3","https://fb.com/c1","Juliana",'
        '"Sticker",""\n'
        '"c2","cmt2","João","u2","MALE","First Look","Bagus sekali! Good job",'
        '"2026-10-02T11:00:00.000Z","5","1","https://fb.com/c2","Juliana",'
        '"Image",""\n'
        '"c3","cmt3","Ana","u3","FEMALE","First Look","Aat los, triste 😞",'
        '"2026-10-03T12:00:00.000Z","2","0","https://fb.com/c3","Juliana",'
        '"",""\n'
        '"c4","cmt4","Pedro","u4","MALE","First Look","Excelente! Muito obrigada",'
        '"2026-10-04T13:00:00.000Z","20","8","https://fb.com/c4","Juliana",'
        '"Image",""\n'
    )
    f = tmp_path / "dataset_test.csv"
    f.write_text(content, encoding="utf-8")
    return str(f)


@pytest.fixture
def empty_csv(tmp_path):
    """CSV with header but no rows."""
    content = (
        '"id","text","author/name","author/gender","date"\n'
    )
    f = tmp_path / "empty.csv"
    f.write_text(content, encoding="utf-8")
    return str(f)


@pytest.fixture
def malformed_csv(tmp_path):
    """CSV with broken rows (wrong column count)."""
    content = (
        '"id","text","author/name"\n'
        '"c1","hello","Maria"\n'
        '"c2"\n'                              # missing columns
        '"c3","world","João","extra"\n'       # extra column
    )
    f = tmp_path / "malformed.csv"
    f.write_text(content, encoding="utf-8")
    return str(f)


@pytest.fixture
def duplicate_csv(tmp_path):
    """CSV with duplicate record IDs."""
    content = (
        '"id","text","author/name"\n'
        '"dup1","hello","A"\n'
        '"dup1","hello again","A"\n'
        '"dup2","world","B"\n'
    )
    f = tmp_path / "duplicate.csv"
    f.write_text(content, encoding="utf-8")
    return str(f)


# ═══════════════════════════════════════════════
# 1. IMPORT — VALID CSV
# ═══════════════════════════════════════════════

class TestImportValidCsv:
    def test_import_success(self, app, sample_csv):
        with app.app_context():
            hist = import_csv(sample_csv)
            assert hist.status == "success"
            assert hist.imported_rows == 4
            assert hist.failed_rows == 0
            assert FacebookRecord.query.count() == 4

    def test_import_preserves_text(self, app, sample_csv):
        with app.app_context():
            import_csv(sample_csv)
            rec = FacebookRecord.query.filter_by(facebook_record_id="c1").first()
            assert rec is not None
            assert "Furak los" in rec.text
            assert "🥰" in rec.text

    def test_import_parses_date(self, app, sample_csv):
        with app.app_context():
            import_csv(sample_csv)
            rec = FacebookRecord.query.filter_by(facebook_record_id="c1").first()
            assert rec.date is not None
            assert rec.date.year == 2026
            assert rec.date.month == 10

    def test_import_parses_numeric(self, app, sample_csv):
        with app.app_context():
            import_csv(sample_csv)
            rec = FacebookRecord.query.filter_by(facebook_record_id="c4").first()
            assert rec.likes_count == 20
            assert rec.comments_count == 8

    def test_import_normalizes_gender(self, app, sample_csv):
        with app.app_context():
            import_csv(sample_csv)
            r1 = FacebookRecord.query.filter_by(facebook_record_id="c1").first()
            r2 = FacebookRecord.query.filter_by(facebook_record_id="c2").first()
            assert r1.gender == "FEMALE"
            assert r2.gender == "MALE"

    def test_import_detects_language(self, app, sample_csv):
        with app.app_context():
            import_csv(sample_csv)
            r1 = FacebookRecord.query.filter_by(facebook_record_id="c1").first()
            assert r1.language in ("tet", "unknown", "ind", "eng")

    def test_import_creates_history_record(self, app, sample_csv):
        with app.app_context():
            hist = import_csv(sample_csv)
            assert ImportHistory.query.count() == 1
            saved = ImportHistory.query.first()
            assert saved.total_rows == 4
            assert saved.imported_rows == 4


# ═══════════════════════════════════════════════
# 2. IMPORT — DUPLICATE
# ═══════════════════════════════════════════════

class TestImportDuplicates:
    def test_duplicate_ids_detected(self, app, duplicate_csv):
        with app.app_context():
            hist = import_csv(duplicate_csv)
            assert hist.duplicate_rows >= 1
            assert FacebookRecord.query.count() == 2

    def test_reimport_same_file_no_duplicate_insert(self, app, sample_csv):
        with app.app_context():
            import_csv(sample_csv)
            hist2 = import_csv(sample_csv)
            assert hist2.duplicate_rows == 4
            assert hist2.imported_rows == 0
            assert FacebookRecord.query.count() == 4


# ═══════════════════════════════════════════════
# 3. IMPORT — EMPTY
# ═══════════════════════════════════════════════

class TestImportEmpty:
    def test_empty_csv_no_crash(self, app, empty_csv):
        with app.app_context():
            hist = import_csv(empty_csv)
            assert hist.status == "success"
            assert hist.total_rows == 0
            assert hist.imported_rows == 0

    def test_nonexistent_file(self, app):
        with app.app_context():
            hist = import_csv("/tmp/nonexistent_xyz_123.csv")
            assert hist.status == "failed"


# ═══════════════════════════════════════════════
# 4. IMPORT — MALFORMED
# ═══════════════════════════════════════════════

class TestImportMalformed:
    def test_malformed_rows_handled(self, app, malformed_csv):
        with app.app_context():
            hist = import_csv(malformed_csv)
            # Should not crash; some rows fail gracefully
            assert hist is not None
            assert FacebookRecord.query.count() >= 1


# ═══════════════════════════════════════════════
# 5. CLEANING — TEXT
# ═══════════════════════════════════════════════

class TestCleaningText:
    def test_clean_basic(self):
        assert clean_text("Hello world") == "Hello world"

    def test_clean_url_removed(self):
        result = clean_text("Check https://example.com now")
        assert "http" not in result
        assert "example.com" not in result

    def test_clean_html_tags_removed(self):
        result = clean_text("<b>bold</b> text")
        assert "<" not in result
        assert ">" not in result
        assert "bold" in result

    def test_clean_mentions_removed(self):
        result = clean_text("Hello @maria world")
        assert "@" not in result

    def test_clean_hashtags_keep_word(self):
        result = clean_text("Hello #baliwedding")
        assert "#" not in result
        assert "baliwedding" in result

    def test_clean_multiple_whitespace(self):
        assert clean_text("a  b   c") == "a b c"

    def test_clean_newlines(self):
        assert clean_text("line1\nline2") == "line1 line2"

    def test_clean_empty(self):
        assert clean_text("") == ""
        assert clean_text(None) == ""

    def test_clean_none_string(self):
        assert clean_text("None") == "None"

    def test_clean_removes_emoji(self):
        assert clean_text("Posting the video tomorrow😍") == "Posting the video tomorrow"
        assert clean_text("Bali Wedding With Me❤️") == "Bali Wedding With Me"
        assert clean_text("❤️") == ""
        assert clean_text("Parabens Sista💍❤🫶") == "Parabens Sista"
        assert clean_text("good job 🥰😊🎉🎊💗💕") == "good job"

    def test_clean_preserves_accented(self):
        result = clean_text("café bonita")
        assert "é" in result or "café" in result

    def test_clean_preserves_tetum(self):
        result = clean_text("hau nia diak tebes")
        assert "diak" in result
        assert "tebes" in result


# ═══════════════════════════════════════════════
# 6. CLEANING — LANGUAGE DETECTION
# ═══════════════════════════════════════════════

class TestLanguageDetection:
    def test_detect_english(self):
        result = detect_language("the good and beautiful")
        assert result in ("eng", "unknown")

    def test_detect_tetum(self):
        result = detect_language("hau nia diak ba ita")
        assert result in ("tet", "unknown")

    def test_detect_indonesian(self):
        result = detect_language("saya suka yang bagus")
        assert result in ("ind", "unknown")

    def test_detect_portuguese(self):
        result = detect_language("muito bonita você obrigada")
        assert result in ("por", "unknown")

    def test_detect_empty(self):
        assert detect_language("") == "unknown"

    def test_detect_none(self):
        assert detect_language(None) == "unknown"

    def test_detect_short_text(self):
        assert detect_language("ok") == "unknown"


# ═══════════════════════════════════════════════
# 7. CLEANING — GENDER
# ═══════════════════════════════════════════════

class TestGenderNormalization:
    def test_male_uppercase(self):
        assert normalize_gender("MALE") == "MALE"

    def test_male_lowercase(self):
        assert normalize_gender("male") == "MALE"

    def test_female(self):
        assert normalize_gender("FEMALE") == "FEMALE"

    def test_f_short(self):
        assert normalize_gender("F") == "FEMALE"

    def test_m_short(self):
        assert normalize_gender("M") == "MALE"

    def test_neuter(self):
        assert normalize_gender("NEUTER") == "NEUTER"

    def test_unknown_empty(self):
        assert normalize_gender("") == "UNKNOWN"

    def test_unknown_none(self):
        assert normalize_gender(None) == "UNKNOWN"

    def test_unknown_garbage(self):
        assert normalize_gender("xyz") == "UNKNOWN"


# ═══════════════════════════════════════════════
# 8. VALIDATORS
# ═══════════════════════════════════════════════

class TestValidators:
    def test_safe_int_valid(self):
        assert safe_int("42") == 42

    def test_safe_int_float_string(self):
        assert safe_int("42.9") == 42

    def test_safe_int_empty(self):
        assert safe_int("") == 0

    def test_safe_int_none(self):
        assert safe_int(None) == 0

    def test_safe_int_invalid(self):
        assert safe_int("abc") == 0

    def test_safe_int_negative(self):
        assert safe_int("-5") == -5

    def test_safe_float_valid(self):
        assert safe_float("3.14") == 3.14

    def test_safe_float_empty(self):
        assert safe_float("") == 0.0

    def test_safe_float_invalid(self):
        assert safe_float("xyz") == 0.0


# ═══════════════════════════════════════════════
# 9. MULTILINGUAL — END-TO-END
# ═══════════════════════════════════════════════

class TestMultilingual:
    def test_tetum_text_cleaned(self):
        r = clean_text("Furak los! Hau gosta tebes 🥰")
        assert "Furak" in r
        assert "gosta" in r

    def test_indonesian_text_cleaned(self):
        r = clean_text("Bagus sekali, saya suka!")
        assert "Bagus" in r
        assert "suka" in r

    def test_portuguese_text_cleaned(self):
        r = clean_text("Muito bonita, obrigada!")
        assert "bonita" in r
        assert "obrigada" in r

    def test_english_text_cleaned(self):
        r = clean_text("Beautiful picture, love it!")
        assert "Beautiful" in r
        assert "love" in r

    def test_mixed_language(self):
        r = clean_text("Furak los! Good job diak")
        assert "Furak" in r
        assert "Good" in r
        assert "diak" in r


# ═══════════════════════════════════════════════
# 10. EDGE CASES
# ═══════════════════════════════════════════════

class TestEdgeCases:
    def test_very_long_text(self):
        long_text = "word " * 5000
        r = clean_text(long_text)
        assert len(r) > 0

    def test_only_emoji(self):
        assert clean_text("🥰❤️🔥👩🏽‍💻🇹🇱1️⃣") == "1"

    def test_clean_preserves_numbers_negation_and_multilingual_text(self):
        sample = "La lae labele laos la'os not no never nao não sem tanpa tidak bukan belum jangan 123 Tetum bagus English"
        assert clean_text(sample) == sample

    def test_clean_removes_emoji_and_other_noise(self):
        sample = '<b>La labele 42</b> #diak @maria https://example.com 🥰'
        assert clean_text(sample) == "La labele 42 diak"

    def test_only_url(self):
        r = clean_text("https://example.com")
        assert r == "" or "http" not in r

    def test_only_whitespace(self):
        assert clean_text("     ") == ""

    def test_unicode_special_chars(self):
        r = clean_text("Ñoño café résumé")
        assert "Ñ" in r or "ño" in r

    def test_zero_width_space(self):
        r = clean_text("hello\u200bworld")
        assert "\u200b" not in r

    def test_bom_removed(self):
        r = clean_text("\ufeffhello")
        assert "\ufeff" not in r

    def test_quoted_text_preserved(self):
        r = clean_text('She said "hello"')
        assert "hello" in r


# ═══════════════════════════════════════════════
# 11. COLUMN MAPPING
# ═══════════════════════════════════════════════

class TestColumnMapping:
    def test_column_map_exists(self):
        from backend.services.data_service import COLUMN_MAP
        assert "id" in COLUMN_MAP
        assert "text" in COLUMN_MAP
        assert "author/name" in COLUMN_MAP

    def test_all_expected_columns_mapped(self):
        from backend.services.data_service import COLUMN_MAP
        expected = ["id", "commentId", "author/name", "text", "date",
                    "likesCount", "commentsCount", "author/gender"]
        for col in expected:
            assert col in COLUMN_MAP


# ═══════════════════════════════════════════════
# 12. DATABASE INTEGRITY
# ═══════════════════════════════════════════════

class TestDatabaseIntegrity:
    def test_unique_facebook_record_id(self, app, sample_csv):
        with app.app_context():
            import_csv(sample_csv)
            ids = [r.facebook_record_id for r in FacebookRecord.query.all()]
            assert len(ids) == len(set(ids))

    def test_record_has_created_at(self, app, sample_csv):
        with app.app_context():
            import_csv(sample_csv)
            rec = FacebookRecord.query.first()
            assert rec.created_at is not None

    def test_import_history_linked_to_user(self, app, sample_csv):
        with app.app_context():
            from backend.models.user import User
            admin = User(username="admin2", email="a2@x.com", role="ADMIN")
            admin.set_password("x")
            db.session.add(admin)
            db.session.commit()
            hist = import_csv(sample_csv, user_id=admin.id)
            assert hist.user_id == admin.id
