import csv
import io
import os
from datetime import datetime, timezone

from backend import db
from backend.models.facebook_record import FacebookRecord
from backend.models.import_history import ImportHistory
from backend.models.sentiment_result import SentimentResult
from backend.services.cleaning_service import (
    clean_text, detect_language, normalize_gender,
)
from backend.services.sentiment_service import analyze_text, load_wordlist
from backend.utils.validators import safe_int


# Keep the source column names explicit: Facebook exports use slash-delimited
# names, while FacebookRecord uses SQLAlchemy-friendly names.
COLUMN_MAP = {
    "id": "facebook_record_id",
    "commentId": "comment_id",
    "author/name": "author_name",
    "author/id": "author_facebook_id",
    "author/url": "author_url",
    "author/gender": "gender",
    "postTitle": "post_title",
    "text": "text",
    "date": "date",
    "likesCount": "likes_count",
    "commentsCount": "comments_count",
    "facebookUrl": "facebook_url",
    "profileName": "profile_name",
    "attachments/0/__typename": "attachment_type",
    "parentComment/id": "parent_comment_id",
}


def _value(row, key):
    value = row.get(key)
    if value is None:
        return None
    value = str(value).strip()
    return value if value and value.casefold() not in {"null", "none", "nan"} else None


def parse_date(value):
    value = _value({"value": value}, "value")
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        # SQLite stores naive datetimes; normalize timestamps to UTC first.
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc)
            parsed = parsed.replace(tzinfo=None)
        return parsed
    except (TypeError, ValueError, OverflowError):
        return None


def _read_csv(path):
    """Read standards-compliant CSV, preserving quoted multiline text.

    UTF-8-SIG accepts both UTF-8 and UTF-8-SIG files. Strict parsing makes
    unrecoverable quoting errors explicit instead of silently shifting columns.
    """
    with open(path, "r", encoding="utf-8-sig", newline="") as source:
        content = source.read()

    reader = csv.reader(io.StringIO(content, newline=""), strict=True)
    try:
        headers = [header.strip() for header in next(reader)]
    except StopIteration:
        return [], []
    except csv.Error:
        headers = []

    # Some Facebook exports add an extra quote around each complete CSV
    # record, while leaving newlines inside text untouched. Unwrap those
    # records and parse each one independently so text newlines stay in text.
    if len(headers) == 1 and "," in headers[0]:
        physical_lines = content.splitlines()
        header_line = physical_lines[0].strip()
        if len(header_line) < 2 or header_line[0] != '"' or header_line[-1] != '"':
            raise csv.Error("Malformed Facebook CSV header")
        header_payload = header_line[1:-1].replace('""', '"')
        headers = next(csv.reader([header_payload], strict=True))
        headers = [header.strip() for header in headers]
        expected = len(headers)
        post_title_index = headers.index("postTitle") if "postTitle" in headers else -1
        rows, errors, buffer = [], [], []

        def decode_record(lines):
            payload = "\n".join(lines).strip()
            if len(payload) < 2 or payload[0] != '"' or payload[-1] != '"':
                return None
            payload = payload[1:-1].replace('""', '"')
            try:
                decoded = list(csv.reader(io.StringIO(payload, newline=""), strict=False))
            except csv.Error:
                return None
            if len(decoded) == 1 and len(decoded[0]) == expected:
                return dict(zip(headers, decoded[0]))

            # In the damaged export, raw newlines in `text` split one logical
            # row into several CSV rows. Reassemble the known trailing profile
            # fields around the text column, preserving all text fragments.
            flat = [value for fragment in decoded for value in fragment]
            if post_title_index < 0 or len(flat) <= post_title_index:
                return None
            prefix = flat[:post_title_index + 1]
            remainder = flat[post_title_index + 1:]

            def is_media_url(value):
                return isinstance(value, str) and value.startswith((
                    "https://scontent-", "https://platform-lookaside.fbsbx.com/"
                ))

            def is_facebook_profile_url(value):
                return isinstance(value, str) and value.startswith("https://www.facebook.com/")

            profile_pos = next((
                i for i in range(2, len(remainder) - 1)
                if is_media_url(remainder[i]) and is_facebook_profile_url(remainder[i + 1])
            ), None)
            if profile_pos is None:
                return None

            # `profileId`, `profileName`, `profilePicture`, `profileUrl`, and
            # `replyToCommentId` have recognizable positions in this export.
            profile_id, profile_name = remainder[profile_pos - 2:profile_pos]
            picture_url, profile_url = remainder[profile_pos:profile_pos + 2]
            reply_to = remainder[profile_pos + 2] if len(remainder) > profile_pos + 2 else ""
            trailing = remainder[profile_pos + 3:]
            if not trailing:
                return None
            depth = trailing[-1]
            text_parts = remainder[:profile_pos - 2] + trailing[:-1]
            repaired = dict(zip(headers[:post_title_index + 1], prefix))
            repaired.update({
                "profileId": profile_id,
                "profileName": profile_name,
                "profilePicture": picture_url,
                "profileUrl": profile_url,
                "replyToCommentId": reply_to,
                "text": "\n".join(part for part in text_parts if part is not None),
                "threadingDepth": depth,
            })
            return repaired

        def likely_record_start(line):
            # Empty attachment cells are the common case. A nonempty first
            # cell can also be an attachment type. Text lines often begin
            # with a quote or hashtag, so only known attachment values count
            # as a new row boundary.
            return (
                line.startswith('\",,')
                or line.startswith('\",\"\"')
                or line.startswith('\"\"\"')
                or line.startswith(('"Sticker,', '"GenericAttachmentMedia,'))
            )

        for line_number, line in enumerate(physical_lines[1:], start=2):
            if not line and not buffer:
                continue
            if buffer and likely_record_start(line):
                recovered = decode_record(buffer)
                if recovered is not None:
                    rows.append(recovered)
                else:
                    errors.append(f"CSV line {line_number}: previous wrapped record could not be recovered")
                buffer = []
            buffer.append(line)
            record = decode_record(buffer)
            if record is not None:
                rows.append(record)
                buffer = []
        if buffer:
            errors.append(f"CSV line {len(physical_lines)}: wrapped record could not be recovered")
        return rows, errors

    rows = []
    row_errors = []
    expected = len(headers)
    for row in reader:
        if not row:
            continue
        if len(row) != expected:
            row_errors.append(
                f"CSV line {reader.line_num}: expected {expected} columns, found {len(row)}"
            )
            continue
        rows.append(dict(zip(headers, row)))
    return rows, row_errors


def import_csv(path, user_id=None):
    """Clean and transactionally import Facebook CSV records."""
    filename = os.path.basename(os.fspath(path))
    history = ImportHistory(filename=filename, status="processing", user_id=user_id)
    db.session.add(history)
    db.session.commit()

    try:
        rows, parse_errors = _read_csv(path)
    except (OSError, UnicodeError, csv.Error) as exc:
        history.status = "failed"
        history.message = f"CSV parse error: {exc}"
        history.total_rows = 0
        history.failed_rows = 1
        db.session.commit()
        return history

    source_rows = len(rows) + len(parse_errors)
    imported = duplicate = cleaned = 0
    error_rows = len(parse_errors)
    error_messages = parse_errors[:5]

    # Commit the dataset and its final history together. A database error
    # rolls back every record from this import.
    try:
        existing_ids = {
            value for (value,) in db.session.query(FacebookRecord.facebook_record_id)
            .filter(FacebookRecord.facebook_record_id.isnot(None)).all()
        }
        existing_text_rows = db.session.query(
            FacebookRecord.text, FacebookRecord.cleaned_text
        ).all()
        seen_texts = {
            clean_text(cleaned_text or raw_text).casefold()
            for raw_text, cleaned_text in existing_text_rows
            if clean_text(cleaned_text or raw_text)
        }
        seen_ids = set(existing_ids)
        sentiment_lexicon = load_wordlist()
        sentiment_results = []
        for row_number, row in enumerate(rows, start=2):
            # In this Facebook comments export, `facebookId` identifies the
            # parent post and is shared by many comments. The source `id` is
            # the unique record key; fall back to facebookId only when no
            # record id is supplied.
            record_id = _value(row, "id") or _value(row, "facebookId")
            if not record_id:
                error_rows += 1
                if len(error_messages) < 5:
                    error_messages.append(f"CSV row {row_number}: missing facebookId/id")
                continue
            if record_id in seen_ids:
                duplicate += 1
                cleaned += 1
                continue

            raw_text = _value(row, "text")
            normalized_text = raw_text
            cleaned_text = clean_text(raw_text) if raw_text is not None else ""
            text_key = cleaned_text.casefold() if cleaned_text else None
            duplicate_text = bool(text_key and text_key in seen_texts)
            if text_key and not duplicate_text:
                seen_texts.add(text_key)
            sentiment = analyze_text(cleaned_text, sentiment_lexicon)
            author = _value(row, "author/name")
            record = FacebookRecord(
                facebook_record_id=record_id,
                comment_id=_value(row, "commentId"),
                author_name=author,
                author_facebook_id=_value(row, "author/id"),
                author_url=_value(row, "author/url"),
                gender=normalize_gender(_value(row, "author/gender")),
                post_title=_value(row, "postTitle"),
                text=normalized_text,
                cleaned_text=cleaned_text or None,
                date=parse_date(_value(row, "date")),
                likes_count=safe_int(_value(row, "likesCount")),
                comments_count=safe_int(_value(row, "commentsCount")),
                facebook_url=_value(row, "facebookUrl"),
                profile_name=_value(row, "profileName"),
                attachment_type=_value(row, "attachments/0/__typename"),
                parent_comment_id=_value(row, "parentComment/id"),
                language=detect_language(cleaned_text),
                sentiment=sentiment["sentiment"],
                sentiment_score=sentiment["score"],
                positive_words=sentiment["positive"],
                negative_words=sentiment["negative"],
                is_clean=bool(cleaned_text),
                is_duplicate=duplicate_text,
            )
            db.session.add(record)
            sentiment_results.append((record, sentiment))
            seen_ids.add(record_id)
            imported += 1
            cleaned += 1
            if duplicate_text:
                duplicate += 1

        db.session.flush()
        for record, result in sentiment_results:
            db.session.add(SentimentResult(
                record_id=record.id,
                sentiment=result["sentiment"],
                sentiment_score=result["score"],
                positive_words=result["positive"],
                negative_words=result["negative"],
                method="wordlist",
            ))

        history.total_rows = source_rows
        history.imported_rows = imported
        history.failed_rows = error_rows
        history.duplicate_rows = duplicate
        history.status = "success" if not error_rows else "partial"
        history.message = "; ".join(error_messages) if error_messages else (
            f"Imported {imported}; cleaned {cleaned}; duplicates {duplicate}; errors 0"
        )
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        history = db.session.get(ImportHistory, history.id)
        history.total_rows = source_rows
        history.imported_rows = 0
        history.failed_rows = source_rows or 1
        history.duplicate_rows = 0
        history.status = "failed"
        history.message = f"Database import failed; transaction rolled back: {exc}"
        db.session.commit()
    return history
