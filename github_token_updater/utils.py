import base64
import re
from typing import Optional

import nacl.encoding
import requests
from nacl.public import PublicKey, SealedBox

DEFAULT_TIMEOUT = 60


def fetch_paginated_results(
    session: requests.Session,
    url: str,
    token: str,
    timeout: int,
) -> list[dict]:
    """Fetch results from a paginated GitHub API endpoint."""
    results = []
    while url:
        response = session.get(
            url,
            headers={"Authorization": f"token {token}"},
            timeout=timeout,
        )
        if response.status_code == 200:
            results.extend(response.json())
            link_header = response.headers.get("Link", None)
            if link_header:
                # Extract the next URL correctly without the angle brackets
                next_links = [
                    link.split(";")[0].strip(" <>")
                    for link in link_header.split(",")
                    if 'rel="next"' in link
                ]
                url = next_links[0] if next_links else ""
            else:
                break
        else:
            break
    return results


def get_user_repos(
    session: requests.Session,
    token: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict]:
    """Fetch all repositories owned by the user."""
    return fetch_paginated_results(
        session,
        "https://api.github.com/user/repos",
        token,
        timeout,
    )


def get_user_orgs(
    session: requests.Session,
    token: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict]:
    """Fetch all organizations the user is part of."""
    return fetch_paginated_results(
        session,
        "https://api.github.com/user/orgs",
        token,
        timeout,
    )


def get_org_repos(
    session: requests.Session,
    token: str,
    org: dict,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict]:
    """Fetch all repositories for a given organization."""
    org_name = org.get("login")
    return fetch_paginated_results(
        session,
        f"https://api.github.com/orgs/{org_name}/repos",
        token,
        timeout,
    )


def get_repos(
    session: requests.Session,
    token: str,
    orgs: bool = False,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict]:
    """Fetch all repositories (user and organizations) accessible with the given token."""
    repos = get_user_repos(session, token, timeout)
    if orgs:
        _orgs = get_user_orgs(session, token, timeout)
        for org in _orgs:
            repos.extend(get_org_repos(session, token, org, timeout))
    return repos


def check_repo_for_secret(
    session: requests.Session,
    repo_name: str,
    token: str,
    secret_key: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> bool:
    """Check if the given repository uses the specified secret in its workflows."""
    headers = {"Authorization": f"token {token}"}
    workflows_url = (
        f"https://api.github.com/repos/{repo_name}/contents/.github/workflows"
    )
    response = session.get(workflows_url, headers=headers, timeout=timeout)
    yaml_pattern = re.compile(r".*\.ya?ml", re.IGNORECASE)
    if response.status_code == 200:
        for file in response.json():
            if file["type"] == "file" and yaml_pattern.match(file["name"]):
                file_content = session.get(
                    file["download_url"],
                    headers=headers,
                    timeout=timeout,
                ).text
                if secret_key in file_content:
                    return True
    return False


def get_public_key(
    session: requests.Session,
    repo: str,
    token: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> Optional[dict]:
    """Retrieve the public key for a repository."""
    url = f"https://api.github.com/repos/{repo}/actions/secrets/public-key"
    headers = {"Authorization": f"token {token}"}
    response = session.get(url, headers=headers, timeout=timeout)
    return response.json() if response.status_code == 200 else None


def encrypt_secret(public_key: str, secret_value: str) -> str:
    """Encrypt the secret using the repository's public key."""
    pk = PublicKey(public_key.encode("utf-8"), encoder=nacl.encoding.Base64Encoder)
    sealed_box = SealedBox(pk)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def update_secret(
    session: requests.Session,
    repo: str,
    secret_name: str,
    encrypted_value: str,
    public_key_id: str,
    token: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> bool:
    """Update the secret in the specified repository."""
    url = f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}"
    headers = {"Authorization": f"token {token}"}
    data = {"encrypted_value": encrypted_value, "key_id": public_key_id}
    response = session.put(url, headers=headers, json=data, timeout=timeout)
    return response.status_code in [201, 204]
