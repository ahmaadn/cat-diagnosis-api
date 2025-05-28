from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    PROJECT_NAME: str
    API_V1_STR: str = "v1"

    DB_DRIVER: str
    DB_SERVER: str
    DB_PORT: int
    DB_DATABASE: str
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_SSLMODE: str
    DB_SSLROOTCERT: str

    @computed_field
    @property
    def db_url(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme=self.DB_DRIVER,
            username=self.DB_USERNAME,
            password=self.DB_PASSWORD,
            host=self.DB_SERVER,
            port=self.DB_PORT,
            path=self.DB_DATABASE,
        )


def _singleton(cls):
    _instances = {}

    def warp():
        if cls not in _instances:
            _instances[cls] = cls()
        return _instances[cls]

    return warp


Settings = _singleton(Settings)  # type: ignore


def get_settings() -> "Settings":
    """Mendapatkan setting

    Returns
    -------
        Settings: instance settings

    """
    return Settings()  # type: ignore


settings = get_settings()

if __name__ == "__main__":
    print(settings)
