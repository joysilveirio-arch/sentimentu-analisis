import re
import html
import unicodedata
from sqlalchemy import text as sql_text

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
MENTION_PATTERN = re.compile(r"@\w+")
HASHTAG_PATTERN = re.compile(r"#(\w+)")
MULTI_WS = re.compile(r"\s+")
HTML_TAG = re.compile(r"<[^>]+>")
# Emoji and their common sequence components (ZWJ, variation selectors,
# keycap marks, skin tones, regional flags, and tag characters). Letters and
# digits are intentionally outside these ranges.
EMOJI_PATTERN = re.compile(
    "["
    "\\U0001F000-\\U0001FAFF"
    "\\U0001FC00-\\U0001FFFD"
    "\\u2300-\\u23FF"
    "\\u2600-\\u27BF"
    "\\u2B00-\\u2BFF"
    "\\uFE0F\\u200D\\u20E3"
    "\\U000E0020-\\U000E007F"
    "]"
)

def normalize_unicode(text):
    if not text:
        return ""
    return unicodedata.normalize("NFC", text)

def clean_text(text):
    if text is None:
        return ""
    t = str(text)
    t = html.unescape(t)
    t = HTML_TAG.sub(" ", t)
    t = URL_PATTERN.sub(" ", t)
    t = MENTION_PATTERN.sub(" ", t)
    t = HASHTAG_PATTERN.sub(r"\1", t)
    t = normalize_unicode(t)
    t = EMOJI_PATTERN.sub(" ", t)
    t = t.replace("\u200b", "").replace("\ufeff", "")
    t = MULTI_WS.sub(" ", t)
    return t.strip()


def _cleaning_scope_query():
    from backend import db
    from backend.models.facebook_record import FacebookRecord

    return FacebookRecord.query.filter(
        FacebookRecord.is_clean.is_(True),
        FacebookRecord.is_duplicate.is_not(True),
        FacebookRecord.text.isnot(None),
        db.func.trim(FacebookRecord.text) != "",
    ).order_by(FacebookRecord.id)


def build_cleaning_preview():
    """Build an in-memory before/after preview without writing to the database."""
    from backend import db
    from backend.models.facebook_record import FacebookRecord

    records = _cleaning_scope_query().all()
    preview = []
    nonempty = empty = 0
    for record in records:
        cleaned = clean_text(record.text)
        status = "Cleaned" if cleaned else "Mamuk depois cleaning"
        nonempty += bool(cleaned)
        empty += not bool(cleaned)
        preview.append({
            "id": record.id,
            "text": record.text,
            "cleaned_text": cleaned,
            "status": status,
        })

    total_records = FacebookRecord.query.count()
    duplicate_records = FacebookRecord.query.filter(
        FacebookRecord.is_duplicate.is_(True)
    ).count()
    missing_records = FacebookRecord.query.filter(
        db.or_(
            FacebookRecord.text.is_(None),
            db.func.trim(FacebookRecord.text) == "",
        )
    ).count()
    return {
        "stats": {
            "total_records": total_records,
            "clean_records": len(records),
            "cleaned_text_nonempty": int(nonempty),
            "cleaned_text_empty": int(empty),
            "duplicate_records": duplicate_records,
            "missing_text_records": missing_records,
        },
        "records": preview,
    }


def run_cleaning():
    """Persist only cleaned_text for the eligible clean records."""
    from backend import db

    preview = build_cleaning_preview()
    updates = [
        {"record_id": row["id"], "cleaned_text": row["cleaned_text"]}
        for row in preview["records"]
    ]
    if updates:
        # SQL text deliberately bypasses ORM onupdate hooks, so this operation
        # changes exactly one existing column and leaves flags/timestamps intact.
        db.session.execute(
            sql_text("UPDATE facebook_records SET cleaned_text = :cleaned_text WHERE id = :record_id"),
            updates,
        )
        db.session.commit()
    preview["updated"] = len(updates)
    return preview


def reprocess_clean_records():
    """Compatibility wrapper used by maintenance scripts and tests."""
    result = run_cleaning()
    return {
        "processed": result["stats"]["clean_records"],
        "updated": result["updated"],
        "empty_record_ids": [
            row["id"] for row in result["records"] if not row["cleaned_text"]
        ],
    }

def detect_language(text):
    if not text:
        return "unknown"
    t = text.lower()
    tetum_kw = ["diak", "furak", "gosta", "la", "ita", "nia", "ba", "ho", "mak", "kona"]
    indo_kw = ["yang", "dan", "saya", "kamu", "bagus", "cantik", "sekali", "tidak", "adalah"]
    pt_kw = ["você", "não", "muito", "bonita", "obrigada", "para", "com", "que"]
    en_kw = ["the", "and", "you", "good", "beautiful", "love", "is", "with"]

    scores = {
        "tet": sum(1 for w in tetum_kw if f" {w} " in f" {t} "),
        "ind": sum(1 for w in indo_kw if f" {w} " in f" {t} "),
        "por": sum(1 for w in pt_kw if f" {w} " in f" {t} "),
        "eng": sum(1 for w in en_kw if f" {w} " in f" {t} "),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"

def normalize_gender(raw):
    if not raw:
        return "UNKNOWN"
    g = str(raw).strip().upper()
    if g in {"MALE", "M"}:
        return "MALE"
    if g in {"FEMALE", "F"}:
        return "FEMALE"
    if g in {"NEUTER", "N"}:
        return "NEUTER"
    return "UNKNOWN"
