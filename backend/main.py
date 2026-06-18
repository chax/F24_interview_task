from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session

from db import crud
from db.database import create_db_and_tables, get_session
from db.model import File

SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


def _get_folder_or_404(session: Session, folder_id: int):
    folder = crud.get_by_id(session, folder_id)
    if folder is None or not folder.is_folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@app.get("/folders", response_model=list[File])
async def get_root_folders(session: SessionDep):
    root = crud.get_or_create_root_folder(session)
    return crud.get_children(session, parent_id=root.id, is_folder=True)


@app.get("/folders/{folder_id}", response_model=list[File])
async def get_folders(folder_id: int, session: SessionDep):
    _get_folder_or_404(session, folder_id)
    return crud.get_children(session, parent_id=folder_id, is_folder=True)


@app.get("/files", response_model=list[File])
async def get_root_files(session: SessionDep):
    root = crud.get_or_create_root_folder(session)
    return crud.get_children(session, parent_id=root.id, is_folder=False)


@app.get("/files/{folder_id}", response_model=list[File])
async def get_files(folder_id: int, session: SessionDep):
    _get_folder_or_404(session, folder_id)
    return crud.get_children(session, parent_id=folder_id, is_folder=False)
