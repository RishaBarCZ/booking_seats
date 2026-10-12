from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Настройки приложения."""

    # Общие настройки
    title: str = 'Система бронирования мест в кафе'
    version: str = '0.0.3'
    description: str = 'API для бронирования мест в кафе'

    # Настройки администратора
    admin_username: str
    admin_email: str
    admin_password: str

    # Настройки подключения к БД
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_server: str = 'localhost'
    postgres_port: int = 5432

    # Настройки подключения к Redis
    redis_host: str = 'redis'
    redis_port: int = 6379

    # Настройки хранилища медиа-файлов
    media_storage_path: Path = BASE_DIR.parent / 'media_storage'

    # JWT настройки
    jwt_secret_key: str
    jwt_algorithm: str = 'HS256'
    jwt_access_token_expire_minutes: int = 60

    # Настройки для отправки email
    email_from: str = ''
    email_password: str = ''
    smtp_host: str
    smtp_port: int

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / '../infra/.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    @property
    def db_url(self) -> str:
        """Строка подключения к БД."""
        return (
            f'postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@'
            f'{self.postgres_server}:{self.postgres_port}/{self.postgres_db}'
        )

    @property
    def redis_url(self) -> str:
        """Строка подключения к Redis."""
        return f'redis://{self.redis_host}:{self.redis_port}/0'


settings = Settings()
