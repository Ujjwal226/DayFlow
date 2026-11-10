import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.models.category import Category
from app.models.project import Project
from app.models.tag import Tag
from app.models.task import Task
from app.models.user import User


@pytest.fixture
def user_a(db_session):
    user = User(
        email="note_user_a@example.com",
        display_name="Notes User A",
        hashed_password=hash_password("PasswordA123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_b(db_session):
    user = User(
        email="note_user_b@example.com",
        display_name="Notes User B",
        hashed_password=hash_password("PasswordB123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_a(user_a):
    token = create_access_token(user_id=user_a.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_b(user_b):
    token = create_access_token(user_id=user_b.id)
    return {"Authorization": f"Bearer {token}"}


def test_note_crud_and_tenant_isolation(
    client: TestClient,
    user_a: User,
    user_b: User,
    auth_headers_a: dict,
    auth_headers_b: dict,
    db_session,
):
    # 1. Create Note as User A
    create_payload = {
        "title": "Architecture Ideas",
        "content": "# System Design\n- Point 1\n- Point 2",
        "is_pinned": True,
    }
    res = client.post("/api/v1/notes", json=create_payload, headers=auth_headers_a)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["title"] == "Architecture Ideas"
    assert data["content"] == "# System Design\n- Point 1\n- Point 2"
    assert data["is_pinned"] is True
    assert data["is_archived"] is False
    note_id = data["id"]

    # 2. Retrieve Note as User A
    res = client.get(f"/api/v1/notes/{note_id}", headers=auth_headers_a)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["id"] == note_id

    # 3. Tenant isolation: User B cannot access User A's note
    res = client.get(f"/api/v1/notes/{note_id}", headers=auth_headers_b)
    assert res.status_code == status.HTTP_404_NOT_FOUND

    # User B cannot update User A's note
    res = client.patch(
        f"/api/v1/notes/{note_id}",
        json={"title": "Hacked Title"},
        headers=auth_headers_b,
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND

    # User B cannot delete User A's note
    res = client.delete(f"/api/v1/notes/{note_id}", headers=auth_headers_b)
    assert res.status_code == status.HTTP_404_NOT_FOUND

    # 4. Update Note as User A
    update_payload = {
        "title": "Refined Architecture Ideas",
        "is_pinned": False,
        "is_archived": True,
    }
    res = client.patch(f"/api/v1/notes/{note_id}", json=update_payload, headers=auth_headers_a)
    assert res.status_code == status.HTTP_200_OK
    updated_data = res.json()
    assert updated_data["title"] == "Refined Architecture Ideas"
    assert updated_data["is_pinned"] is False
    assert updated_data["is_archived"] is True

    # 5. Delete Note as User A
    res = client.delete(f"/api/v1/notes/{note_id}", headers=auth_headers_a)
    assert res.status_code == status.HTTP_200_OK

    res = client.get(f"/api/v1/notes/{note_id}", headers=auth_headers_a)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_note_search_and_filters(
    client: TestClient,
    user_a: User,
    auth_headers_a: dict,
    db_session,
):
    # Setup notes
    notes = [
        {"title": "Python Backend Best Practices", "content": "FastAPI and SQLAlchemy 2.0 tips", "is_pinned": True},
        {"title": "Frontend React Guide", "content": "Vite and Tailwind CSS patterns", "is_pinned": False},
        {"title": "Grocery Shopping List", "content": "Milk, eggs, and coffee beans", "is_pinned": False},
    ]
    for n in notes:
        res = client.post("/api/v1/notes", json=n, headers=auth_headers_a)
        assert res.status_code == status.HTTP_201_CREATED

    # Search for "FastAPI" in content
    res = client.get("/api/v1/notes?search=fastapi", headers=auth_headers_a)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Python Backend Best Practices"

    # Search for "React" in title
    res = client.get("/api/v1/notes?search=react", headers=auth_headers_a)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Frontend React Guide"

    # Filter by pinned
    res = client.get("/api/v1/notes?is_pinned=true", headers=auth_headers_a)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Python Backend Best Practices"


def test_note_associations_category_project_task_and_tags(
    client: TestClient,
    user_a: User,
    user_b: User,
    auth_headers_a: dict,
    auth_headers_b: dict,
    db_session,
):
    # Create category, project, task, and tag for User A
    cat = Category(user_id=user_a.id, name="Development", name_normalized="development", color="#10B981")
    proj = Project(user_id=user_a.id, name="Project Alpha")
    task = Task(user_id=user_a.id, title="Implement Notes Backend")
    tag1 = Tag(user_id=user_a.id, name="backend", name_normalized="backend")
    tag2 = Tag(user_id=user_a.id, name="v1", name_normalized="v1")

    db_session.add_all([cat, proj, task, tag1, tag2])
    db_session.commit()

    # Create note linked to all associations
    payload = {
        "title": "Development Sprint Note",
        "content": "Sprint notes and decisions",
        "category_id": str(cat.id),
        "project_id": str(proj.id),
        "task_id": str(task.id),
        "tag_ids": [str(tag1.id), str(tag2.id)],
    }
    res = client.post("/api/v1/notes", json=payload, headers=auth_headers_a)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["category"]["id"] == str(cat.id)
    assert data["project"]["id"] == str(proj.id)
    assert data["task"]["id"] == str(task.id)
    assert len(data["tags"]) == 2

    # Attempt cross-user association: User B tries to associate User A's project
    invalid_payload = {
        "title": "Malicious Note",
        "content": "Trying to link user 1 project",
        "project_id": str(proj.id),
    }
    res = client.post("/api/v1/notes", json=invalid_payload, headers=auth_headers_b)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_validation_rejects_empty_title(
    client: TestClient,
    user_a: User,
    auth_headers_a: dict,
):
    res = client.post("/api/v1/notes", json={"title": "   ", "content": "Valid content"}, headers=auth_headers_a)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
