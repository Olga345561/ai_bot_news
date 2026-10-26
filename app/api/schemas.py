from pydantic import BaseModel


class NewsItemCreate(BaseModel):
    title: str
    url: str | None = None
    summary: str
    source: str
    published_at: str
    raw_text: str
