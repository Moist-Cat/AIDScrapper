import requests
from stem import Signal
from stem.control import Controller

proxies = {
    'http':  'socks5://127.0.0.1:9050',
    'https': 'socks5://127.0.0.1:9050'
}

def get_tor_session(session = None):
    if not session:
        session = requests.session()
    session.proxies = proxies
    return session

def renew_connection():
    with Controller.from_port(port = 9051) as controller:
        controller.authenticate(password="password")
        controller.signal(Signal.NEWNYM)
