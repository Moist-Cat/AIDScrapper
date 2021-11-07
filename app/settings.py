from pathlib import Path
import json
import warnings

class ImproperlyConfigured(Exception):
    pass

DEACTIVATE_LOG = 0

# notice that '' is a catch-all. This does not 
# include Untitled scenarios, though.
DEFAULT_TITLE = ''
DEFAULT_MIN_ACT = 10

# base path
# could be changed to cwd() to use this module from console after
# a pip install.
BASE_DIR = Path(__file__).resolve().parent.parent

WARNINGS = 1

# secrets
try:
    with open(BASE_DIR / 'app/secrets.json') as file:
        secrets = json.load(file)
except FileNotFoundError:
    if WARNINGS:
        warnings.warn('File with credentials was not found.')

def get_secret(setting):
    try:
        return secrets[setting]
    except (NameError, KeyError) as exc:
        raise ImproperlyConfigured(
            f'Setting {setting} was not found in your secrets.json file.'
        ) from exc

# requests settings
headers = {
            'User-Agent':'Mozilla/5.0 (X11; Fedora; Linux x86_64) ' \
                         'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                         'Chrome/90.0.4430.93 Safari/537.36',
            'Referer': 'https://play.aidungeon.io/',
            'Origin': 'https://play.aidungeon.io',
            'Host': 'api.aidungeon.io',
            'DNT': '1',
            'Accept-Language': 'en-US,en;q=0.9',
            'content-type': 'application/json'
}
