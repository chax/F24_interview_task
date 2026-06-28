from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session

from db import crud
from db.database import create_db_and_tables, engine, get_session
from db.model import File

SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # Ensure the root folder exists before serving requests, so concurrent
    # first requests can't race on creating it: SQLite's (name, parent_id)
    # unique constraint does not protect rows where parent_id IS NULL.
    with Session(engine) as session:
        crud.get_or_create_root_folder(session)
    yield


app = FastAPI(lifespan=lifespan)


def _get_folder_or_404(session: Session, folder_id: int | None):
    # if folder_id is None treat it as a root folder
    if folder_id is None:
        return crud.get_or_create_root_folder(session)
    
    # else try to find a folder by id and raise Exception if it doesn't exist
    folder = crud.get_by_id(session, folder_id)
    if folder is None or not folder.is_folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@app.get("/folders", response_model=list[File])
async def get_folders(session: SessionDep, parent_id: int | None = None):
    parent = _get_folder_or_404(session, parent_id)
    return crud.get_children(session, parent.id, is_folder=True)

@app.post("/folders/create")
async def create_folder(session: SessionDep, name: str, parent_id: int | None = None):
    parent = _get_folder_or_404(session, parent_id)
    try:
        return crud.create_file(session, parent.id, name, is_folder=True)
    except crud.UniqueNameError:
        raise HTTPException(status_code=400, detail="File names in same folder must be unique.")

@app.get("/files", response_model=list[File])
async def get_root_files(session: SessionDep, parent_id: int | None = None):
    parent = _get_folder_or_404(session, parent_id)
    return crud.get_children(session, parent.id, is_folder=False)

@app.post("/files/create")
async def create_file(session: SessionDep, name: str, parent_id: int | None = None):
    parent = _get_folder_or_404(session, parent_id)
    try:
        return crud.create_file(session, parent.id, name, is_folder=False)
    except crud.UniqueNameError:
        raise HTTPException(status_code=400, detail="File names in same folder must be unique.")

@app.post("/folders/rename")
@app.post("/files/rename")
async def rename_file(session: SessionDep, file_id: int, name: str):
    try:
        renamed = crud.rename_file(session, file_id, name)
    except crud.UniqueNameError:
        raise HTTPException(status_code=400, detail="File names in same folder must be unique.")
    if renamed is None:
        raise HTTPException(status_code=404, detail="File not found")
    return renamed

@app.delete("/folders/delete")
@app.delete("/files/delete")
async def delete_path(session: SessionDep, file_id: int, recursive: bool = False):
    try:
        return crud.delete_file(session, file_id, recursive)
    except crud.FolderNotEmptyError:
        raise HTTPException(status_code=400, detail="Folder not empty")

@app.get("/files/search")
async def search_file(session: SessionDep, starts_with: str, parent_id: int | None = None):
    parent = _get_folder_or_404(session, parent_id)
    return crud.search_file(session, starts_with, parent.id)

@app.get("/files/get_by_name")
async def get_files_by_name(session: SessionDep, file_name: str, parent_id: int | None = None):
    parent = _get_folder_or_404(session, parent_id)
    return crud.get_files_by_name(session, file_name, parent.id)
