import base64
from typing import Optional

import nacl.encoding
import requests
from nacl.public import PublicKey, SealedBox


DEFAULT_TIMEOUT = 60


def get_repos(token: str, timeout: int = DEFAULT_TIMEOUT) -> list[dict]:
    """Fetch all repositories accessible with the given token."""
    headers = {"Authorization": f"token {token}"}
    response = requests.get(
        "https://api.github.com/user/repos",
        headers=headers,
        timeout=timeout,
    )
    if response.status_code == 200:
        return response.json()
    else:
        return []


def check_repo_for_secret(
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
    response = requests.get(workflows_url, headers=headers, timeout=timeout)
    if response.status_code == 200:
        for file in response.json():
            if file["type"] == "file" and file["name"].endswith(".yml"):
                file_content = requests.get(
                    file["download_url"],
                    headers=headers,
                    timeout=timeout,
                ).text
                if secret_key in file_content:
                    return True
    return False


def get_public_key(
    repo: str,
    token: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> Optional[dict]:
    """Retrieve the public key for a repository."""
    url = f"https://api.github.com/repos/{repo}/actions/secrets/public-key"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers, timeout=timeout)
    return response.json() if response.status_code == 200 else None


def encrypt_secret(public_key: str, secret_value: str) -> str:
    """Encrypt the secret using the repository's public key."""
    pk = PublicKey(public_key.encode("utf-8"), encoder=nacl.encoding.Base64Encoder)
    sealed_box = SealedBox(pk)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def update_secret(
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
    response = requests.put(url, headers=headers, json=data, timeout=timeout)
    return response.status_code in [201, 204]
