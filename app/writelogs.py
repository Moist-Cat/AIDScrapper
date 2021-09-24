import os
from datetime import datetime
import traceback

from aids.app.settings import BASE_DIR, DEACTIVATE_LOG


# default is linux console.
ERROR_FILE =  BASE_DIR / 'client.error' # '/dev/stdout'
LOG_FILE = '/dev/stdout' #BASE_DIR / 'app/client.log'


init_str = '---------------INIT---------------\n'

def make_log_message(level, extra_msg):
    return f'{str(datetime.today())} [{level}] {extra_msg}'

def log(lvl, msg):
    """
    Logs a message in whatever file is the current default.
    """
#    if DEACTIVATE_LOG:
#       return
    try:
        if os.stat(LOG_FILE).st_size > 5000000:
            os.system(f'mv {LOG_FILE} {BASE_DIR / "old_logs"}')
            with open(LOG_FILE, 'w'): pass
    except TypeError:
        # console
        pass
    if lvl == 'init':
        msg = init_str + msg

    try:
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(make_log_message(lvl, msg) + '\n')
    except OSError:
        pass

def log_error(lvl, msg):
    """
    Logs an error in whatever file is the current default.
    """
    if DEACTIVATE_LOG:
       return
    # bigger than 1 mb
    try:
        if os.stat(ERROR_FILE).st_size > 5000000:
            os.system(f'mv {ERROR_FILE} {BASE_DIR / "old_errors"}')
#            with open(ERROR_FILE, 'w'): pass
    except TypeError:
        # console
        pass
    with open(ERROR_FILE, 'a') as error_file:
        error_file.write(make_log_message(lvl, msg) + '\n')
