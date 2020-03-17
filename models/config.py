import pathlib

NOAUTH_URL = "https://old.reddit.com"
AUTH_URL = "https://oauth.reddit.com"

ACCESS_TOKEN_ENDPOINT = "https://www.reddit.com/api/v1/access_token"

JSON_DIR = "saved-posts"
CONFIG_DIR = "instance/config.json"
SYNC_DIR = "sync"

dir_path = pathlib.Path(__file__).parent.absolute()

SAVES_JSON_PATH = str(dir_path / JSON_DIR)
CONFIG_PATH = str(dir_path / CONFIG_DIR)
SAVES_SYNC_PATH = str(dir_path / SYNC_DIR)
