import os
from pathlib import Path
import json
import sys
import warnings
try:
    import fake_headers
except ImportError:
    fake_headers = None

class ImproperlyConfigured(Exception):
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = True

## Models settings
# notice that '' is a catch-all. This does not 
# include Untitled scenarios due the data validation
# performed to the models.
DEFAULT_TITLE = ''
DEFAULT_MIN_ACT = 10

try:
    os.mkdir(BASE_DIR / 'backups')
except FileExistsError:
    pass

# Secrets
secrets_form = {
    "TOR_PASSWORD": "",
    "AID_TOKEN": "",
    "AID_USERNAME": "",
    "AID_PASSWORD": ""
}
try:
    with open(BASE_DIR / 'app/secrets.json') as file:
        secrets = json.load(file)
except FileNotFoundError:
    warnings.warn(
        'File with credentials was not found. You have to register to use certain features.'
    )
except json.decoder.JSONDecodeError:
    # First time, create the file
    with open(BASE_DIR / 'app/secrets.json', 'w') as file:
        file.write(json.dumps(secrets_form))

def get_secret(setting):
    """Fetch senstive information from the .json file."""
    try:
        return secrets[setting]
    except (NameError, KeyError) as exc:
        raise ImproperlyConfigured(
            f'Setting {setting} was not found in your secrets.json file.'
        ) from exc

# requests settings
def get_request_headers():
    """
    To get a brand new User-Agent every time we call the function if fake-headers is
    available.
    """
    headers = {
            'User-Agent':'Mozilla/5.0 (X11; Fedora; Linux x86_64) ' \
                         'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                         'Chrome/90.0.4430.93 Safari/537.36',
            'DNT': '1',
            'Accept-Language': 'en-US,en;q=0.9',
            'content-type': 'application/json'
    }
    if fake_headers:
        new_headers = fake_headers.Headers().generate()
        headers.update(new_headers)

    return headers

# logger settings
LOGGERS = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stderr,
            "formatter": "basic"
        },
        "audit_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": 5000000,
            "backupCount": 1,
            "filename": BASE_DIR / "app/client.error",
            "encoding": "utf-8",
            "formatter": "basic"
        }
   },
   "formatters": {
       "basic": {
           "style": "{",
           "format": "{asctime:s} [{levelname:s}] -- {name:s}: {message:s}"
       }
   },
   "loggers": {
       "user_info": {
           "handlers": ("console",),
           "level": "INFO" if DEBUG is False else "DEBUG"
       },
       "audit": {
           "handlers": ("audit_file",),
           "level": "ERROR"
       }
   }
}
