import argparse

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

    args = parser.parse_args()

    token = args.token
    secret_name = args.secret_name
    new_secret_value = args.new_secret_value

    for repo in get_repos(token):
        repo_name = repo["full_name"]
        if check_repo_for_secret(repo_name, token, secret_name):
            public_key_info = get_public_key(repo_name, token)
            if public_key_info:
                encrypted_value = encrypt_secret(
                    public_key_info["key"],
                    new_secret_value,
                )
                if update_secret(
                    repo_name,
                    secret_name,
                    encrypted_value,
                    public_key_info["key_id"],
                    token,
                ):
                    print(f"Updated secret in {repo_name}")
                else:
                    print(f"Failed to update secret in {repo_name}")


if __name__ == "__main__":
    main()
