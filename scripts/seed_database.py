import sys
import os

# ============================================================
# Add project root to Python path
# ============================================================
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# Imports
# ============================================================
from backend import create_app, db
from backend.models.user import User
from backend.models.sentiment_word import SentimentWord
from backend.models.label import Label
from config import Config


# ============================================================
# Create Flask application
# ============================================================
app = create_app()


# ============================================================
# Default Sentiment Wordlist
# ============================================================
WORDLIST = [
    # --------------------------------------------------------
    # Tetum
    # --------------------------------------------------------
    ("diak", "Positive", 1, "tet"),
    ("furak", "Positive", 1, "tet"),
    ("gosta", "Positive", 1, "tet"),
    ("bonita", "Positive", 1, "tet"),

    ("aat", "Negative", 1, "tet"),
    ("triste", "Negative", 1, "tet"),
    ("odi", "Negative", 1, "tet"),
    ("problema", "Negative", 1, "tet"),

    # --------------------------------------------------------
    # Indonesian
    # --------------------------------------------------------
    ("bagus", "Positive", 1, "ind"),
    ("cantik", "Positive", 1, "ind"),
    ("suka", "Positive", 1, "ind"),
    ("indah", "Positive", 1, "ind"),

    ("jelek", "Negative", 1, "ind"),
    ("sedih", "Negative", 1, "ind"),

    # --------------------------------------------------------
    # English
    # --------------------------------------------------------
    ("good", "Positive", 1, "eng"),
    ("beautiful", "Positive", 1, "eng"),
    ("love", "Positive", 1, "eng"),
    ("amazing", "Positive", 1, "eng"),
    ("nice", "Positive", 1, "eng"),

    ("bad", "Negative", 1, "eng"),
    ("sad", "Negative", 1, "eng"),
    ("ugly", "Negative", 1, "eng"),
    ("hate", "Negative", 1, "eng"),

    # --------------------------------------------------------
    # Portuguese
    # --------------------------------------------------------
    ("bom", "Positive", 1, "por"),
    ("bonita", "Positive", 1, "por"),
    ("gosto", "Positive", 1, "por"),
    ("feliz", "Positive", 1, "por"),
    ("obrigada", "Positive", 1, "por"),

    ("mau", "Negative", 1, "por"),
    ("triste", "Negative", 1, "por"),
]


# ============================================================
# Seed Database
# ============================================================
with app.app_context():

    print("=" * 60)
    print("INITIALIZING DATABASE")
    print("=" * 60)

    # --------------------------------------------------------
    # Create all database tables
    # --------------------------------------------------------
    db.create_all()

    print("✔ Database tables checked/created")


    # ========================================================
    # ADMIN USER
    # ========================================================
    admin = User.query.filter_by(
        username=Config.ADMIN_USERNAME
    ).first()

    if not admin:
        admin = User(
            username=Config.ADMIN_USERNAME,
            email=Config.ADMIN_EMAIL,
            role="ADMIN",
            status="active",
        )

        admin.set_password(Config.ADMIN_PASSWORD)

        db.session.add(admin)

        print(
            f"✔ Admin created: {Config.ADMIN_USERNAME}"
        )

    else:
        # ----------------------------------------------------
        # Admin already exists:
        # reset credentials for development
        # ----------------------------------------------------
        admin.email = Config.ADMIN_EMAIL
        admin.role = "ADMIN"
        admin.status = "active"

        admin.set_password(Config.ADMIN_PASSWORD)

        print(
            f"✔ Admin already exists - password reset: "
            f"{Config.ADMIN_USERNAME}"
        )


    # ========================================================
    # DEMO USER
    # ========================================================
    demo_user = User.query.filter_by(
        username="user"
    ).first()

    if not demo_user:

        demo_user = User(
            username="user",
            email="user@example.com",
            role="USER",
            status="active",
        )

        demo_user.set_password("user123")

        db.session.add(demo_user)

        print("✔ Demo user created: user / user123")

    else:
        # ----------------------------------------------------
        # User already exists:
        # reset password and status
        # ----------------------------------------------------
        demo_user.email = "user@example.com"
        demo_user.role = "USER"
        demo_user.status = "active"

        demo_user.set_password("user123")

        print("✔ Demo user already exists - password reset")


    # ========================================================
    # Save users
    # ========================================================
    db.session.commit()

    print("✔ Users saved")


    # ========================================================
    # SENTIMENT WORDLIST
    # ========================================================
    words_added = 0

    for word, sentiment, score, language in WORDLIST:

        existing_word = SentimentWord.query.filter_by(
            word=word,
            language=language,
        ).first()

        if not existing_word:

            sentiment_word = SentimentWord(
                word=word,
                sentiment=sentiment,
                score=score,
                language=language,
            )

            db.session.add(sentiment_word)
            words_added += 1

    db.session.commit()

    print(
        f"✔ Wordlist seeded: {words_added} new words"
    )


    # ========================================================
    # SENTIMENT LABELS
    # ========================================================
    LABELS = [
        ("Positive", "#16A34A"),
        ("Neutral", "#64748B"),
        ("Negative", "#DC2626"),
    ]

    labels_added = 0

    for name, color in LABELS:

        existing_label = Label.query.filter_by(
            name=name
        ).first()

        if not existing_label:

            label = Label(
                name=name,
                color=color,
            )

            db.session.add(label)
            labels_added += 1

    db.session.commit()

    print(
        f"✔ Labels seeded: {labels_added} new labels"
    )


    # ========================================================
    # Final verification
    # ========================================================
    print()
    print("=" * 60)
    print("DATABASE READY")
    print("=" * 60)

    print(f"Database: facebook_analytics.db")

    print(
        f"Admin username: {Config.ADMIN_USERNAME}"
    )

    print(
        "Demo user username: user"
    )

    print(
        "Demo user password: user123"
    )

    print(
        f"Total users: {User.query.count()}"
    )

    print(
        f"Total sentiment words: {SentimentWord.query.count()}"
    )

    print(
        f"Total labels: {Label.query.count()}"
    )

    print("=" * 60)