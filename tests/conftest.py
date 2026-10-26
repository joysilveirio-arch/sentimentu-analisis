import sys, os, tempfile, pytest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from backend import create_app, db
from backend.models.user import User
from backend.models.sentiment_word import SentimentWord
from backend.models.label import Label

@pytest.fixture
def app():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    class TestConfig:
        TESTING = True
        SECRET_KEY = "test"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{path}"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        WTF_CSRF_ENABLED = False
        UPLOAD_FOLDER = tempfile.gettempdir()
        MODEL_FOLDER = tempfile.gettempdir()
        LOG_FOLDER = tempfile.gettempdir()
        ADMIN_USERNAME = "admin"
        ADMIN_EMAIL = "admin@test.local"
        ADMIN_PASSWORD = "admin123"

    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        admin = User(username="admin", email="admin@test.local", role="ADMIN")
        admin.set_password("admin123")
        user = User(username="user", email="user@test.local", role="USER")
        user.set_password("user123")
        db.session.add_all([admin, user])

        for w, s, sc, lang in [
            ("good", "Positive", 1, "eng"),
            ("bad", "Negative", 1, "eng"),
            ("diak", "Positive", 1, "tet"),
            ("aat", "Negative", 1, "tet"),
        ]:
            db.session.add(SentimentWord(word=w, sentiment=s, score=sc, language=lang))

        for name in ["Positive", "Neutral", "Negative"]:
            db.session.add(Label(name=name))

        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()
    try:
        os.remove(path)
    except OSError:
        pass

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_client(client):
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    return client

@pytest.fixture
def user_client(client):
    client.post("/api/auth/login", json={"username": "user", "password": "user123"})
    return client