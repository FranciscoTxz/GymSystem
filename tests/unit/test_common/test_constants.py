import importlib

from common import constants


def test_constants_read_values_from_environment(monkeypatch):
    expected_values = {
        "SECRET_KEY": "test-secret",
        "MONGODB_URI": "mongodb://localhost:27017/test",
        "SENDER_EMAIL": "sender@example.com",
        "SENDER_PASSWORD": "test-password",
        "ADMIN_EMAIL": "admin@example.com",
    }
    for name, value in expected_values.items():
        monkeypatch.setenv(name, value)

    reloaded_constants = importlib.reload(constants)

    for name, value in expected_values.items():
        assert getattr(reloaded_constants, name) == value
