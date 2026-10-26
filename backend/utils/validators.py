ALLOWED_EXTENSIONS = {"csv"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_int(value, default=0):
    try:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default

def safe_float(value, default=0.0):
    try:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return default
        return float(str(value).strip())
    except Exception:
        return default