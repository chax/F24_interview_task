from datetime import datetime
from typing import Optional

from pydantic import computed_field
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

class File(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    is_folder: bool = Field(default=False, exclude=True)
    name: str = Field(index=True)
    created: datetime = Field(default_factory=datetime.now)
    modified: datetime = Field(default_factory=datetime.now)
    parent_id: int | None = Field(
        default=None,
        foreign_key="file.id",
        index=True,
        ondelete="CASCADE",
    )
    parent_folder: Optional["File"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "File.id"},
    )
    children: list["File"] = Relationship(
        back_populates="parent_folder",
        cascade_delete=True,
        sa_relationship_kwargs={
            "single_parent": True,
        },
    )

    def __init__(self, name: str, parent_id: int | None, is_folder: bool = False):
        self.name = name
        self.parent_id = parent_id
        self.is_folder = is_folder

    __table_args__ = (UniqueConstraint("name", "parent_id"), )

    @computed_field
    @property
    def path(self) -> str:
        # Walks the parent_folder chain up to (but not including) the root row,
        # so it's recomputed from current names on every fetch instead of stored.
        parts: list[str] = []
        node: Optional["File"] = self
        while node is not None and node.parent_id is not None:
            parts.append(node.name)
            node = node.parent_folder
        return "/" + "/".join(reversed(parts))
