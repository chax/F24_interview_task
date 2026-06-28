from db import crud


def test_root_folder_path_is_slash(session):
    root = crud.get_or_create_root_folder(session)
    assert root.path == "/"


def test_top_level_file_path(session):
    root = crud.get_or_create_root_folder(session)
    file = crud.create_file(session, root.id, "notes.txt", is_folder=False)

    assert file.path == "/notes.txt"


def test_nested_file_path_reflects_folder_chain(session):
    root = crud.get_or_create_root_folder(session)
    folder = crud.create_file(session, root.id, "docs", is_folder=True)
    nested_folder = crud.create_file(session, folder.id, "drafts", is_folder=True)
    file = crud.create_file(session, nested_folder.id, "notes.txt", is_folder=False)

    assert file.path == "/docs/drafts/notes.txt"


def test_path_recomputes_after_rename(session):
    root = crud.get_or_create_root_folder(session)
    folder = crud.create_file(session, root.id, "docs", is_folder=True)
    file = crud.create_file(session, folder.id, "notes.txt", is_folder=False)

    crud.rename_file(session, folder.id, "renamed-docs")
    session.refresh(file)

    assert file.path == "/renamed-docs/notes.txt"
