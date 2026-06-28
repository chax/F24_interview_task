from datetime import datetime

from sqlmodel import Session, select, text
from sqlalchemy.exc import IntegrityError

from .model import File


RECURSIVE_FILE_TREE = """
    WITH RECURSIVE FileTree AS (
        -- 1. Anchor member: gets the starting root node
        SELECT *, 0 as depth
        FROM file
        WHERE id = :parent_id

        UNION ALL

        -- 2. Recursive member: joins the CTE to find children
        SELECT f.*, ft.depth + 1
        FROM file f
        JOIN FileTree ft ON f.parent_id = ft.id
    )
"""

class UniqueNameError(Exception):
    pass

class FolderNotEmptyError(Exception):
    pass

def get_by_id(session: Session, file_id: int) -> File | None:
    return session.get(File, file_id)


def get_or_create_root_folder(session: Session) -> File:
    statement = select(File).where(File.parent_id.is_(None), File.is_folder == True)
    root = session.exec(statement).first()
    if root is not None:
        return root
    root = File(name="root", parent_id=None, is_folder=True)
    session.add(root)
    session.commit()
    session.refresh(root)
    return root


def get_children(
    session: Session,
    parent_id: int | None,
    is_folder: bool,
) -> list[File]:
    statement = select(File).where(File.parent_id == parent_id)
    if is_folder is not None:
        statement = statement.where(File.is_folder == is_folder)
    return list(session.exec(statement))


def create_file(session: Session, parent_id: int | None, name: str, is_folder: bool) -> File:
    if parent_id is not None:
        folder = get_by_id(session, parent_id)
        if folder is None:
            return None
    file = File(name, parent_id, is_folder)
    try:
        session.add(file)
        session.commit()
        session.refresh(file)
        return file
    except IntegrityError as e:
        session.rollback()
        raise UniqueNameError(e)


def rename_file(session: Session, file_id: int, name: str) -> File:
    file = get_by_id(session, file_id)
    if file is None:
        return None
    file.name = name
    file.modified = datetime.now()
    try:
        session.add(file)
        session.commit()
        session.refresh(file)
        return file
    except IntegrityError as e:
        session.rollback()
        raise UniqueNameError(e)


def delete_file(session: Session, file_id: int, recursive: bool = False) -> None:
    file = get_by_id(session, file_id)
    if file is not None:
        if len(file.children) == 0 or len(file.children) > 0 and recursive:
            session.delete(file)
            session.commit()
        else:
            raise FolderNotEmptyError()

def search_file(session: Session, starts_with: str, parent_id: int, limit: int = 10) -> list[str]:
    search_query = "SELECT DISTINCT name FROM FileTree WHERE name LIKE :starts_with AND is_folder = 0 ORDER BY name LIMIT :limit"
    query = text(RECURSIVE_FILE_TREE + search_query)
    params = {"parent_id": parent_id, "starts_with": f"{starts_with}%", "limit": limit}
    result = session.exec(query, params=params).scalars().all()
    return result

def get_files_by_name(session: Session, file_name: str, parent_id: int) -> list[File]:
    search_query = "SELECT * FROM FileTree WHERE name = :file_name AND is_folder = 0"
    statement = select(File).from_statement(text(RECURSIVE_FILE_TREE + search_query))
    params = {"parent_id": parent_id, "file_name": file_name}
    result = session.exec(statement, params=params).scalars().all()
    return result

