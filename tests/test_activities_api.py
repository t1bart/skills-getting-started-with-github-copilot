from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_get_activities_returns_activity_details(client):
    # Arrange
    expected_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    response_activities = response.json()
    assert "Chess Club" in response_activities
    assert expected_fields <= response_activities["Chess Club"].keys()


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "aaa-signup@example.test"
    participants = activities[activity_name]["participants"]
    participants[:] = [participant for participant in participants if participant != email]

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert participants.count(email) == 1


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "aaa-duplicate@example.test"
    participants = activities[activity_name]["participants"]
    participants[:] = [participant for participant in participants if participant != email]
    participants.append(email)

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert participants.count(email) == 1


def test_signup_for_unknown_activity_returns_not_found(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": "aaa-unknown@example.test"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "aaa-remove@example.test"
    participants = activities[activity_name]["participants"]
    participants[:] = [participant for participant in participants if participant != email]
    participants.append(email)

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in participants


def test_remove_from_unknown_activity_returns_not_found(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": "aaa-unknown@example.test"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_unregistered_participant_returns_not_found(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "aaa-not-registered@example.test"
    participants = activities[activity_name]["participants"]
    participants[:] = [participant for participant in participants if participant != email]

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert email not in participants