from datetime import datetime

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from .model import File

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
        raise UniqueNameError(e)


def delete_file(session: Session, file_id: int, recursive: bool = False) -> None:
    file = get_by_id(session, file_id)
    if file is not None:
        if len(file.children) == 0 or len(file.children) > 0 and recursive:
            session.delete(file)
            session.commit()
        else:
            raise FolderNotEmptyError()

