from datetime import datetime

import pytest

from db import crud


def test_get_or_create_root_folder_creates_once(session):
    root = crud.get_or_create_root_folder(session)
    assert root.id is not None
    assert root.is_folder is True
    assert root.parent_id is None

    again = crud.get_or_create_root_folder(session)
    assert again.id == root.id


def test_get_by_id_missing_returns_none(session):
    assert crud.get_by_id(session, 12345) is None


def test_create_file_under_root(session):
    root = crud.get_or_create_root_folder(session)
    file = crud.create_file(session, root.id, "notes.txt", is_folder=False)

    assert file.id is not None
    assert file.name == "notes.txt"
    assert file.parent_id == root.id
    assert file.is_folder is False


def test_create_folder_under_root(session):
    root = crud.get_or_create_root_folder(session)
    folder = crud.create_file(session, root.id, "docs", is_folder=True)

    assert folder.is_folder is True
    assert folder.parent_id == root.id


def test_create_file_with_missing_parent_returns_none(session):
    assert crud.create_file(session, 99999, "orphan.txt", is_folder=False) is None


def test_create_file_duplicate_name_in_same_parent_raises(session):
    root = crud.get_or_create_root_folder(session)
    crud.create_file(session, root.id, "dup.txt", is_folder=False)

    with pytest.raises(crud.UniqueNameError):
        crud.create_file(session, root.id, "dup.txt", is_folder=False)


def test_session_stays_usable_after_create_duplicate_error(session):
    # IntegrityError must roll back the session, otherwise any later use of
    # this same session raises sqlalchemy.exc.PendingRollbackError.
    root = crud.get_or_create_root_folder(session)
    crud.create_file(session, root.id, "dup.txt", is_folder=False)
    with pytest.raises(crud.UniqueNameError):
        crud.create_file(session, root.id, "dup.txt", is_folder=False)

    file = crud.create_file(session, root.id, "after.txt", is_folder=False)
    assert file.name == "after.txt"


def test_session_stays_usable_after_rename_duplicate_error(session):
    root = crud.get_or_create_root_folder(session)
    crud.create_file(session, root.id, "taken.txt", is_folder=False)
    movable = crud.create_file(session, root.id, "movable.txt", is_folder=False)
    with pytest.raises(crud.UniqueNameError):
        crud.rename_file(session, movable.id, "taken.txt")

    file = crud.create_file(session, root.id, "after.txt", is_folder=False)
    assert file.name == "after.txt"


def test_create_file_duplicate_name_clashes_across_file_and_folder_types(session):
    # The unique constraint is on (name, parent_id) only, so a folder and a
    # file can't share a name in the same parent either.
    root = crud.get_or_create_root_folder(session)
    crud.create_file(session, root.id, "shared", is_folder=True)

    with pytest.raises(crud.UniqueNameError):
        crud.create_file(session, root.id, "shared", is_folder=False)


def test_create_file_same_name_allowed_in_different_parents(session):
    root = crud.get_or_create_root_folder(session)
    folder_a = crud.create_file(session, root.id, "a", is_folder=True)
    folder_b = crud.create_file(session, root.id, "b", is_folder=True)

    file_a = crud.create_file(session, folder_a.id, "report.txt", is_folder=False)
    file_b = crud.create_file(session, folder_b.id, "report.txt", is_folder=False)

    assert file_a.id != file_b.id
    assert file_a.name == file_b.name == "report.txt"


def test_get_children_filters_by_is_folder(session):
    root = crud.get_or_create_root_folder(session)
    crud.create_file(session, root.id, "docs", is_folder=True)
    crud.create_file(session, root.id, "notes.txt", is_folder=False)

    folders = crud.get_children(session, root.id, is_folder=True)
    files = crud.get_children(session, root.id, is_folder=False)

    assert [f.name for f in folders] == ["docs"]
    assert [f.name for f in files] == ["notes.txt"]


def test_get_children_empty_for_childless_folder(session):
    root = crud.get_or_create_root_folder(session)
    folder = crud.create_file(session, root.id, "empty", is_folder=True)

    assert crud.get_children(session, folder.id, is_folder=True) == []
    assert crud.get_children(session, folder.id, is_folder=False) == []


def test_rename_file_updates_name_and_modified(session):
    root = crud.get_or_create_root_folder(session)
    file = crud.create_file(session, root.id, "old.txt", is_folder=False)

    before_rename = datetime.now()
    renamed = crud.rename_file(session, file.id, "new.txt")

    assert renamed.id == file.id
    assert renamed.name == "new.txt"
    assert renamed.modified >= before_rename


def test_rename_file_missing_id_returns_none(session):
    assert crud.rename_file(session, 99999, "whatever") is None


def test_rename_file_to_duplicate_name_raises(session):
    root = crud.get_or_create_root_folder(session)
    crud.create_file(session, root.id, "taken.txt", is_folder=False)
    file = crud.create_file(session, root.id, "movable.txt", is_folder=False)

    with pytest.raises(crud.UniqueNameError):
        crud.rename_file(session, file.id, "taken.txt")


def test_delete_file_missing_id_is_noop(session):
    assert crud.delete_file(session, 99999) is None


def test_delete_empty_file(session):
    root = crud.get_or_create_root_folder(session)
    file = crud.create_file(session, root.id, "throwaway.txt", is_folder=False)

    crud.delete_file(session, file.id)

    assert crud.get_by_id(session, file.id) is None


def test_delete_nonempty_folder_without_recursive_raises(session):
    root = crud.get_or_create_root_folder(session)
    folder = crud.create_file(session, root.id, "docs", is_folder=True)
    crud.create_file(session, folder.id, "inside.txt", is_folder=False)

    with pytest.raises(crud.FolderNotEmptyError):
        crud.delete_file(session, folder.id, recursive=False)

    # Folder and its child must remain untouched after the failed delete.
    assert crud.get_by_id(session, folder.id) is not None
    assert len(crud.get_children(session, folder.id, is_folder=False)) == 1


def test_delete_nonempty_folder_recursive_removes_descendants(session):
    root = crud.get_or_create_root_folder(session)
    folder = crud.create_file(session, root.id, "docs", is_folder=True)
    child_file = crud.create_file(session, folder.id, "inside.txt", is_folder=False)
    nested_folder = crud.create_file(session, folder.id, "nested", is_folder=True)
    grandchild = crud.create_file(session, nested_folder.id, "deep.txt", is_folder=False)

    crud.delete_file(session, folder.id, recursive=True)

    assert crud.get_by_id(session, folder.id) is None
    assert crud.get_by_id(session, child_file.id) is None
    assert crud.get_by_id(session, nested_folder.id) is None
    assert crud.get_by_id(session, grandchild.id) is None


def test_search_file_matches_prefix_case_insensitively(session):
    root = crud.get_or_create_root_folder(session)
    crud.create_file(session, root.id, "Foobar.txt", is_folder=False)
    crud.create_file(session, root.id, "bar.txt", is_folder=False)

    result = crud.search_file(session, "foo", root.id)

    assert result == ["Foobar.txt"]


def test_search_file_excludes_non_prefix_matches(session):
    root = crud.get_or_create_root_folder(session)
    crud.create_file(session, root.id, "foobar.txt", is_folder=False)

    assert crud.search_file(session, "bar", root.id) == []


def test_search_file_treats_percent_as_literal_not_wildcard(session):
    root = crud.get_or_create_root_folder(session)
    crud.create_file(session, root.id, "100%off.txt", is_folder=False)
    crud.create_file(session, root.id, "100xyz.txt", is_folder=False)

    assert crud.search_file(session, "100%", root.id) == ["100%off.txt"]


def test_search_file_treats_underscore_as_literal_not_wildcard(session):
    root = crud.get_or_create_root_folder(session)
    crud.create_file(session, root.id, "a_b.txt", is_folder=False)
    crud.create_file(session, root.id, "axb.txt", is_folder=False)

    assert crud.search_file(session, "a_", root.id) == ["a_b.txt"]


def test_search_file_with_only_wildcard_characters_matches_nothing(session):
    root = crud.get_or_create_root_folder(session)
    crud.create_file(session, root.id, "report.txt", is_folder=False)

    assert crud.search_file(session, "%", root.id) == []
    assert crud.search_file(session, "_", root.id) == []


def test_search_file_excludes_folders(session):
    root = crud.get_or_create_root_folder(session)
    crud.create_file(session, root.id, "fooFolder", is_folder=True)
    crud.create_file(session, root.id, "fooFile.txt", is_folder=False)

    assert crud.search_file(session, "foo", root.id) == ["fooFile.txt"]


def test_search_file_is_scoped_to_subtree(session):
    root = crud.get_or_create_root_folder(session)
    folder_a = crud.create_file(session, root.id, "a", is_folder=True)
    folder_b = crud.create_file(session, root.id, "b", is_folder=True)
    crud.create_file(session, folder_a.id, "fooInA.txt", is_folder=False)
    crud.create_file(session, folder_b.id, "fooInB.txt", is_folder=False)

    assert crud.search_file(session, "foo", folder_a.id) == ["fooInA.txt"]
    assert sorted(crud.search_file(session, "foo", root.id)) == ["fooInA.txt", "fooInB.txt"]


def test_search_file_respects_limit_and_orders_alphabetically(session):
    root = crud.get_or_create_root_folder(session)
    for i in range(15):
        crud.create_file(session, root.id, f"item{i:02d}.txt", is_folder=False)

    result = crud.search_file(session, "item", root.id, limit=10)

    assert len(result) == 10
    assert result == sorted(result)


def test_search_file_dedupes_same_name_in_different_subfolders(session):
    root = crud.get_or_create_root_folder(session)
    folder_a = crud.create_file(session, root.id, "a", is_folder=True)
    folder_b = crud.create_file(session, root.id, "b", is_folder=True)
    crud.create_file(session, folder_a.id, "report.txt", is_folder=False)
    crud.create_file(session, folder_b.id, "report.txt", is_folder=False)

    assert crud.search_file(session, "report", root.id) == ["report.txt"]


def test_get_files_by_name_returns_all_matches_in_subtree(session):
    root = crud.get_or_create_root_folder(session)
    folder_a = crud.create_file(session, root.id, "a", is_folder=True)
    folder_b = crud.create_file(session, root.id, "b", is_folder=True)
    file_a = crud.create_file(session, folder_a.id, "report.txt", is_folder=False)
    file_b = crud.create_file(session, folder_b.id, "report.txt", is_folder=False)

    result = crud.get_files_by_name(session, "report.txt", root.id)

    assert {f.id for f in result} == {file_a.id, file_b.id}


def test_get_files_by_name_scoped_to_parent(session):
    root = crud.get_or_create_root_folder(session)
    folder_a = crud.create_file(session, root.id, "a", is_folder=True)
    folder_b = crud.create_file(session, root.id, "b", is_folder=True)
    file_a = crud.create_file(session, folder_a.id, "report.txt", is_folder=False)
    crud.create_file(session, folder_b.id, "report.txt", is_folder=False)

    result = crud.get_files_by_name(session, "report.txt", folder_a.id)

    assert [f.id for f in result] == [file_a.id]


def test_get_files_by_name_excludes_folders(session):
    root = crud.get_or_create_root_folder(session)
    crud.create_file(session, root.id, "report.txt", is_folder=True)

    assert crud.get_files_by_name(session, "report.txt", root.id) == []


def test_get_files_by_name_no_match_returns_empty_list(session):
    root = crud.get_or_create_root_folder(session)
    assert crud.get_files_by_name(session, "missing.txt", root.id) == []
