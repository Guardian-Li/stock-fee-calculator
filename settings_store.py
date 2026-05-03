import json

from app_config import DEFAULT_COMMISSION_PER_TEN_THOUSAND, DEFAULT_MIN_COMMISSION, SETTINGS_FILE


def default_settings():
    return {
        "commission_per_ten_thousand": str(DEFAULT_COMMISSION_PER_TEN_THOUSAND),
        "min_commission": str(DEFAULT_MIN_COMMISSION),
    }


def load_settings():
    defaults = default_settings()
    if not SETTINGS_FILE.exists():
        save_settings(defaults["commission_per_ten_thousand"], defaults["min_commission"])
        return defaults
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        save_settings(defaults["commission_per_ten_thousand"], defaults["min_commission"])
        return defaults

    settings = defaults.copy()
    for key in settings:
        value = str(data.get(key, "")).strip()
        if value:
            settings[key] = value
    return settings


def save_settings(commission_per_ten_thousand, min_commission):
    data = {
        "commission_per_ten_thousand": str(commission_per_ten_thousand),
        "min_commission": str(min_commission),
    }
    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
