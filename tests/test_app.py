from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client():
    # Arrange: keep a clean copy of the in-memory activity store for each test.
    original_activities = deepcopy(app_module.activities)
    app_module.activities.clear()
    app_module.activities.update(deepcopy(original_activities))

    with TestClient(app_module.app) as test_client:
        yield test_client

    # Arrange cleanup: restore the original app state after the request.
    app_module.activities.clear()
    app_module.activities.update(deepcopy(original_activities))


def test_root_redirects_to_static_index(client):
    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_catalog(client):
    # Arrange
    expected_keys = {"Chess Club", "Programming Class", "Gym Class"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert expected_keys.issubset(payload.keys())
    assert payload["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_for_activity_adds_student(client):
    # Arrange
    email = "newstudent@mergington.edu"

    # Act
    response = client.post("/activities/Basketball Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Basketball Club"}
    assert email in app_module.activities["Basketball Club"]["participants"]


def test_signup_for_unknown_activity_returns_404(client):
    # Arrange
    email = "newstudent@mergington.edu"

    # Act
    response = client.post("/activities/Unknown Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_for_duplicate_email_returns_409(client):
    # Arrange
    email = "michael@mergington.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 409
    assert response.json() == {"detail": "Student is already signed up"}


def test_unregister_from_activity_removes_student(client):
    # Arrange
    email = "michael@mergington.edu"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_unregister_from_unknown_activity_returns_404(client):
    # Arrange
    email = "newstudent@mergington.edu"

    # Act
    response = client.delete("/activities/Unknown Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_missing_student_returns_404(client):
    # Arrange
    email = "notregistered@mergington.edu"

    # Act
    response = client.delete("/activities/Basketball Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up"}
