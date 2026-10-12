import logging
import os
import sys
from logging.handlers import RotatingFileHandler


class DefaultFormatter(logging.Formatter):
    """Форматтер с дефолтным значением для поля user."""

    def format(self, record: logging.LogRecord) -> str:
        """Добавляет user=SYSTEM если user не передан."""
        if not hasattr(record, 'user'):
            record.user = 'SYSTEM'
        return super().format(record)


def setup_logger(name: str) -> logging.Logger:
    """Настраивает логгер с выводом в консоль и файл с ротацией."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = DefaultFormatter(
        '%(asctime)s | %(levelname)s | %(name)s | user=%(user)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    os.makedirs('logs', exist_ok=True)
    file_handler = RotatingFileHandler(
        filename='logs/app.log',
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8',
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def get_user_logger(
    logger: logging.Logger,
    username: str | None = None,
    user_id: int | None = None,
) -> logging.LoggerAdapter:
    """Возвращает LoggerAdapter с контекстом пользователя."""
    user = f'{username}({user_id})' if username else 'SYSTEM'
    return logging.LoggerAdapter(logger, {'user': user})
