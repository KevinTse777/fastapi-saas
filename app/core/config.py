from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    app_name: str = "fastapi-saas"

    mysql_host: str = "mysql"
    mysql_port: int = 3306
    mysql_db: str = "appdb"
    mysql_user: str = "appuser"
    mysql_password: str = "apppass"

    redis_host: str = "redis"
    redis_port: int = 6379

    jwt_secret: str = "jofeswfoi"
    jwt_alg: str = "HS256"

    @property
    def mysql_dsn(self) -> str:
        # SQLAlchemy + PyMySQL
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"
        )

    @property
    def redis_dsn(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"


settings = Settings()
