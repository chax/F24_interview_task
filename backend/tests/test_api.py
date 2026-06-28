def test_get_folders_defaults_to_root(client):
    client.post("/folders/create", params={"name": "docs"})

    response = client.get("/folders")

    assert response.status_code == 200
    names = [f["name"] for f in response.json()]
    assert names == ["docs"]


def test_get_folders_with_missing_parent_id_returns_404(client):
    response = client.get("/folders", params={"parent_id": 99999})
    assert response.status_code == 404


def test_create_folder_returns_created_folder(client):
    response = client.post("/folders/create", params={"name": "docs"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "docs"
    assert body["path"] == "/docs"


def test_create_folder_duplicate_name_returns_400(client):
    client.post("/folders/create", params={"name": "docs"})
    response = client.post("/folders/create", params={"name": "docs"})

    assert response.status_code == 400


def test_create_folder_with_missing_parent_returns_404(client):
    response = client.post(
        "/folders/create", params={"name": "docs", "parent_id": 99999}
    )
    assert response.status_code == 404


def test_create_nested_folder(client):
    parent = client.post("/folders/create", params={"name": "docs"}).json()
    response = client.post(
        "/folders/create", params={"name": "drafts", "parent_id": parent["id"]}
    )

    assert response.status_code == 200
    assert response.json()["path"] == "/docs/drafts"


def test_create_and_list_files(client):
    response = client.post("/files/create", params={"name": "notes.txt"})

    assert response.status_code == 200
    assert response.json()["path"] == "/notes.txt"

    listed = client.get("/files")
    assert [f["name"] for f in listed.json()] == ["notes.txt"]


def test_create_file_duplicate_name_returns_400(client):
    client.post("/files/create", params={"name": "notes.txt"})
    response = client.post("/files/create", params={"name": "notes.txt"})

    assert response.status_code == 400


def test_files_and_folders_with_same_name_in_same_parent_conflict(client):
    client.post("/folders/create", params={"name": "shared"})
    response = client.post("/files/create", params={"name": "shared"})

    assert response.status_code == 400


def test_get_files_does_not_include_folders(client):
    client.post("/folders/create", params={"name": "docs"})
    client.post("/files/create", params={"name": "notes.txt"})

    response = client.get("/files")

    assert [f["name"] for f in response.json()] == ["notes.txt"]


def test_rename_folder(client):
    folder = client.post("/folders/create", params={"name": "docs"}).json()

    response = client.post(
        "/folders/rename", params={"file_id": folder["id"], "name": "documents"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "documents"


def test_rename_file(client):
    file = client.post("/files/create", params={"name": "old.txt"}).json()

    response = client.post(
        "/files/rename", params={"file_id": file["id"], "name": "new.txt"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "new.txt"


def test_rename_to_duplicate_name_returns_400(client):
    client.post("/files/create", params={"name": "taken.txt"})
    movable = client.post("/files/create", params={"name": "movable.txt"}).json()

    response = client.post(
        "/files/rename", params={"file_id": movable["id"], "name": "taken.txt"}
    )

    assert response.status_code == 400


def test_delete_file(client):
    file = client.post("/files/create", params={"name": "throwaway.txt"}).json()

    response = client.delete("/files/delete", params={"file_id": file["id"]})
    assert response.status_code == 200

    listed = client.get("/files")
    assert listed.json() == []


def test_delete_nonempty_folder_without_recursive_returns_400(client):
    folder = client.post("/folders/create", params={"name": "docs"}).json()
    client.post(
        "/files/create", params={"name": "inside.txt", "parent_id": folder["id"]}
    )

    response = client.delete("/folders/delete", params={"file_id": folder["id"]})

    assert response.status_code == 400


def test_delete_nonempty_folder_recursive_succeeds(client):
    folder = client.post("/folders/create", params={"name": "docs"}).json()
    client.post(
        "/files/create", params={"name": "inside.txt", "parent_id": folder["id"]}
    )

    response = client.delete(
        "/folders/delete", params={"file_id": folder["id"], "recursive": True}
    )
    assert response.status_code == 200

    # The folder is gone, so listing its (former) contents 404s.
    follow_up = client.get("/files", params={"parent_id": folder["id"]})
    assert follow_up.status_code == 404


def test_search_files_returns_matching_names(client):
    client.post("/files/create", params={"name": "foobar.txt"})
    client.post("/files/create", params={"name": "bar.txt"})

    response = client.get("/files/search", params={"starts_with": "foo"})

    assert response.status_code == 200
    assert response.json() == ["foobar.txt"]


def test_search_files_scoped_to_parent_id(client):
    folder_a = client.post("/folders/create", params={"name": "a"}).json()
    folder_b = client.post("/folders/create", params={"name": "b"}).json()
    client.post(
        "/files/create", params={"name": "fooInA.txt", "parent_id": folder_a["id"]}
    )
    client.post(
        "/files/create", params={"name": "fooInB.txt", "parent_id": folder_b["id"]}
    )

    response = client.get(
        "/files/search", params={"starts_with": "foo", "parent_id": folder_a["id"]}
    )

    assert response.json() == ["fooInA.txt"]


def test_search_files_with_missing_parent_returns_404(client):
    response = client.get(
        "/files/search", params={"starts_with": "foo", "parent_id": 99999}
    )
    assert response.status_code == 404


def test_get_files_by_name_returns_exact_matches(client):
    folder_a = client.post("/folders/create", params={"name": "a"}).json()
    folder_b = client.post("/folders/create", params={"name": "b"}).json()
    client.post(
        "/files/create", params={"name": "report.txt", "parent_id": folder_a["id"]}
    )
    client.post(
        "/files/create", params={"name": "report.txt", "parent_id": folder_b["id"]}
    )

    response = client.get("/files/get_by_name", params={"file_name": "report.txt"})

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_files_by_name_no_match_returns_empty_list(client):
    response = client.get("/files/get_by_name", params={"file_name": "missing.txt"})

    assert response.status_code == 200
    assert response.json() == []
