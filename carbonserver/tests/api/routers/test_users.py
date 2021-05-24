from unittest import mock

import pytest
from container import ServerContainer
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.api.routers import users
from carbonserver.database.sql_models import User as ModelUser

USER_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
USER_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"

USER = {
    "user_id": USER_ID,
    "name": "Gontran Bonheur",
    "email": "xyz@email.com",
    "hashed_password": "pwd",
    "is_active": True,
}

USER_2 = {
    "user_id": USER_ID_2,
    "name": "Jonnhy Monnay",
    "email": "1234+1@email.fr",
    "hashed_password": "password",
    "is_active": True,
}

USER_TO_CREATE = {
    "name": "Gontran Bonheur",
    "email": "xyz@email.com",
    "password": "pwd",
}

USER_WITH_BAD_EMAIL = {
    "name": "Gontran Bonheur",
    "email": "xyz",
    "password": "pwd",
}


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[users])
    app = FastAPI()
    app.container = container
    app.include_router(users.router)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_create_user(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_user = USER
    repository_mock.create_user.return_value = ModelUser(**expected_user)

    container_mock = mock.Mock(spec=ServerContainer)
    container_mock.db.return_value = True
    with custom_test_server.container.user_repository.override(repository_mock):
        with custom_test_server.container.db.override(container_mock):
            response = client.post("/users/", json=USER_TO_CREATE)
            actual_user = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert actual_user == expected_user


def test_create_user_with_bad_email_fails_at_http_layer(client):
    response = client.post("/users/", json=USER_WITH_BAD_EMAIL)
    actual_response = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert actual_response["detail"][0]["type"] == "value_error.email"


def test_list_users_list_all_existing_users_with_200(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_user = USER
    expected_user_2 = USER_2
    expected_user_list = [USER, USER_2]
    repository_mock.list_users.return_value = [
        ModelUser(**expected_user),
        ModelUser(**expected_user_2),
    ]

    # container_mock = mock.Mock(spec=ServerContainer)
    # container_mock.db.return_value = True
    with custom_test_server.container.user_repository.override(repository_mock):
        # with custom_test_server.container.db.override(container_mock):
        response = client.get("/users/")
        actual_user_list = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_user_list == expected_user_list


def test_get_user_by_id_returns_correct_user_with_correct_id(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_user = USER
    repository_mock.get_user_by_id.return_value = ModelUser(**expected_user)

    container_mock = mock.Mock(spec=ServerContainer)
    container_mock.db.return_value = True
    with custom_test_server.container.user_repository.override(repository_mock):
        with custom_test_server.container.db.override(container_mock):
            response = client.get("/users/get_user_by_id/", params={"user_id": USER_ID})
            actual_user = response.json()

    assert actual_user == expected_user