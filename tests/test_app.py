import pytest
from fastapi.testclient import TestClient

from src import app as app_module


client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activity_participants():
    participants = {
        activity_name: activity["participants"].copy()
        for activity_name, activity in app_module.activities.items()
    }
    yield
    for activity_name, original_participants in participants.items():
        app_module.activities[activity_name]["participants"][:] = original_participants


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details():
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == app_module.activities


def test_signup_adds_participant():
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Soccer Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Soccer Club"}
    assert email in app_module.activities["Soccer Club"]["participants"]


def test_signup_returns_not_found_for_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant():
    email = "michael@mergington.edu"

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_unregister_removes_participant():
    email = "michael@mergington.edu"

    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Chess Club"
    }
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_unregister_returns_not_found_for_unknown_activity():
    response = client.delete(
        "/activities/Unknown Club/participants",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_not_found_for_unregistered_participant():
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
