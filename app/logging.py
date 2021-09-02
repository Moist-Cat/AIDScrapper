#from .settings import BASE_DIR

"""
Quick and dirty logger for aids.
"""

# default is linux console.
ERROR_FILE =  '/dev/stdout' #BASE_DIR / 'app/client.error'
LOG_FILE = '/dev/stdout' #BASE_DIR / 'app/client.log'

def log(msg):
    """
    Logs a message in whatever file is the current default.
    """
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(msg + '\n')

def log_error(msg):
    """
    Logs an error in whatever file is the current default.
    """
    with open(ERROR_FILE, 'a') as error_file:
        error_file.write(msg + '\n')
