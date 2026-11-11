from pydantic import BaseModel


class NewsItemCreate(BaseModel):
    title: str
    url: str | None = None
    summary: str
    source: str
    published_at: str
    raw_text: str

class SourceCreate(BaseModel):
    type: str
    name: str | None = None
    url: str | None = None
    enabled: bool = True

class SourceUpdate(BaseModel):
    enabled: bool

class KeywordCreate(BaseModel):
    word: str

class KeywordUpdate(BaseModel):
    word: str