import argparse

import requests

from github_token_updater.utils import (
    get_repos,
    check_repo_for_secret,
    get_public_key,
    encrypt_secret,
    update_secret,
)


def main():
    """Main function to update a secret across multiple repositories."""
    parser = argparse.ArgumentParser(
        description="Update a secret across multiple repositories.",
    )
    parser.add_argument(
        "--token",
        type=str,
        required=True,
        help="GitHub token",
    )
    parser.add_argument(
        "--secret_name",
        type=str,
        required=True,
        help="Secret name",
    )
    parser.add_argument(
        "--new_secret_value",
        type=str,
        required=True,
        help="New secret value",
    )
    parser.add_argument(
        "--orgs",
        action="store_true",
        help="Include organization repositories",
    )

    args = parser.parse_args()

    token = args.token
    secret_name = args.secret_name
    new_secret_value = args.new_secret_value
    orgs = args.orgs
    headers = {"Authorization": f"token {token}"}

    with requests.Session() as session:
        session.headers.update(headers)
        secrets_updated = 0
        for repo in get_repos(session, orgs):
            repo_name = repo["full_name"]
            if check_repo_for_secret(session, repo_name, secret_name):
                public_key_info = get_public_key(session, repo_name)
                if public_key_info:
                    encrypted_value = encrypt_secret(
                        public_key_info["key"],
                        new_secret_value,
                    )
                    if update_secret(
                        session,
                        repo_name,
                        secret_name,
                        encrypted_value,
                        public_key_info["key_id"],
                    ):
                        print(f"Updated secret in {repo_name}")
                        secrets_updated += 1
                    else:
                        print(f"Failed to update secret in {repo_name}")
        print(f"Updated {secrets_updated} secrets")


if __name__ == "__main__":
    main()
