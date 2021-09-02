import json
import getpass
from typing import Sequence
import time
from datetime import datetime
import traceback
import requests
try:
    import bs4
except ImportError:
    bs4 = None

from aids.app.models import Story, Scenario, ValidationError
from aids.app.obfuscate import get_tor_session, renew_connection
from aids.app.writelogs import log_error, log
from aids.app import settings, writelogs

def check_for_errors(request):
    def inner_func(cls, method, url, **kwargs):
        connection_success = False
        while not connection_success:
            try:
                response = request(cls, method, url, **kwargs)
            except requests.exceptions.ConnectionError:
                error_message = '-------------------ERROR-------------------------\n' \
                                f'{str(datetime.today())} [fatal] Server URL: {url}), ' \
                                f'failed while trying to connect.'
                with open(writelogs.ERROR_FILE, 'a') as error:
                    traceback.print_exc(file=error)

                log('Something went wrong. Retrying...')
                log_error(error_message)

                time.sleep(3)
            else:
                connection_success = True
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            try:
                errors = response.json()['errors']
            except json.decoder.JSONDecodeError:
                errors = 'No errors'
            raw_response = response.content[:20] if len(response.content) > 50 else response.content
            error_message = '-------------------ERROR-------------------------\n' \
                            f'{str(datetime.today())} [crit] Server URL: {response.url}, ' \
                            f'failed with status code ({response.status_code}). ' \
                            f'Errors: {errors}. ' \
                            f'Raw response: {raw_response}'
            log_error(error_message)
            raise
        return response
    return inner_func

class Session(requests.Session):
    """
    Overrriden version of requests.Session that checks for errors
    after completing the request.
    """

    @check_for_errors
    def request(self, method, url, **kwargs):
        return super().request(method, url, **kwargs)

class BaseClient:
    """
    Base client from where all other clients must inherit.
    """
    def __init__(self):
        self.url = None
        self.session = Session()
        self.session.headers.update(settings.headers)
        self._initial_logging()

    def __delete__(self, instance):
        self.session.close()

    def _initial_logging(self):
        message = '--------------------INIT-----------------------\n' \
                  f'{str(datetime.today())}: {self.__class__.__name__} successfully initialized.'
        log(message)

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
        renew_connection()
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

class AIDScrapper(BaseClient):
    """
    AID Client to make API calls via requests.
    """
    def __init__(self):
        super().__init__()

        self.url = 'https://api.aidungeon.io/graphql'

        # Get all settings
        self.stories_query = settings.stories_query
        self.scenarios_query = settings.scenarios_query
        self.subscen_query = settings.subscen_query
        self.aid_loginpayload = settings.aid_loginpayload

        self.adventures = Story()
        self.prompts = Scenario()

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

    def _get_object(self, query: dict):
        query['variables']['input']['searchTerm'] = self.adventures.title

        return self.session.post(
            self.url,
            data=json.dumps(
                query
            )
        ).json()['data']

    def get_stories(self):
        while True:
            self.stories_query['variables']['input']['searchTerm'] = self.adventures.title
            log('Getting a page of stories...')

            result = self._get_object(self.stories_query)['user']['search']

            if result:
                for story in result:
                    try:
                        self.adventures.add(story)
                    except ValidationError:
                        self.discarded_stories += 1
                    log(f'Got {len(self.adventures)} stories so far')
                self.stories_query['variables']['input']['offset'] = len(
                                                                         self.adventures
                                                                     ) + self.discarded_stories
            else:
                log('Looks like there\'s no more.')
                # return discarded stories to 0, since we are done
                self.discarded_stories = 0
                break

    def get_scenarios(self):
        while True:
            self.scenarios_query['variables']['input']['searchTerm'] = self.prompts.title
            log('Getting a page of scenarios...')

            result = self._get_object(self.scenarios_query)['user']['search']

            if len(result):
                for scenario in result:
                    try:
                        self.prompts.add(scenario)
                    except ValidationError:
                        self.discarded_stories += 1
                    if isinstance(scenario['options'], Sequence):
                        for option in scenario['options']:
                            self.get_subscenario(option['publicId'])
                            # don not count suscens
                            self.discarded_stories -= 1
                    log('Got {len(self.prompts)} scenarios so far')
                self.scenarios_query['variables'] \
                                    ['input'] \
                                    ['offset'] = len(
                                                     self.prompts
                                                 ) + self.discarded_stories
            else:
                log('Looks like there\'s no more.')
                self.discarded_stories = 0
                break

    def get_subscenario(self, pubid):
        log(f'Getting subscenario {pubid}...')

        self.subscen_query['variables']['publicId'] = pubid

        result = self._get_object(self.subscen_query)['scenario']

        result['isOption'] = True
        try:
            self.prompts.add(result)
        except ValidationError:
            # With subscens there is no problem with offset
            pass
        if isinstance(result['options'], Sequence):
            for option in result['options']:
                self.get_subscenario(option['publicId'])
                self.discarded_stories -= 1

    def get_login_token(self, credentials: dict):
        self.aid_loginpayload['variables']['identifier'] = \
            self.aid_loginpayload['variables']['email'] = credentials['user']
        self.aid_loginpayload['variables']['password'] = credentials['password']
        res = self.session.post(
            self.url,
            data=json.dumps(
                self.aid_loginpayload
            )
        ).json()
        if 'data' in res:
            return res['data']['login']['accessToken']
        log('no data?!')
        return None

    def upload_in_bulk(self, stories):
        #(XXX)
        # Mental note: Find where I put the payload.
        for scenario in stories['scenarios']:
            self.session.post(self.url,
                data=json.dumps(
                    self.create_scen_payload
                 )
            )
            self.session.post(
                self.url,
                data=json.dumps(
                    self.update_scen_payload
                )
            )
            log(f'{scenario["title"]} successfully uploaded...')


class ClubClient(BaseClient):

    def __init__(self):
        super().__init__()

        self.url = 'https://prompts.aidg.club/'

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
                 'ReturnUrl': '',
                 'Honey': '',
                 'Username': '',
                 'Password': '',
                 'PasswordConfirm': ''
        }.update(credentials)
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
                 'Honey': '',
                 'Username': '',
                 'Password': ''
        }.update(credentials)
        if not credentials:
            params.update(
                {
                'Username': input('Username: '),
                'Password': getpass.getpass('Password: ')
                }
            )

        self._post('user/login/', params)

    def publish(self, title=''):
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
        self.generate_holo = settings.generate_holo

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
