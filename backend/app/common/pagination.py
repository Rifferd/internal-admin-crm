from math import ceil

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PageMeta(BaseModel):
    page: int
    size: int
    total: int
    pages: int


def build_page_meta(page: int, size: int, total: int) -> PageMeta:
    pages = ceil(total / size) if total > 0 else 0

    return PageMeta(
        page=page,
        size=size,
        total=total,
        pages=pages,
    )