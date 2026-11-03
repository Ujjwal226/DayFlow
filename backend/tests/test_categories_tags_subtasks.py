import pytest
import uuid
from app.models.category import Category
from app.models.tag import Tag
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.core.security import create_access_token, hash_password


@pytest.fixture
def user_a(db_session):
    user = User(
        email="user_a_2b@example.com",
        display_name="User Alpha 2B",
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
        email="user_b_2b@example.com",
        display_name="User Beta 2B",
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


# ============================================================================
# CATEGORY TESTS
# ============================================================================

def test_category_crud_and_validation(client, auth_headers_a):
    # 1. Invalid color format -> 422
    res_bad_color = client.post(
        "/api/v1/categories",
        json={"name": "Work", "color": "blue"},
        headers=auth_headers_a,
    )
    assert res_bad_color.status_code == 422

    # 2. Empty name -> 422
    res_empty_name = client.post(
        "/api/v1/categories",
        json={"name": "   ", "color": "#10B981"},
        headers=auth_headers_a,
    )
    assert res_empty_name.status_code == 422

    # 3. Valid creation
    res_create = client.post(
        "/api/v1/categories",
        json={"name": "Work Projects", "color": "#10b981", "icon": "briefcase", "description": "Professional tasks"},
        headers=auth_headers_a,
    )
    assert res_create.status_code == 201
    cat = res_create.json()
    assert cat["name"] == "Work Projects"
    assert cat["color"] == "#10B981"
    assert cat["icon"] == "briefcase"
    cat_id = cat["id"]

    # 4. Duplicate name (case-insensitive) -> 409
    res_dup = client.post(
        "/api/v1/categories",
        json={"name": "work projects"},
        headers=auth_headers_a,
    )
    assert res_dup.status_code == 409

    # 5. List categories
    res_list = client.get("/api/v1/categories", headers=auth_headers_a)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

    # 6. Get category
    res_get = client.get(f"/api/v1/categories/{cat_id}", headers=auth_headers_a)
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Work Projects"

    # 7. Update category
    res_update = client.patch(
        f"/api/v1/categories/{cat_id}",
        json={"name": "Career", "color": "#3B82F6"},
        headers=auth_headers_a,
    )
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Career"
    assert res_update.json()["color"] == "#3B82F6"

    # 8. Delete category
    res_del = client.delete(f"/api/v1/categories/{cat_id}", headers=auth_headers_a)
    assert res_del.status_code == 200

    # 9. Get deleted category -> 404
    res_get_del = client.get(f"/api/v1/categories/{cat_id}", headers=auth_headers_a)
    assert res_get_del.status_code == 404


def test_category_deletion_preserves_tasks_as_uncategorized(client, auth_headers_a, db_session):
    # Create category
    res_cat = client.post("/api/v1/categories", json={"name": "Finances"}, headers=auth_headers_a)
    cat_id = res_cat.json()["id"]

    # Create task in this category
    res_task = client.post(
        "/api/v1/tasks",
        json={"title": "Review Monthly Budget", "category_id": cat_id},
        headers=auth_headers_a,
    )
    assert res_task.status_code == 201
    task_id = res_task.json()["id"]

    # Delete category
    res_del = client.delete(f"/api/v1/categories/{cat_id}", headers=auth_headers_a)
    assert res_del.status_code == 200

    # Verify task still exists and category is now None
    res_task_after = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers_a)
    assert res_task_after.status_code == 200
    assert res_task_after.json()["category_id"] is None
    assert res_task_after.json()["category"] is None


# ============================================================================
# TAG TESTS
# ============================================================================

def test_tag_crud_and_validation(client, auth_headers_a):
    # 1. Invalid color -> 422
    res_bad_color = client.post("/api/v1/tags", json={"name": "Urgent", "color": "#12"}, headers=auth_headers_a)
    assert res_bad_color.status_code == 422

    # 2. Empty name -> 422
    res_empty = client.post("/api/v1/tags", json={"name": "  "}, headers=auth_headers_a)
    assert res_empty.status_code == 422

    # 3. Create tag
    res_create = client.post(
        "/api/v1/tags",
        json={"name": "Dev", "color": "#0d9488"},
        headers=auth_headers_a,
    )
    assert res_create.status_code == 201
    tag_id = res_create.json()["id"]
    assert res_create.json()["name"] == "Dev"
    assert res_create.json()["color"] == "#0D9488"

    # 4. Duplicate tag (case-insensitive) -> 409
    res_dup = client.post("/api/v1/tags", json={"name": "dev"}, headers=auth_headers_a)
    assert res_dup.status_code == 409

    # 5. List tags
    res_list = client.get("/api/v1/tags", headers=auth_headers_a)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

    # 6. Update tag
    res_update = client.patch(
        f"/api/v1/tags/{tag_id}",
        json={"name": "Backend", "color": "#F59E0B"},
        headers=auth_headers_a,
    )
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Backend"

    # 7. Delete tag
    res_del = client.delete(f"/api/v1/tags/{tag_id}", headers=auth_headers_a)
    assert res_del.status_code == 200

    # 8. Deleted tag -> 404
    assert client.get(f"/api/v1/tags/{tag_id}", headers=auth_headers_a).status_code == 404


def test_task_tag_assignments_and_deletion_preserves_task(client, auth_headers_a):
    # Create two tags
    tag1_id = client.post("/api/v1/tags", json={"name": "Frontend"}, headers=auth_headers_a).json()["id"]
    tag2_id = client.post("/api/v1/tags", json={"name": "React"}, headers=auth_headers_a).json()["id"]

    # Create task with tags
    res_task = client.post(
        "/api/v1/tasks",
        json={"title": "Build Task Card", "tag_ids": [tag1_id, tag2_id]},
        headers=auth_headers_a,
    )
    assert res_task.status_code == 201
    task_id = res_task.json()["id"]
    assert len(res_task.json()["tags"]) == 2

    # Replace tags via PUT /tasks/{task_id}/tags
    res_put_tags = client.put(
        f"/api/v1/tasks/{task_id}/tags",
        json={"tag_ids": [tag1_id]},
        headers=auth_headers_a,
    )
    assert res_put_tags.status_code == 200
    assert len(res_put_tags.json()["tags"]) == 1
    assert res_put_tags.json()["tags"][0]["name"] == "Frontend"

    # Delete tag1
    res_del_tag = client.delete(f"/api/v1/tags/{tag1_id}", headers=auth_headers_a)
    assert res_del_tag.status_code == 200

    # Task still exists with 0 tags
    res_task_after = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers_a)
    assert res_task_after.status_code == 200
    assert len(res_task_after.json()["tags"]) == 0


# ============================================================================
# SUBTASK TESTS & PROGRESS CALCULATION
# ============================================================================

def test_subtask_lifecycle_and_progress_calculation(client, auth_headers_a):
    # 1. Create parent task
    res_parent = client.post(
        "/api/v1/tasks",
        json={"title": "Feature 2B Release"},
        headers=auth_headers_a,
    )
    parent_id = res_parent.json()["id"]
    assert res_parent.json()["progress"]["progress_percentage"] == 0.0

    # 2. Add 3 subtasks
    st1 = client.post(
        f"/api/v1/tasks/{parent_id}/subtasks",
        json={"title": "Implement Models", "status": "COMPLETED"},
        headers=auth_headers_a,
    ).json()

    st2 = client.post(
        f"/api/v1/tasks/{parent_id}/subtasks",
        json={"title": "Implement Services", "status": "IN_PROGRESS"},
        headers=auth_headers_a,
    ).json()

    st3 = client.post(
        f"/api/v1/tasks/{parent_id}/subtasks",
        json={"title": "Implement UI", "status": "TODO"},
        headers=auth_headers_a,
    ).json()

    # 3. Check parent task progress: 1 of 3 = 33.3%
    parent_data = client.get(f"/api/v1/tasks/{parent_id}", headers=auth_headers_a).json()
    progress = parent_data["progress"]
    assert progress["total_subtasks"] == 3
    assert progress["completed_subtasks"] == 1
    assert progress["remaining_subtasks"] == 2
    assert progress["progress_percentage"] == 33.3
    # Verify parent status remains independent (TODO)
    assert parent_data["status"] == "TODO"

    # 4. Update st2 to COMPLETED: 2 of 3 = 66.7%
    client.patch(
        f"/api/v1/subtasks/{st2['id']}",
        json={"status": "COMPLETED"},
        headers=auth_headers_a,
    )
    parent_data = client.get(f"/api/v1/tasks/{parent_id}", headers=auth_headers_a).json()
    assert parent_data["progress"]["completed_subtasks"] == 2
    assert parent_data["progress"]["progress_percentage"] == 66.7

    # 5. Complete st3: 3 of 3 = 100.0%
    client.patch(
        f"/api/v1/subtasks/{st3['id']}",
        json={"status": "COMPLETED"},
        headers=auth_headers_a,
    )
    parent_data = client.get(f"/api/v1/tasks/{parent_id}", headers=auth_headers_a).json()
    assert parent_data["progress"]["completed_subtasks"] == 3
    assert parent_data["progress"]["progress_percentage"] == 100.0
    # Parent status stays TODO
    assert parent_data["status"] == "TODO"

    # 6. Delete st1: 2 of 2 = 100.0%
    res_del_st = client.delete(f"/api/v1/subtasks/{st1['id']}", headers=auth_headers_a)
    assert res_del_st.status_code == 200
    parent_data = client.get(f"/api/v1/tasks/{parent_id}", headers=auth_headers_a).json()
    assert parent_data["progress"]["total_subtasks"] == 2
    assert parent_data["progress"]["completed_subtasks"] == 2

    # 7. Delete parent task: cascades to delete subtasks
    client.delete(f"/api/v1/tasks/{parent_id}", headers=auth_headers_a)
    assert client.get(f"/api/v1/subtasks/{st2['id']}", headers=auth_headers_a).status_code == 404
    assert client.get(f"/api/v1/subtasks/{st3['id']}", headers=auth_headers_a).status_code == 404


def test_subtask_single_nesting_rule(client, auth_headers_a):
    # 1. Create parent task
    parent_id = client.post(
        "/api/v1/tasks",
        json={"title": "Grandparent Task"},
        headers=auth_headers_a,
    ).json()["id"]

    # 2. Create subtask
    subtask_id = client.post(
        f"/api/v1/tasks/{parent_id}/subtasks",
        json={"title": "Child Subtask"},
        headers=auth_headers_a,
    ).json()["id"]

    # 3. Attempt to create subtask under subtask -> 422
    res_nested = client.post(
        f"/api/v1/tasks/{subtask_id}/subtasks",
        json={"title": "Grandchild Subtask Not Allowed"},
        headers=auth_headers_a,
    )
    assert res_nested.status_code == 422
    assert "Only one nesting level is permitted" in res_nested.json()["detail"]


# ============================================================================
# MULTI-USER ISOLATION TESTS
# ============================================================================

def test_multi_user_isolation_categories_tags_subtasks(client, auth_headers_a, auth_headers_b, user_b):
    # User B creates Category, Tag, Parent Task, and Subtask
    cat_b = client.post("/api/v1/categories", json={"name": "User B Category"}, headers=auth_headers_b).json()
    tag_b = client.post("/api/v1/tags", json={"name": "User B Tag"}, headers=auth_headers_b).json()
    task_b = client.post("/api/v1/tasks", json={"title": "User B Task"}, headers=auth_headers_b).json()
    subtask_b = client.post(
        f"/api/v1/tasks/{task_b['id']}/subtasks",
        json={"title": "User B Subtask"},
        headers=auth_headers_b,
    ).json()

    # User A tries to get, update, delete User B's category -> 404
    assert client.get(f"/api/v1/categories/{cat_b['id']}", headers=auth_headers_a).status_code == 404
    assert client.patch(f"/api/v1/categories/{cat_b['id']}", json={"name": "Hacked"}, headers=auth_headers_a).status_code == 404
    assert client.delete(f"/api/v1/categories/{cat_b['id']}", headers=auth_headers_a).status_code == 404
    assert client.get(f"/api/v1/categories/{cat_b['id']}/tasks", headers=auth_headers_a).status_code == 404

    # User A tries to get, update, delete User B's tag -> 404
    assert client.get(f"/api/v1/tags/{tag_b['id']}", headers=auth_headers_a).status_code == 404
    assert client.patch(f"/api/v1/tags/{tag_b['id']}", json={"name": "Hacked"}, headers=auth_headers_a).status_code == 404
    assert client.delete(f"/api/v1/tags/{tag_b['id']}", headers=auth_headers_a).status_code == 404

    # User A tries to get, update, delete User B's subtask -> 404
    assert client.get(f"/api/v1/subtasks/{subtask_b['id']}", headers=auth_headers_a).status_code == 404
    assert client.patch(f"/api/v1/subtasks/{subtask_b['id']}", json={"title": "Hacked"}, headers=auth_headers_a).status_code == 404
    assert client.delete(f"/api/v1/subtasks/{subtask_b['id']}", headers=auth_headers_a).status_code == 404

    # User A tries to create a subtask under User B's parent task -> 404
    res_st_cross = client.post(
        f"/api/v1/tasks/{task_b['id']}/subtasks",
        json={"title": "Cross User Subtask"},
        headers=auth_headers_a,
    )
    assert res_st_cross.status_code == 404

    # User A creates their own task
    task_a = client.post("/api/v1/tasks", json={"title": "User A Task"}, headers=auth_headers_a).json()

    # User A tries to assign User B's category to User A's task -> 404
    res_assign_cross_cat = client.patch(
        f"/api/v1/tasks/{task_a['id']}/category",
        json={"category_id": cat_b["id"]},
        headers=auth_headers_a,
    )
    assert res_assign_cross_cat.status_code == 404

    # User A tries to assign User B's tag to User A's task -> 404
    res_assign_cross_tag = client.put(
        f"/api/v1/tasks/{task_a['id']}/tags",
        json={"tag_ids": [tag_b["id"]]},
        headers=auth_headers_a,
    )
    assert res_assign_cross_tag.status_code == 404


# ============================================================================
# FILTERING BY CATEGORY AND TAG TESTS
# ============================================================================

def test_filtering_tasks_by_category_and_tags(client, auth_headers_a):
    # 1. Create categories and tags
    cat1 = client.post("/api/v1/categories", json={"name": "Work"}, headers=auth_headers_a).json()
    cat2 = client.post("/api/v1/categories", json={"name": "Personal"}, headers=auth_headers_a).json()

    tag1 = client.post("/api/v1/tags", json={"name": "Urgent"}, headers=auth_headers_a).json()
    tag2 = client.post("/api/v1/tags", json={"name": "Review"}, headers=auth_headers_a).json()

    # 2. Create tasks with combinations
    client.post(
        "/api/v1/tasks",
        json={"title": "Task 1", "category_id": cat1["id"], "tag_ids": [tag1["id"]]},
        headers=auth_headers_a,
    )
    client.post(
        "/api/v1/tasks",
        json={"title": "Task 2", "category_id": cat1["id"], "tag_ids": [tag2["id"]]},
        headers=auth_headers_a,
    )
    client.post(
        "/api/v1/tasks",
        json={"title": "Task 3", "category_id": cat2["id"], "tag_ids": [tag1["id"], tag2["id"]]},
        headers=auth_headers_a,
    )

    # 3. Filter by Category 1 -> Should return 2 tasks
    res_cat1 = client.get(f"/api/v1/tasks?category_id={cat1['id']}", headers=auth_headers_a)
    assert res_cat1.status_code == 200
    assert res_cat1.json()["total"] == 2

    # 4. Filter by Tag 1 -> Should return 2 tasks (Task 1 and Task 3)
    res_tag1 = client.get(f"/api/v1/tasks?tag_id={tag1['id']}", headers=auth_headers_a)
    assert res_tag1.status_code == 200
    assert res_tag1.json()["total"] == 2

    # 5. Filter by Category 2 AND Tag 2 -> Should return 1 task (Task 3)
    res_both = client.get(f"/api/v1/tasks?category_id={cat2['id']}&tag_id={tag2['id']}", headers=auth_headers_a)
    assert res_both.status_code == 200
    assert res_both.json()["total"] == 1
    assert res_both.json()["items"][0]["title"] == "Task 3"

    # 6. Verify Subtasks do not appear in top-level list
    task3_id = res_both.json()["items"][0]["id"]
    client.post(
        f"/api/v1/tasks/{task3_id}/subtasks",
        json={"title": "Subtask of Task 3"},
        headers=auth_headers_a,
    )
    res_all_top = client.get("/api/v1/tasks", headers=auth_headers_a)
    assert res_all_top.json()["total"] == 3


# ============================================================================
# AUDIT REGRESSION TESTS (Self-parent, whitespace, duplicate tags)
# ============================================================================

def test_whitespace_normalization_and_conflict(client, auth_headers_a):
    # Category with surrounding whitespace
    res_cat = client.post(
        "/api/v1/categories",
        json={"name": "   Deep Work   ", "color": "#10B981"},
        headers=auth_headers_a,
    )
    assert res_cat.status_code == 201
    assert res_cat.json()["name"] == "Deep Work"

    # Conflicting category with mixed casing and whitespace
    res_cat_conflict = client.post(
        "/api/v1/categories",
        json={"name": "  deep work  ", "color": "#3B82F6"},
        headers=auth_headers_a,
    )
    assert res_cat_conflict.status_code == 409

    # Tag with surrounding whitespace
    res_tag = client.post(
        "/api/v1/tags",
        json={"name": "  Refactor  ", "color": "#0D9488"},
        headers=auth_headers_a,
    )
    assert res_tag.status_code == 201
    assert res_tag.json()["name"] == "Refactor"

    # Conflicting tag with different casing
    res_tag_conflict = client.post(
        "/api/v1/tags",
        json={"name": "refactor"},
        headers=auth_headers_a,
    )
    assert res_tag_conflict.status_code == 409


def test_atomic_tag_replacement_and_duplicate_deduplication(client, auth_headers_a):
    tag1 = client.post("/api/v1/tags", json={"name": "Tag One"}, headers=auth_headers_a).json()
    tag2 = client.post("/api/v1/tags", json={"name": "Tag Two"}, headers=auth_headers_a).json()

    task = client.post("/api/v1/tasks", json={"title": "Atomic Tag Task"}, headers=auth_headers_a).json()

    # Pass duplicates in tag_ids list -> should deduplicate without failing
    res_dup = client.put(
        f"/api/v1/tasks/{task['id']}/tags",
        json={"tag_ids": [tag1["id"], tag1["id"], tag2["id"]]},
        headers=auth_headers_a,
    )
    assert res_dup.status_code == 200
    assert len(res_dup.json()["tags"]) == 2

    # Clear all tags atomically with empty list
    res_clear = client.put(
        f"/api/v1/tasks/{task['id']}/tags",
        json={"tag_ids": []},
        headers=auth_headers_a,
    )
    assert res_clear.status_code == 200
    assert len(res_clear.json()["tags"]) == 0


