import logging
import structlog

from app.core.logging import get_logger, setup_logging


class TestSetupLogging:
    def test_setup_logging_completes_without_error(self) -> None:
        setup_logging()

    def test_setup_logging_with_different_levels(self) -> None:
        for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
            structlog.reset_defaults()
            logging.getLogger().setLevel(getattr(logging, level))
            setup_logging()


class TestGetLogger:
    def test_returns_structlog_logger(self) -> None:
        logger = get_logger(__name__)
        assert hasattr(logger, "bind")
        assert hasattr(logger, "unbind")

    def test_logger_binds_methods_exist(self) -> None:
        logger = get_logger(__name__)
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")

    def test_logger_can_log_without_error(self) -> None:
        logger = get_logger("test_logger")
        logger.info("test_message", key="value")
