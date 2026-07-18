import json
import os

DEFAULTS = {
    "username": "User",
    "port": 5050,
    "blocked_ips": []
}

_settings_path = None


def _get_path():
    global _settings_path
    if _settings_path:
        return _settings_path
    try:
        from android.storage import app_storage_path  # type: ignore
        base = app_storage_path()
    except Exception:
        base = os.path.expanduser("~")
    _settings_path = os.path.join(base, ".bukp_settings.json")
    return _settings_path


def load():
    path = _get_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                for k, v in DEFAULTS.items():
                    data.setdefault(k, v)
                return data
        except Exception:
            pass
    return dict(DEFAULTS)


def save(settings: dict):
    with open(_get_path(), "w") as f:
        json.dump(settings, f, indent=2)
