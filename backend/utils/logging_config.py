import logging
import os

def setup_logging(app):
    log_dir = app.config["LOG_FOLDER"]
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Application started.")