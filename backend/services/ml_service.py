import os
import json
import joblib
import numpy as np
from flask import current_app, has_app_context
from collections import Counter, defaultdict
from sqlalchemy.exc import OperationalError
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report,
)
from backend import db
from backend.models.facebook_record import FacebookRecord
from backend.models.model_training_history import ModelTrainingHistory
from backend.services.cleaning_service import clean_text
from config import Config

MODEL_FILENAME = "decision_tree_model.joblib"
VECTORIZER_FILENAME = "tfidf_vectorizer.joblib"
CLASS_LABELS = ("Positive", "Negative", "Neutral")
MIN_TEST_SUPPORT = 2

def _model_path(filename):
    folder = current_app.config.get("MODEL_FOLDER", Config.MODEL_FOLDER) if has_app_context() else Config.MODEL_FOLDER
    return os.path.join(folder, filename)


def _distribution(labels):
    counts = Counter(labels)
    return {label: int(counts.get(label, 0)) for label in CLASS_LABELS}


def _prepare_examples(records):
    """Collapse identical normalized text into one majority-label example."""
    grouped = defaultdict(Counter)
    raw_counts = Counter()
    for cleaned_text, raw_text, sentiment in records:
        label = (sentiment or "").strip().title()
        if label not in CLASS_LABELS:
            continue
        raw_counts[label] += 1
        text = clean_text(cleaned_text or raw_text or "").casefold()
        if text:
            grouped[text][label] += 1

    texts, labels = [], []
    conflicting_duplicate_groups = 0
    for text, label_counts in grouped.items():
        if len(label_counts) > 1:
            conflicting_duplicate_groups += 1
        texts.append(text)
        labels.append(label_counts.most_common(1)[0][0])
    duplicate_text_groups = sum(1 for label_counts in grouped.values() if sum(label_counts.values()) > 1)
    return texts, labels, _distribution(raw_counts.elements()), duplicate_text_groups, conflicting_duplicate_groups


def _split_examples(labels, test_size, random_state):
    """Split unique-text indices, stratifying whenever class counts allow it."""
    counts = Counter(labels)
    indices = np.arange(len(labels))
    requested_test_count = int(np.ceil(len(indices) * test_size))
    class_count = len(counts)
    can_stratify_all = (
        min(counts.values()) >= 2
        and requested_test_count >= class_count
        and len(indices) - requested_test_count >= class_count
    )
    if can_stratify_all:
        train_indices, test_indices = train_test_split(
            indices, test_size=test_size, random_state=random_state, stratify=labels
        )
        return list(train_indices), list(test_indices), True, "stratified"

    # A class with one example cannot appear in both partitions. Keep such
    # examples in training and stratify the remaining classes if possible.
    singleton_indices = [i for i, label in enumerate(labels) if counts[label] == 1]
    singleton_set = set(singleton_indices)
    remaining_indices = [i for i in indices if i not in singleton_set]
    if len(remaining_indices) < 2:
        raise ValueError("Not enough unique texts remain for an independent test set.")
    test_count = min(requested_test_count, len(remaining_indices) - 1)
    remaining_labels = [labels[i] for i in remaining_indices]
    remaining_counts = Counter(remaining_labels)
    remaining_classes = len(remaining_counts)
    stratify_remaining = (
        remaining_classes > 1
        and min(remaining_counts.values()) >= 2
        and test_count >= remaining_classes
        and len(remaining_indices) - test_count >= remaining_classes
    )
    remaining_train, test_indices = train_test_split(
        remaining_indices,
        test_size=test_count,
        random_state=random_state,
        stratify=remaining_labels if stratify_remaining else None,
    )
    train_indices = singleton_indices + list(remaining_train)

    # If an unstratified fallback omitted a class from training, move one of
    # its held-out examples into training. Unique text remains in only one set.
    for label in counts:
        if not any(labels[i] == label for i in train_indices):
            candidate = next((i for i in test_indices if labels[i] == label), None)
            if candidate is not None:
                test_indices.remove(candidate)
                train_indices.append(candidate)
    return train_indices, list(test_indices), stratify_remaining, (
        "stratified_remaining" if stratify_remaining else "unstratified_fallback"
    )

def train_model(max_depth=15, test_size=0.2, max_features=5000, min_df=1, max_df=0.95, persist=True, save_artifacts=None):
    if save_artifacts is None:
        save_artifacts = persist
    records = db.session.query(
        FacebookRecord.cleaned_text,
        FacebookRecord.text,
        FacebookRecord.sentiment,
    ).filter(
        FacebookRecord.sentiment.isnot(None),
        FacebookRecord.is_duplicate.isnot(True),
    ).order_by(FacebookRecord.id).all()
    manual_label_count = FacebookRecord.query.filter(FacebookRecord.label.isnot(None)).count()
    # Release SQLite's read transaction before feature extraction/model fitting.
    db.session.rollback()

    if len(records) < 10:
        return {"success": False, "message": "Need at least 10 non-duplicate records with automatic sentiment results. Run sentiment analysis first."}

    texts, labels, raw_distribution, duplicate_text_groups, conflicting_duplicate_groups = _prepare_examples(records)
    if len(texts) < 10:
        return {"success": False, "message": f"Only {len(texts)} unique texts with automatic sentiment are available; need at least 10."}
    if len(set(labels)) < 2:
        return {"success": False, "message": "Need automatic sentiment results in at least 2 classes."}

    try:
        test_size = float(test_size)
        if not 0 < test_size < 1:
            return {"success": False, "message": "Test size must be greater than 0 and less than 1 (for example, 0.2)."}
    except (TypeError, ValueError):
        return {"success": False, "message": "Test size must be a decimal between 0 and 1 (for example, 0.2)."}

    try:
        train_indices, test_indices, stratified, split_strategy = _split_examples(
            labels, test_size, Config.ML_RANDOM_STATE
        )
    except ValueError as exc:
        return {"success": False, "message": f"Cannot create an independent train/test split: {exc}"}
    if not test_indices:
        return {"success": False, "message": "Not enough unique texts remain for a test set. Increase the dataset or reduce Test Size."}

    X_train_txt = [texts[index] for index in train_indices]
    X_test_txt = [texts[index] for index in test_indices]
    y_train = [labels[index] for index in train_indices]
    y_test = [labels[index] for index in test_indices]
    train_distribution = _distribution(y_train)
    test_distribution = _distribution(y_test)
    unique_distribution = _distribution(labels)
    classes_with_insufficient_samples = [
        label for label in CLASS_LABELS if unique_distribution[label] < 2
    ]
    classes_without_test_examples = [
        label for label in CLASS_LABELS if test_distribution[label] == 0
    ]
    classes_with_low_test_support = [
        label for label in CLASS_LABELS if 0 < test_distribution[label] < MIN_TEST_SUPPORT
    ]
    evaluation_valid = not (
        classes_with_insufficient_samples
        or classes_without_test_examples
        or classes_with_low_test_support
        or any(unique_distribution[label] == 0 for label in CLASS_LABELS)
    )

    warnings = []
    warnings.append(
        "This evaluation compares model predictions with wordlist-generated sentiment labels, not necessarily human-verified sentiment."
    )
    if classes_with_insufficient_samples:
        warnings.append(
            "Too few unique examples to evaluate these classes reliably: "
            + ", ".join(classes_with_insufficient_samples)
            + ". A class with fewer than 2 examples cannot appear independently in train and test."
        )
    if classes_without_test_examples:
        warnings.append("No held-out test examples for: " + ", ".join(classes_without_test_examples) + ".")
    if classes_with_low_test_support:
        warnings.append(
            f"Test support is below {MIN_TEST_SUPPORT} for: "
            + ", ".join(classes_with_low_test_support) + "."
        )
    if not manual_label_count:
        warnings.append("No independent human-verified labels are available in the database.")
    if conflicting_duplicate_groups:
        warnings.append(
            f"{conflicting_duplicate_groups} identical-text groups had conflicting automatic labels; each group uses its majority label."
        )

    vectorizer = TfidfVectorizer(
        max_features=max_features, min_df=min_df, max_df=max_df,
        ngram_range=(1, 2),
    )
    X_train = vectorizer.fit_transform(X_train_txt)
    X_test = vectorizer.transform(X_test_txt)

    clf = DecisionTreeClassifier(max_depth=max_depth, random_state=Config.ML_RANDOM_STATE)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    accuracy = float(accuracy_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
    recall = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
    f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    cm = confusion_matrix(y_test, y_pred, labels=list(CLASS_LABELS)).tolist()
    report = classification_report(
        y_test, y_pred, labels=list(CLASS_LABELS), target_names=list(CLASS_LABELS), zero_division=0
    )
    report_data = classification_report(
        y_test, y_pred, labels=list(CLASS_LABELS), target_names=list(CLASS_LABELS),
        zero_division=0, output_dict=True,
    )
    class_metrics = {
        label: {
            "precision": float(report_data[label]["precision"]),
            "recall": float(report_data[label]["recall"]),
            "f1_score": float(report_data[label]["f1-score"]),
            "support": int(report_data[label]["support"]),
        }
        for label in CLASS_LABELS
    }

    history_data = {
        "model_name": "decision_tree",
        "algorithm": "DecisionTreeClassifier",
        "training_records": len(X_train_txt),
        "testing_records": len(X_test_txt),
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "configuration": {
            "max_depth": max_depth, "test_size": test_size,
            "max_features": max_features, "min_df": min_df, "max_df": max_df,
            "classes": list(CLASS_LABELS), "label_source": "automatic_sentiment",
        "manual_label_count": int(manual_label_count),
            "unique_texts": len(texts),
            "duplicate_text_groups": duplicate_text_groups,
            "conflicting_duplicate_groups": conflicting_duplicate_groups,
            "raw_class_distribution": raw_distribution,
            "unique_class_distribution": unique_distribution,
            "train_class_distribution": train_distribution,
            "test_class_distribution": test_distribution,
            "stratified": stratified,
            "split_strategy": split_strategy,
            "evaluation_valid": evaluation_valid,
            "minimum_test_support": MIN_TEST_SUPPORT,
            "classes_with_insufficient_samples": classes_with_insufficient_samples,
            "classes_without_test_examples": classes_without_test_examples,
            "classes_with_low_test_support": classes_with_low_test_support,
            "warnings": warnings,
            "class_metrics": class_metrics,
        },
        "confusion_matrix": {"labels": list(CLASS_LABELS), "matrix": cm},
        "classification_report": report,
        "model_path": _model_path(MODEL_FILENAME),
    }

    if save_artifacts:
        joblib.dump(clf, _model_path(MODEL_FILENAME))
        joblib.dump(vectorizer, _model_path(VECTORIZER_FILENAME))

    if not persist:
        return {"success": True, "history": history_data}
    hist = ModelTrainingHistory(
        model_name=history_data["model_name"],
        algorithm=history_data["algorithm"],
        training_records=history_data["training_records"],
        testing_records=history_data["testing_records"],
        accuracy=accuracy, precision=precision, recall=recall, f1_score=f1,
        configuration=json.dumps(history_data["configuration"]),
        confusion_matrix=json.dumps(history_data["confusion_matrix"]),
        classification_report=report,
        model_path=history_data["model_path"],
    )
    db.session.add(hist)
    try:
        db.session.commit()
    except OperationalError as exc:
        db.session.rollback()
        if "locked" in str(exc).lower() or "busy" in str(exc).lower():
            return {"success": False, "message": "Training finished, but SQLite is busy and could not save the training history. Close database viewers or wait for active writes, then retry."}
        raise
    return {"success": True, "history": hist.to_dict()}

def load_model():
    latest = ModelTrainingHistory.query.order_by(ModelTrainingHistory.created_at.desc()).first()
    if latest is None:
        return None, None
    try:
        training_config = json.loads(latest.configuration or "{}")
    except (TypeError, ValueError):
        return None, None
    # Do not serve an artifact trained with the old/manual label source after
    # the application has switched to automatic sentiment labels.
    if training_config.get("label_source") != "automatic_sentiment":
        return None, None
    if not os.path.exists(_model_path(MODEL_FILENAME)):
        return None, None
    clf = joblib.load(_model_path(MODEL_FILENAME))
    vec = joblib.load(_model_path(VECTORIZER_FILENAME))
    return clf, vec

def predict_text(text):
    clf, vec = load_model()
    if clf is None:
        return {"success": False, "message": "Model not trained yet."}
    cleaned = clean_text(text) or " "
    X = vec.transform([cleaned])
    pred = clf.predict(X)[0]
    try:
        proba = clf.predict_proba(X)[0]
        confidence = float(np.max(proba))
    except Exception:
        confidence = None
    return {"success": True, "predicted_label": str(pred),
            "confidence": confidence, "cleaned_text": cleaned}
