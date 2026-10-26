from backend import db
from backend.models.facebook_record import FacebookRecord
from backend.services.ml_service import _prepare_examples, _split_examples, train_model


def test_train_with_insufficient_data(admin_client):
    r = admin_client.post("/api/admin/ml/train", json={})
    assert r.status_code == 200
    assert r.get_json()["success"] is False

def test_train_and_evaluate(admin_client):
    page = admin_client.get("/ml")
    assert page.status_code == 200
    assert b"class-distribution" in page.data
    assert b"classification-report" in page.data

    texts = [
        ("good diak", "Positive"),
        ("love nice", "Positive"),
        ("happy beautiful", "Positive"),
        ("excellent amazing", "Positive"),
        ("joy lovely", "Positive"),
        ("great wonderful", "Positive"),
        ("sweet cheerful", "Positive"),
        ("perfect adore", "Positive"),
        ("fantastic kind", "Positive"),
        ("sunshine delight", "Positive"),
        ("bad aat", "Negative"),
        ("hate ugly", "Negative"),
        ("poor awful", "Negative"),
        ("sad terrible", "Negative"),
        ("angry hurt", "Negative"),
        ("horrible painful", "Negative"),
        ("worst upset", "Negative"),
        ("dislike gloomy", "Negative"),
        ("bitter fear", "Negative"),
        ("disappointed grief", "Negative"),
        ("plain text", "Neutral"),
        ("nothing here", "Neutral"),
        ("average normal", "Neutral"),
        ("okay usual", "Neutral"),
        ("just simple", "Neutral"),
        ("ordinary update", "Neutral"),
        ("statement only", "Neutral"),
        ("basic information", "Neutral"),
        ("regular note", "Neutral"),
        ("routine details", "Neutral"),
    ]
    for txt, lab in texts:
        source_text = f"good {txt}" if lab == "Positive" else f"bad {txt}" if lab == "Negative" else txt
        r = admin_client.post("/api/data", json={
            "text": source_text, "author_name": "Test", "sentiment": lab
        })
        rid = r.get_json()["data"]["id"]
        admin_client.post("/api/admin/labeling/assign", json={
            "record_id": rid, "label": lab
        })
    res = admin_client.post("/api/admin/ml/train", json={"max_depth": 5})
    j = res.get_json()
    assert j["success"] is True
    assert 0 <= j["history"]["accuracy"] <= 1
    history = j["history"]
    config = history["configuration"]
    assert config["stratified"] is True
    assert config["evaluation_valid"] is True
    assert config["raw_class_distribution"] == {"Positive": 10, "Negative": 10, "Neutral": 10}
    assert sum(config["train_class_distribution"].values()) == history["training_records"]
    assert sum(config["test_class_distribution"].values()) == history["testing_records"]
    assert config["manual_label_count"] == 30
    assert set(config["class_metrics"]) == {"Positive", "Negative", "Neutral"}
    assert all(config["class_metrics"][label]["support"] >= 2 for label in config["class_metrics"])
    assert all(label in history["classification_report"] for label in ("Positive", "Negative", "Neutral"))
    assert sum(map(sum, history["confusion_matrix"]["matrix"])) == history["testing_records"]

    ev = admin_client.get("/api/admin/ml/evaluation")
    assert ev.status_code == 200


def test_unique_text_groups_do_not_leak_and_conflicting_labels_are_aggregated():
    records = [
        ("same text", "same text", "Positive"),
        ("same text", "same text", "Positive"),
        ("same text", "same text", "Negative"),
        ("another text", "another text", "Neutral"),
    ]
    texts, labels, raw_counts, duplicate_groups, conflicts = _prepare_examples(records)
    assert texts == ["same text", "another text"]
    assert labels == ["Positive", "Neutral"]
    assert raw_counts == {"Positive": 2, "Negative": 1, "Neutral": 1}
    assert duplicate_groups == 1
    assert conflicts == 1


def test_split_stratifies_when_possible_and_keeps_singleton_class_in_training():
    balanced = [label for label in ("Positive", "Negative", "Neutral") for _ in range(10)]
    train, test, stratified, strategy = _split_examples(balanced, 0.2, 42)
    assert stratified is True
    assert strategy == "stratified"
    assert not (set(train) & set(test))

    imbalanced = ["Negative"] + ["Positive"] * 20 + ["Neutral"] * 20
    train, test, stratified, strategy = _split_examples(imbalanced, 0.2, 42)
    assert strategy == "stratified_remaining"
    assert train.count(0) == 1
    assert 0 not in test
    assert not (set(train) & set(test))


def test_singleton_class_produces_explicitly_incomplete_evaluation(app):
    with app.app_context():
        records = [
            FacebookRecord(facebook_record_id="singleton-negative", text="unique negative",
                           cleaned_text="unique negative", sentiment="Negative",
                           is_clean=True, is_duplicate=False)
        ]
        for i in range(10):
            records.append(FacebookRecord(
                facebook_record_id=f"singleton-positive-{i}", text=f"positive sample {i}",
                cleaned_text=f"positive sample {i}", sentiment="Positive",
                is_clean=True, is_duplicate=False,
            ))
            records.append(FacebookRecord(
                facebook_record_id=f"singleton-neutral-{i}", text=f"neutral sample {i}",
                cleaned_text=f"neutral sample {i}", sentiment="Neutral",
                is_clean=True, is_duplicate=False,
            ))
        db.session.add_all(records)
        db.session.commit()

        result = train_model(persist=False)
        assert result["success"] is True
        history = result["history"]
        config = history["configuration"]
        assert config["evaluation_valid"] is False
        assert config["classes_with_insufficient_samples"] == ["Negative"]
        assert config["classes_without_test_examples"] == ["Negative"]
        assert config["class_metrics"]["Negative"]["support"] == 0
        assert "not necessarily human-verified" in config["warnings"][0]
