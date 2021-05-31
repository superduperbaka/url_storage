from pydantic import BaseModel, Extra, Field, validator
from urllib.parse import urlparse


class CreateRequest(BaseModel):
    link: str = Field(..., max_length=4096, )
    short_name: str = Field(..., max_length=256)

    @validator('link', pre=False)
    def to_upper(cls, v: str):
        result = urlparse(v)
        if not all([result.scheme, result.netloc]):
            raise ValueError(f'Can not validate link {v}')
        return v

    class Config:
        extra = Extra.ignore


class Statistics(BaseModel):
    short_name: str = Field(...)
    count: int = Field(...)
