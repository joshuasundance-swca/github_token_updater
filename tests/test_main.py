import json
from unittest.mock import patch, Mock

import pytest
import requests

import github_token_updater


# Fixture to load test data from a configuration file
@pytest.fixture(scope="module")
def test_data():
    with open("tests/config.json") as file:
        data = json.load(file)
    return data


def test_get_repos(test_data):
    token = test_data["token"]
    repo_name = test_data["repo_name"]

    with patch("github_token_updater.utils.requests.Session.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"full_name": repo_name}]
        with requests.Session() as session:
            session.headers.update({"Authorization": f"token {token}"})
            repos = github_token_updater.utils.get_repos(session)
        assert len(repos) == 1
        assert repos[0]["full_name"] == repo_name


def test_check_repo_for_secret(test_data):
    repo_name = test_data["repo_name"]
    token = test_data["token"]
    secret_name = test_data["secret_name"]

    with patch("github_token_updater.utils.requests.Session.get") as mock_get:
        mock_get.side_effect = [
            Mock(
                status_code=200,
                json=Mock(
                    return_value=[
                        {
                            "type": "file",
                            "name": "test_workflow.yml",
                            "download_url": "url",
                        },
                    ],
                ),
            ),
            Mock(status_code=200, text=f"uses {secret_name}"),
        ]

        with requests.Session() as session:
            session.headers.update({"Authorization": f"token {token}"})
            result = github_token_updater.utils.check_repo_for_secret(
                session,
                repo_name,
                secret_name,
            )
        assert result


def test_get_public_key(test_data):
    repo_name = test_data["repo_name"]
    token = test_data["token"]

    with patch("github_token_updater.utils.requests.Session.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "key": "public_key",
            "key_id": "key_id",
        }

        with requests.Session() as session:
            session.headers.update({"Authorization": f"token {token}"})
            key_info = github_token_updater.utils.get_public_key(
                session,
                repo_name,
            )
        assert key_info is not None
        assert "key" in key_info
        assert "key_id" in key_info


def test_encrypt_secret(test_data):
    public_key = test_data["public_key"]
    new_secret_value = test_data["new_secret_value"]

    encrypted = github_token_updater.utils.encrypt_secret(public_key, new_secret_value)
    assert encrypted is not None


def test_update_secret(test_data):
    repo_name = test_data["repo_name"]
    secret_name = test_data["secret_name"]
    token = test_data["token"]

    with patch("github_token_updater.utils.requests.Session.put") as mock_put:
        mock_put.return_value.status_code = 204
        with requests.Session() as session:
            session.headers.update({"Authorization": f"token {token}"})
            result = github_token_updater.utils.update_secret(
                session,
                repo_name,
                secret_name,
                "encrypted_value",
                "key_id",
            )
        assert result


# You can add more tests as needed
