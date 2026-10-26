from datetime import datetime
import csv
import io

from backend import db
from backend.models.facebook_record import FacebookRecord
from backend.models.sentiment_result import SentimentResult
from backend.services.cleaning_service import reprocess_clean_records
from backend.services.sentiment_service import analyze_records_batch


def test_unauthenticated_data_access(client):
    response = client.get("/api/data")
    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login?")

def test_dashboard_overview(user_client):
    r = user_client.get("/api/dashboard/overview")
    assert r.status_code == 200
    d = r.get_json()["data"]
    assert "total_records" in d
    assert "positive" in d

def test_dashboard_sentiment(user_client):
    r = user_client.get("/api/dashboard/sentiment")
    assert r.status_code == 200
    assert isinstance(r.get_json()["data"], list)


def test_dashboard_endpoints_use_only_clean_records(app, user_client):
    with app.app_context():
        db.session.add_all([
            FacebookRecord(facebook_record_id="clean-1", text="good", cleaned_text="good",
                           is_clean=True, is_duplicate=False, sentiment="Positive",
                           gender="FEMALE", author_name="Clean Author", date=datetime(2026, 1, 1),
                           likes_count=3, comments_count=1),
            FacebookRecord(facebook_record_id="clean-2", text="bad", cleaned_text="bad",
                           is_clean=True, is_duplicate=False, sentiment="Negative",
                           gender="MALE", author_name="Other Author", date=datetime(2026, 1, 2),
                           likes_count=5, comments_count=2),
            FacebookRecord(facebook_record_id="duplicate", text="duplicate", cleaned_text="duplicate",
                           is_clean=True, is_duplicate=True, sentiment="Positive",
                           gender="FEMALE", author_name="Duplicate Author", date=datetime(2026, 1, 1),
                           likes_count=100, comments_count=100),
            FacebookRecord(facebook_record_id="missing", text="", cleaned_text="",
                           is_clean=False, is_duplicate=False, sentiment="Neutral",
                           gender="UNKNOWN", author_name="Missing Author", date=datetime(2026, 1, 1),
                           likes_count=200, comments_count=200),
        ])
        db.session.commit()

    overview = user_client.get("/api/dashboard/overview").get_json()["data"]
    sentiment = user_client.get("/api/dashboard/sentiment").get_json()["data"]
    trends = user_client.get("/api/dashboard/trends").get_json()["data"]
    engagement = user_client.get("/api/dashboard/engagement").get_json()["data"]
    gender = user_client.get("/api/dashboard/gender").get_json()["data"]
    authors = user_client.get("/api/dashboard/authors").get_json()["data"]

    assert overview["total_records"] == 2
    assert overview["total_likes"] == 8
    assert overview["total_comments"] == 3
    assert sum(row["value"] for row in sentiment) == 2
    assert sum(row[label] for row in trends for label in ("Positive", "Negative", "Neutral", "Unlabeled")) == 2
    assert sum(row["likes"] for row in engagement) == 8
    assert sum(row["comments"] for row in engagement) == 3
    assert sum(row["value"] for row in gender) == 2
    assert sum(row["count"] for row in authors) == 2


def test_reanalyzing_sentiment_updates_existing_result(app):
    with app.app_context():
        record = FacebookRecord(
            facebook_record_id="sentiment-1", text="good", cleaned_text="good",
            is_clean=True, is_duplicate=False,
        )
        db.session.add(record)
        db.session.commit()

        assert analyze_records_batch() == 1
        assert analyze_records_batch() == 1
        assert SentimentResult.query.filter_by(record_id=record.id).count() == 1


def test_reprocess_clean_records_preserves_flags_and_reports_empty_text(app):
    with app.app_context():
        eligible = FacebookRecord(
            facebook_record_id="reclean-1", text="La 42 😍 #diak",
            cleaned_text="La 42 😍 diak", is_clean=True, is_duplicate=False,
        )
        emoji_only = FacebookRecord(
            facebook_record_id="reclean-2", text="❤️",
            cleaned_text="❤️", is_clean=True, is_duplicate=False,
        )
        unclean = FacebookRecord(
            facebook_record_id="reclean-3", text="text 😍",
            cleaned_text="text 😍", is_clean=False, is_duplicate=False,
        )
        duplicate = FacebookRecord(
            facebook_record_id="reclean-4", text="text 😍",
            cleaned_text="text 😍", is_clean=True, is_duplicate=True,
        )
        db.session.add_all([eligible, emoji_only, unclean, duplicate])
        db.session.commit()

        result = reprocess_clean_records()

        assert result["processed"] == 2
        assert result["empty_record_ids"] == [emoji_only.id]
        assert eligible.cleaned_text == "La 42 diak"
        assert emoji_only.cleaned_text == ""
        assert unclean.cleaned_text == "text 😍"
        assert duplicate.cleaned_text == "text 😍"
        assert eligible.is_clean is True and emoji_only.is_clean is True
        assert unclean.is_clean is False and duplicate.is_clean is True


def test_dataset_api_includes_original_and_cleaned_text_and_searches_both(app, user_client):
    with app.app_context():
        db.session.add(FacebookRecord(
            facebook_record_id="dataset-before-after",
            text="Raw source wording", cleaned_text="cleaned searchable phrase",
            is_clean=True, is_duplicate=False,
        ))
        db.session.commit()

    page = user_client.get("/dataset")
    assert page.status_code == 200
    result = user_client.get("/api/data?search=searchable").get_json()
    record = result["data"][0]
    assert record["text"] == "Raw source wording"
    assert record["cleaned_text"] == "cleaned searchable phrase"


def test_dataset_api_keeps_search_filters_and_pagination(app, user_client):
    with app.app_context():
        db.session.add_all([
            FacebookRecord(facebook_record_id="page-a", text="shared alpha", cleaned_text="alpha",
                           sentiment="Positive", gender="FEMALE", is_clean=True, is_duplicate=False),
            FacebookRecord(facebook_record_id="page-b", text="shared beta", cleaned_text="beta",
                           sentiment="Negative", gender="MALE", is_clean=True, is_duplicate=False),
            FacebookRecord(facebook_record_id="page-dup", text="shared duplicate", cleaned_text="duplicate",
                           sentiment="Positive", gender="FEMALE", is_clean=True, is_duplicate=True),
        ])
        db.session.commit()

    page = user_client.get("/api/data?search=shared&page=1&per_page=1").get_json()
    assert page["pagination"]["total"] == 2
    assert page["pagination"]["pages"] == 2
    assert len(page["data"]) == 1
    filtered = user_client.get(
        "/api/data?search=shared&sentiment=Positive&gender=FEMALE&per_page=10"
    ).get_json()
    assert filtered["pagination"]["total"] == 1
    assert filtered["data"][0]["facebook_record_id"] == "page-a"


def test_cleaning_preview_run_and_export_preserve_other_fields(app, admin_client):
    assert admin_client.get("/admin/cleaning").status_code == 200
    with app.app_context():
        clean = FacebookRecord(
            facebook_record_id="clean-preview", text="La 12 😍 #diak",
            cleaned_text="old cleaned text", is_clean=True, is_duplicate=False,
            label="Positive", sentiment="Negative", sentiment_score=-1.0,
        )
        emoji_only = FacebookRecord(
            facebook_record_id="emoji-only-preview", text="❤️",
            cleaned_text="old emoji", is_clean=True, is_duplicate=False,
        )
        missing = FacebookRecord(
            facebook_record_id="missing-preview", text=None,
            cleaned_text=None, is_clean=False, is_duplicate=False,
        )
        duplicate = FacebookRecord(
            facebook_record_id="duplicate-preview", text="dupe 😍",
            cleaned_text="old duplicate", is_clean=True, is_duplicate=True,
        )
        db.session.add_all([clean, emoji_only, missing, duplicate])
        db.session.commit()
        ids = {"clean": clean.id, "emoji": emoji_only.id, "missing": missing.id, "duplicate": duplicate.id}
        clean_updated_at = clean.updated_at

    preview_response = admin_client.post("/api/admin/clean/preview", json={})
    assert preview_response.status_code == 200
    preview = preview_response.get_json()["data"]
    assert preview["stats"]["clean_records"] == 2
    assert preview["stats"]["cleaned_text_nonempty"] == 1
    assert preview["stats"]["cleaned_text_empty"] == 1
    assert preview["stats"]["total_records"] == 4
    assert preview["stats"]["duplicate_records"] == 1
    assert preview["stats"]["missing_text_records"] == 1
    assert {row["id"] for row in preview["records"]} == {ids["clean"], ids["emoji"]}

    with app.app_context():
        clean_before = db.session.get(FacebookRecord, ids["clean"])
        assert clean_before.cleaned_text == "old cleaned text"
        assert clean_before.text == "La 12 😍 #diak"

    run_response = admin_client.post("/api/admin/clean", json={})
    assert run_response.status_code == 200
    run = run_response.get_json()["data"]
    assert run["updated"] == 2
    assert {row["id"] for row in run["records"]} == {ids["clean"], ids["emoji"]}

    with app.app_context():
        clean_after = db.session.get(FacebookRecord, ids["clean"])
        emoji_after = db.session.get(FacebookRecord, ids["emoji"])
        missing_after = db.session.get(FacebookRecord, ids["missing"])
        duplicate_after = db.session.get(FacebookRecord, ids["duplicate"])
        assert clean_after.cleaned_text == "La 12 diak"
        assert clean_after.text == "La 12 😍 #diak"
        assert clean_after.label == "Positive"
        assert clean_after.sentiment == "Negative"
        assert clean_after.sentiment_score == -1.0
        assert clean_after.updated_at == clean_updated_at
        assert clean_after.is_clean is True and clean_after.is_duplicate is False
        assert emoji_after.cleaned_text == ""
        assert emoji_after.is_clean is True
        assert missing_after.is_clean is False
        assert duplicate_after.cleaned_text == "old duplicate"
        assert duplicate_after.is_duplicate is True

    export_response = admin_client.get("/api/admin/clean/export.csv")
    assert export_response.status_code == 200
    assert export_response.mimetype == "text/csv"
    rows = list(csv.DictReader(io.StringIO(export_response.get_data(as_text=True))))
    exported = next(row for row in rows if row["id"] == str(ids["clean"]))
    assert exported["text"] == "La 12 😍 #diak"
    assert exported["cleaned_text"] == "La 12 diak"


def test_label_assignment_uses_correct_id_and_confirms_empty_cleaned_text(app, admin_client):
    page = admin_client.get("/labeling")
    assert page.status_code == 200
    page_source = page.get_data(as_text=True)
    assert "row.cleaned_text" in page_source
    assert "row.text" in page_source
    with app.app_context():
        target = FacebookRecord(
            facebook_record_id="label-target", text="Original ❤️",
            cleaned_text="Original", label=None, is_clean=True, is_duplicate=False,
        )
        empty = FacebookRecord(
            facebook_record_id="label-empty", text="❤️",
            cleaned_text="", label=None, is_clean=True, is_duplicate=False,
        )
        db.session.add_all([target, empty])
        db.session.commit()
        target_id, empty_id = target.id, empty.id

    assigned = admin_client.post("/api/admin/labeling/assign", json={
        "record_id": target_id, "label": "Positive"
    })
    assert assigned.status_code == 200
    result = assigned.get_json()["data"]
    assert result["id"] == target_id
    assert result["label"] == "Positive"
    assert result["text"] == "Original ❤️"
    assert result["cleaned_text"] == "Original"
    listed = admin_client.get("/api/data?search=Original").get_json()["data"]
    assert listed[0]["id"] == target_id
    assert listed[0]["label"] == "Positive"

    rejected = admin_client.post("/api/admin/labeling/assign", json={
        "record_id": empty_id, "label": "Neutral"
    })
    assert rejected.status_code == 409
    assert rejected.get_json()["success"] is False

    confirmed = admin_client.post("/api/admin/labeling/assign", json={
        "record_id": empty_id, "label": "Neutral", "confirm_empty_text": True
    })
    assert confirmed.status_code == 200
    empty_result = confirmed.get_json()["data"]
    assert empty_result["id"] == empty_id
    assert empty_result["label"] == "Neutral"
    assert empty_result["text"] == "❤️"
    assert empty_result["cleaned_text"] == ""

    invalid_label = admin_client.post("/api/admin/labeling/assign", json={
        "record_id": target_id, "label": "Unknown"
    })
    assert invalid_label.status_code == 400

def test_wordlist_admin_only(user_client):
    r = user_client.get("/api/admin/wordlist")
    assert r.status_code == 403

def test_wordlist_admin_ok(admin_client):
    r = admin_client.get("/api/admin/wordlist")
    assert r.status_code == 200
    assert isinstance(r.get_json()["data"], list)

def test_db_info_admin(admin_client):
    r = admin_client.get("/api/admin/database/info")
    assert r.status_code == 200
    assert "users" in r.get_json()["data"]

def test_search(user_client):
    r = user_client.get("/api/search?q=test")
    assert r.status_code == 200
