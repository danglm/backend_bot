import json
import os
from typing import Any, Dict, Optional
from pydantic import BaseModel, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class DBConfig(BaseModel):
    Project_Name: str = "Backend Project"
    Postgres_Server: str = "localhost"
    Postgres_User: str = "postgres"
    Postgres_Password: str = "admin123"
    Postgres_DB: str = "server_01"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @model_validator(mode="after")
    def assemble_db_connection(self) -> "DBConfig":
        if not self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql://{self.Postgres_User}:{self.Postgres_Password}@"
                f"{self.Postgres_Server}/{self.Postgres_DB}"
            )
        return self

class IMPConfig(BaseModel):
    Enable_API: bool = True

class AuthConfig(BaseModel):
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7" # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

class ServiceConfig(BaseModel):
    IP_Address: str = "localhost"
    Port: int = 8000

class TienNgaConfig(BaseModel):
    Max_Daily_Payment_Auto_Approve: float = 1000000000.0

class Settings(BaseSettings):
    DB_Config: DBConfig = DBConfig()
    IMP_Config: IMPConfig = IMPConfig()
    Auth: AuthConfig = AuthConfig()
    Service: ServiceConfig = ServiceConfig()
    TienNga: TienNgaConfig = TienNgaConfig()

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple[Any, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            JsonConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

class JsonConfigSettingsSource:
    def __init__(self, settings_cls: type[BaseSettings]):
        self.settings_cls = settings_cls

    def __call__(self) -> Dict[str, Any]:
        encoding = "utf-8"
        json_file = "appsettings.json"
        if os.path.exists(json_file):
            with open(json_file, encoding=encoding) as f:
                return json.load(f)
        return {}

# Instantiate settings once to be used throughout the project
settings = Settings()
