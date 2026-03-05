from app.config import load_config, validate_config


def test_validate_config_fills_defaults() -> None:
    validated = validate_config({"voice": {"hotword": "кряква"}})
    assert validated.voice.hotword == "кряква"
    assert validated.ui.scale == 1.0
    assert validated.llm.model


def test_load_config_returns_dict_shape() -> None:
    cfg = load_config()
    assert "voice" in cfg
    assert "ui" in cfg
    assert "llm" in cfg
