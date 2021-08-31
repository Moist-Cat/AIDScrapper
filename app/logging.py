# fileops
# default is linux console.
error_file = '/dev/stdout' #BASE_DIR / 'client.error'
log_file = '/dev/stdout' #BASE_DIR / 'client.log'

def log(msg):
    with open(log_file, 'a') as log:
        log.write(msg + '\n')
def log_error(msg):
    with open(error_file, 'a') as error:
        error.write(msg + '\n')
