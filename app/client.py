from weakref import ref
import json
import getpass
from typing import Sequence, List, Dict
import time
import traceback
import random
import re
import requests
try:
    import bs4
except ImportError:
    bs4 = None
try:
    import stem
    from aids.app.obfuscate import get_tor_session, renew_connection
except:
    stem = None

from aids.app.models import Story, Scenario
from aids.app.writelogs import log_error, log
from aids.app import settings, writelogs, schemes

# this import must go after settings bacause we might need them
# to use our "fake-headers"
try:
    from fake_headers import Headers
except ImportError:
    class Headers:
        def generate(self):
            return re.sub(settings.headers, 'Chrome/%d.', f'Chrome/{random.randint(60,90)}.')

def check_errors(request):
    def inner_func(cls, method, url, **kwargs):
        request_success = False
        while not request_success:
            try:
                start = time.time()
                log('debug', f'Trying to {method} data from {url}...')
                response = request(cls, method, url, **kwargs)
                time_elapsed = time.time() - start
                log(
                    'debug',
                    f'The response from the server after {time_elapsed:.2f} seconds '\
                    f'was {len(response.text)} characters big. URL: {response.url}'
                )
                response.raise_for_status()
            except (
                    requests.exceptions.ConnectionError, requests.exceptions.SSLError
            ):
                with open(writelogs.ERROR_FILE, 'a') as error:
                    traceback.print_exc(file=error)

                log('log', 'Something went wrong. Retrying...')
                log_error(
                    'fatal',
                    f'Server URL: {url}), failed while trying to connect.'
                )
            except requests.exceptions.HTTPError:
                try:
                    errors = response.json()['errors']
                except json.decoder.JSONDecodeError:
                    errors = 'No errors'
                raw_response = response.content[:20] if len(response.content) > 50 else response.content
                try:
                    payload = kwargs['data']
                except KeyError:
                    payload = 'none'
                error_message = (
                    'crit',
                    f'Server URL: {response.url}, ' \
                    f'failed with status code ({response.status_code}). ' \
                    f'Errors: {errors}. ' \
                    f'Raw response: {raw_response}' \
                    f'Request payload: {payload}'
                )
                log_error(*error_message)
                raise
            else:
                request_success = True
            time.sleep(3)
        return response
    return inner_func

class Session(requests.Session):
    """
    Overrriden version of requests.Session that checks for errors
    after completing the request.
    """

    @check_errors
    def request(self, method, url, **kwargs):
        return super().request(method, url, **kwargs)

class BaseClient:
    """
    Base client from where all other clients must inherit.
    """
    def __init__(self):
        self.url = None
        self.session = ref(Session())
        self.headers = ref(Headers())

        settings.headers.update(self.headers.generate())

        self.session.headers.update(settings.headers)
        self._initial_logging()

    def __del__(self):
        self.session.close()

    def _initial_logging(self):
        log('init', f'{self.__class__.__name__} successfully initialized.')

    def quit(self):
        """
        Kill the client.
        """
        self.session.close()

    def renew(self):
        """
        Use Tor to fake our IP address. Note that couldfare is going to be a
        PITA so this method is pretty useless as it is.
        """
        if not stem:
            raise ImportError('You need the stem library to use this method')
        try:
            renew_connection()
        except stem.SocketError:
            log_error('crit', 'Socket Error: '\
                'The Tor service is not up. Unable to continue.'
            )
        self.session = get_tor_session(self.session)

    def login(self, credentials: dict):
        """
        Login into the site using a dict credentials.
        """
        credentials = credentials or {}
        return NotImplemented

    def logout(self):
        """
        Clean up the session to \"log-out\".
        """
        self.session.headers = settings.headers
        self.session.cookies.clear()
        log('log', 'logged out')

class AIDScrapper(BaseClient):
    """
    AID Client to make API calls via requests.
    """
    adventures = ref(Story())
    prompts = ref(Scenario())

    def __init__(self):
        super().__init__()

        self.url = 'https://api.aidungeon.io/graphql'

        # Get all settings
        self.stories_query = schemes.stories_query
        self.create_scen_payload = schemes.create_scen_payload
        self.update_scen_payload = schemes.update_scen_payload
        self.make_WI_payload = schemes.make_WI_payload
        self.update_WI_payload = schemes.update_WI_payload
        self.scenarios_query = schemes.scenarios_query
        self.subscen_query = schemes.subscen_query
        self.aid_loginpayload = schemes.aid_loginpayload

        self.discarded_stories = 0

    def login(self, credentials = None):
        if not credentials:
            try:
                username = settings.get_secret('AID_USERNAME')
                password = settings.get_secret('AID_PASSWORD')
            except settings.ImproperlyConfigured:
                username = input('Your username or e-mail: ')
                password = getpass.getpass('Your password: ')
            finally:
                credentials = {
                    'username': username,
                    'password': password
                }

        key = self.get_login_token(credentials)

        self.session.headers.update({'x-access-token': key})
        log('log', 'logged in AID')

    def _get_object(self, query: dict):
        query['variables']['input']['searchTerm'] = self.adventures.title

        return self.session.post(
            self.url,
            data=json.dumps(
                query
            )
        ).json()['data']

    def retrieve_data(self):
        for scenario, story in (self.my_scenarios, self.my_stories):
            self.prompts.add(scenario)
            self.adventures.add(story)

    @property
    def my_stories(self) -> List[Dict]:
        stories: List[Dict] = []
        while True:
            self.stories_query['variables']['input']['searchTerm'] = self.adventures.title

            result = self._get_object(self.stories_query)['user']['search']

            if result:
                stories.extend(result)
                log('debug', f'Got {len(stories)} stories so far')
                self.stories_query['variables']['input']['offset'] = len(
                                                                         stories
                                                                     )
            else:
                log('log', 'All stories downloaded')
                break
        return stories

    @property
    def my_scenarios(self) -> List[Dict]:
        scenarios: List[Dict] = []
        while True:
            self.scenarios_query['variables']['input']['searchTerm'] = self.prompts.title

            result: List[Dict] = self._get_object(self.scenarios_query)['user']['search']

            if result:
                for scenario in result:
                    if isinstance(scenario['options'], Sequence):
                        scenarios.extend([
                            self.get_subscenarios(
                                option['publicId']
                            ) for option in scenario['options']
                        ])
                    scenarios.append(scenario)

                log('debug', f'Got {len(scenarios)} scenarios so far')
                self.scenarios_query['variables'] \
                                    ['input'] \
                                    ['offset'] = len(
                                                     scenarios
                                                 ) + self.discarded_stories
            else:
                log('log', 'All scenarios downloaded')
                self.discarded_stories = 0
                break
            return scenarios

    def get_subscenarios(self, pubid) -> List[Dict]:
        self.subscen_query['variables']['publicId'] = pubid

        subscen = self.session.post(
                self.url,
                data=json.dumps(self.subscen_query)
        ).json()['data']['scenario']
        subscen['isOption'] = True

        if isinstance(subscen['options'], Sequence):
            subscens = [
                self.get_subscenarios(
                    option['publicId']
                ) for option in subscen['options']
            ]
        subscens.extend(subscen)
        # do not count subscens for the offset
        self.discarded_stories -= len(subscens)

        return subscens

    def get_login_token(self, credentials: dict):
        self.aid_loginpayload['variables']['identifier'] = \
            self.aid_loginpayload['variables']['email'] = credentials['username']
        self.aid_loginpayload['variables']['password'] = credentials['password']
        res = self.session.post(
            self.url,
            data=json.dumps(
                self.aid_loginpayload
            )
        ).json()
        if 'data' in res:
            return res['data']['login']['accessToken']
        log_error('crit', 'There was no data')
        return None

    def upload_in_bulk(self, scenarios):
        for scenario in scenarios:
            res = self.session.post(self.url,
                data=json.dumps(self.create_scen_payload)
            ).json()['data']['createScenario']
            scenario.update({'publicId': res['publicId']})
            new_scenario = self.update_scen_payload.copy()

            clean_scenario = {k: v for k, v in scenario.items() if k in new_scenario['variables']['input']}
            new_scenario.update({'variables': {'input': clean_scenario}})
            self.session.post(
                self.url,
                data=json.dumps(new_scenario)
            )
            log('log', f'{scenario["title"]} successfully uploaded...')


class ClubClient(BaseClient):

    def __init__(self):
        super().__init__()

        self.url = 'https://prompts.aidg.club/'

        if not bs4:
            raise ImportError('You must pip install bs4 to use the club client.')

    def _post(self, obj_url, params):
        url = self.url + obj_url
        self.session.headers.update(dict(Referer=url))

        params['__RequestVerificationToken'] = self.get_secret_token(url)

        self.session.post(url, data=params)

    def reformat_tags(self, tags):
        nsfw = 'false'
        tags_str = ', '.join(tag for tag in tags)
        for tag in tags:
            if tag == 'nsfw':
                nsfw = 'true'
        return {'nsfw': nsfw, 'tags': tags_str}

    def get_secret_token(self, url):
        res = self.session.get(url)
        body = bs4.BeautifulSoup(res.text)
        hidden_token = body.find('input', {'name': '__RequestVerificationToken'})
        return hidden_token.attrs['value']

    def register(self, credentials=None):
        credentials = credentials or {}

        params = {
                 'ReturnUrl': '/',
                 'Honey': '',
                 'Username': '',
                 'Password': '',
                 'PasswordConfirm': ''
        }
        params.update(credentials)
        if not credentials:
            params.update(
                {
                'Username': input('Username: '),
                'Password': getpass.getpass('Password: '),
                'PasswordConfirm': getpass.getpass('Password(Again): ')
                }
            )

        self._post('user/register/', params)


    def login(self, credentials = None):
        credentials = credentials or {}

        params = {
                 'ReturnUrl': '',
                 'Honey': None,
                 'Username': '',
                 'Password': ''
        }
        params.update(credentials)
        if not credentials:
            params.update(
                {
                'Username': input('Username: '),
                'Password': getpass.getpass('Password: ')
                }
            )

        self._post('user/login/', params)

    def publish_scenario(self, title: str = ''):
        """
        Publish a scenario with a given name to the club.
        """

        # variables
        variables = ('?savedraft=true', '?confirm=false#')

        with open('scenario.json') as file:
            infile = json.load(file)

        for scenario in infile['scenarios']:
            if title in (scenario['title'], '*'):
                # prepare the request
                # prepare tags
                tags = self.reformat_tags(scenario['tags'])

                try:
                    quests = "\n".join(scenario['quests']['quest'])
                except KeyError:
                    quests = []

                params = {
                    "Honey": "",
                    "Command.ParentId": "",
                    "Command.Title": scenario['title'],
                    "Command.Description": scenario['description'],
                    "Command.promptsContent": scenario['prompts'],
                    "Command.promptsTags": tags['tags'],
                    "Command.Memory": scenario['memory'],
                    "Command.Quests": quests,
                    "Command.AuthorsNote": scenario['authorsNote'],
                    "Command.Nsfw": tags['nsfw'],
                    "ScriptZip": "",#file
                    "WorldInfoFile": "",#file
                }
                # prepare WI
                counter = 0
                try:
                    for wi_entry in scenario['worldInfo']:
                        params[f'Command.WorldInfos[{counter}].Keys'] = wi_entry['keys']
                        params[f'Command.WorldInfos[{counter}].Entry'] = wi_entry['entry']
                        counter+=1
                except KeyError:
                    pass

                res = self.session.post(variables[1], params)

                print(f'Your prompts number is {res.url.split("/")[-1]}')
                # I don't want to overload his servers...
                time.sleep(1)

class HoloClient(BaseClient):

    def __init__(self):
        super().__init__()

        self.base_url = 'https://writeholo.com/'
        self.url = self.base_url + 'api/'

        # Get all settings
        self.generate_holo = schemes.generate_holo

        self.curr_story_id = ''

    def login(self, credentials = None):
        # we need to get the cookies to interact with the API
        self.session.get(self.base_url)
        if credentials:
            #TODO
            raise NotImplementedError
        assert self.session.cookies

    def create_scenario(self):
        res = self.session.post(self.url + 'create_story')
        return res.json()['story_id']

    def generate_output(self, context: dict = None):
        if not self.curr_story_id:
            self.curr_story_id = self.create_scenario()

        self.generate_holo['story_id'] = self.curr_story_id
        self.generate_holo.update(context)
        payload = json.dumps(self.generate_holo)

        res = self.session.post(self.url + 'draw_completions', data=payload)
        return res.json()['outputs']
