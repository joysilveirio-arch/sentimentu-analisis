from backend.services.cleaning_service import clean_text, detect_language, normalize_gender

def test_clean_text_basic():
    assert clean_text("hello world") == "hello world"

def test_clean_text_url():
    assert "http" not in clean_text("check https://example.com now")

def test_clean_text_html():
    assert "<" not in clean_text("<b>bold</b> text")

def test_clean_text_whitespace():
    assert clean_text("a  b   c") == "a b c"

def test_clean_text_empty():
    assert clean_text("") == ""
    assert clean_text(None) == ""

def test_detect_language_english():
    assert detect_language("the good and beautiful") in ("eng", "unknown")

def test_detect_language_tetum():
    assert detect_language("hau nia diak ba ita") in ("tet", "unknown")

def test_normalize_gender():
    assert normalize_gender("male") == "MALE"
    assert normalize_gender("F") == "FEMALE"
    assert normalize_gender("") == "UNKNOWN"
    assert normalize_gender("neuter") == "NEUTER"