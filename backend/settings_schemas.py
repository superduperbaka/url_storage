from pydantic import BaseSettings, Field


class PostgreSQLSettings(BaseSettings):
    host: str = Field(default='localhost', env='POSTGRES_HOST')
    port: int = Field(5432, env='POSTGRES_PORT')
    database: str = Field(default='postgres', env='POSTGRES_DATABASE')
    user: str = Field('postgres', env='POSTGRES_USER')
    password: str = Field('somefancypass', env='POSTGRES_PASSWORD')

    @property
    def postgres_dsn(self) -> str:
        return f'postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'
