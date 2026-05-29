from app.core.config import Settings, get_config


class TestSettings:
    def test_default_values(self) -> None:
        cfg = Settings()
        assert cfg.AI_API_BASE == "https://api.deepseek.com/v1"
        assert cfg.AI_DEFAULT_MODEL == "deepseek-v4-flash"
        assert cfg.AI_STRONG_MODEL == "deepseek-v4-pro"
        assert cfg.DATABASE_URL == "sqlite:///reviewpilot.db"
        assert cfg.APP_HOST == "0.0.0.0"
        assert cfg.APP_PORT == 8000
        assert cfg.LOG_LEVEL == "INFO"

    def test_optional_fields_default_empty(self) -> None:
        cfg = Settings()
        assert cfg.GITHUB_APP_ID == ""
        assert cfg.GITHUB_APP_PRIVATE_KEY == ""
        assert cfg.SECRET_KEY == ""

    def test_get_config_returns_settings(self) -> None:
        cfg = get_config()
        assert isinstance(cfg, Settings)

    def test_get_config_is_singleton(self) -> None:
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2


class TestMockConfig:
    def test_mock_config_overrides(self, mock_config: Settings) -> None:
        assert mock_config.GITHUB_APP_ID == "test_app_id"
        assert mock_config.GITHUB_WEBHOOK_SECRET == "test_secret"
        assert mock_config.AI_API_KEY == "test_ai_key"
        assert mock_config.APP_HOST == "127.0.0.1"
        assert mock_config.APP_PORT == 9999
        assert mock_config.LOG_LEVEL == "DEBUG"

    def test_multiline_private_key(self, mock_config: Settings) -> None:
        assert "BEGIN RSA PRIVATE KEY" in mock_config.GITHUB_APP_PRIVATE_KEY
        assert "END RSA PRIVATE KEY" in mock_config.GITHUB_APP_PRIVATE_KEY
