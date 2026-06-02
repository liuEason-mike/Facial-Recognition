import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import _redact_database_uri, get_config


def test_redact_database_uri_masks_password():
    uri = "mysql+pymysql://root:secret@127.0.0.1:3306/interrogation"

    assert _redact_database_uri(uri) == "mysql+pymysql://root:***@127.0.0.1:3306/interrogation"


def test_database_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_DATABASE", raising=False)

    cfg = get_config()

    assert cfg["DATABASE_ENABLED"] is False


def test_database_can_be_enabled_explicitly(monkeypatch):
    monkeypatch.setenv("ENABLE_DATABASE", "1")
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://root:secret@127.0.0.1:3306/interrogation")

    cfg = get_config()

    assert cfg["DATABASE_ENABLED"] is True


class FakeDb:
    def __init__(self):
        self.init_calls = 0
        self.create_all_calls = 0

    def init_app(self, _app):
        self.init_calls += 1

    def create_all(self):
        self.create_all_calls += 1


def test_create_app_skips_sqlalchemy_initialization_when_database_disabled(monkeypatch):
    import app as app_module

    fake_db = FakeDb()
    monkeypatch.setenv("ENABLE_DATABASE", "0")
    monkeypatch.setattr(app_module, "db", fake_db)

    flask_app = app_module.create_app()

    assert flask_app.config["DATABASE_ENABLED"] is False
    assert fake_db.init_calls == 0
    assert fake_db.create_all_calls == 0


def test_create_app_initializes_sqlalchemy_when_database_enabled(monkeypatch):
    import app as app_module

    fake_db = FakeDb()
    monkeypatch.setenv("ENABLE_DATABASE", "1")
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://root:secret@127.0.0.1:3306/interrogation")
    monkeypatch.setattr(app_module, "db", fake_db)

    flask_app = app_module.create_app()

    assert flask_app.config["DATABASE_ENABLED"] is True
    assert fake_db.init_calls == 1
    assert fake_db.create_all_calls == 1
