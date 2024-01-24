# github_token_updater

This repo contains a tool for updating a secret across multiple repositories.


## Requirements

* `PyNaCl`
* `requests`
  * `pip install PyNaCl requests`


## Installation

```bash
git clone https://github.com/joshuasundance-swca/github_token_updater.git
cd github_token_updater
pip install .
```


## Usage

### See Help
```bash
github_token_updater --help
usage: github_token_updater [-h] --token TOKEN --secret_name SECRET_NAME --new_secret_value NEW_SECRET_VALUE [--orgs]

Update a secret across multiple repositories.

options:
  -h, --help            show this help message and exit
  --token TOKEN         GitHub token
  --secret_name SECRET_NAME
                        Secret name
  --new_secret_value NEW_SECRET_VALUE
                        New secret value
  --orgs                Include organization repositories
```

## Testing

1. Install pytest using `pip install pytest` or `pip install .[dev]`
2. Create a file called `tests/config.json`:
```json
{
    "token": "your_token",
    "repo_name": "your_repo_name",
    "secret_name": "your_secret_name",
    "new_secret_value": "your_new_secret_value",
    "public_key": "public_key_here"
}
```
3. Run `pytest`:
```bash
python -m pytest
```
