import warnings
import json
import getpass
from typing import Sequence, List, Dict, Any
import time
import requests

try:
    import bs4
except ImportError:
    bs4 = None
try:
    import stem
    from aids.app.obfuscate import get_tor_session, renew_connection
except ImportError:
    stem = None

from aids.app.models import Story, Scenario, ValidationError
from aids.app.writelogs import logged
from aids.app import settings, schemes

def check_errors(request):
    def inner_func(cls, method, url, **kwargs):
        request_success = False
        while not request_success:
            try:
                response = request(cls, method, url, **kwargs)
                response.raise_for_status()
            except (
                    requests.exceptions.ConnectionError, requests.exceptions.SSLError
            ) as exc:
                cls.logger_err.exception(exc)

                cls.logger.info('Network unstable. Retrying...')
                cls.logger_err.error(
                    'Server URL: %s, failed while trying to connect.',
                    url
                )
            except requests.exceptions.HTTPError as exc:
                try:
                    errors = response.json()['errors']
                except json.decoder.JSONDecodeError:
                    errors = 'No errors'
                except KeyError:
                    # 
                    errors = response.json()
                raw_response = response.content[:50] if len(response.content) > 50 else response.content
                try:
                    payload = kwargs['data']
                except KeyError:
                    payload = 'none'
                error_message = f"""
                    Server URL: {response.url}, 
                    failed with status code ({response.status_code}).
                    Errors: {errors}. 
                    Raw response: {raw_response} 
                    Request payload: {payload}
                """
                cls.logger.error(error_message)
                raise requests.exceptions.HTTPError from exc
            else:
                request_success = True
            #time.sleep(3)
        return response
    return inner_func

@logged
class Session(requests.Session):
    """
    Overrriden version of requests.Session that checks for errors
    after completing the request.
    """

    @check_errors
    def request(self, method, url, **kwargs):
        return super().request(method, url, **kwargs)

@logged
class BaseClient:
    """
    Base client from where all other clients must inherit.
    """
    def __init__(self):
        self.url = None
        self.session = Session()

        self.session.headers.update(settings.get_request_headers())

        self.logger.info('%s successfully initialized.', self.__class__.__name__)

    def __del__(self):
        self.session.close()

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
            self.logger_err.error('Socket Error: '\
                'The Tor service is not up. Unable to continue.'
            )
            # (XXX) Shouldn't I re-raise the exception?
        self.session = get_tor_session(self.session)

    def login(self, credentials: dict):
        """
        Login into the site using a dict credentials.
        """
        raise NotImplementedError

    def logout(self):
        """
        Clean up the session to \"log-out\".
        """
        self.session.headers = settings.get_request_headers()
        self.session.cookies.clear()
        self.logger.info('Logged out.')

class AIDScrapper(BaseClient):
    """
    AID Client to make API calls via requests.
    """
    adventures = Story()
    prompts = Scenario()

    def __init__(self):
        super().__init__()

        self.url = 'https://api.aidungeon.io/graphql'

        # Get all settings
        self.stories_query = schemes.stories_query
        self.story_query = schemes.story_query
        self.create_scen_payload = schemes.create_scen_payload
        self.update_scen_payload = schemes.update_scen_payload
        self.make_WI_payload = schemes.make_WI_payload
        self.update_WI_payload = schemes.update_WI_payload
        self.scenarios_query = schemes.scenarios_query
        self.scenario_query = schemes.scenario_query
        self.wi_query = schemes.wi_query
        self.aid_loginpayload = schemes.aid_loginpayload

        self.offset = 0

    def login(self, credentials = None):
        if not credentials:
            try:
                self.logger.info("Trying to log-in via file...")

                username = settings.get_secret('AID_USERNAME')
                password = settings.get_secret('AID_PASSWORD')
            except settings.ImproperlyConfigured:
                self.logger.info("File is not configured... logging in via console.")

                warnings.warn("Registering a user is the preferred way of logging in.")
                username = input('Your username or e-mail: ').strip()
                password = getpass.getpass('Your password: ')
            credentials = {
                'username': username,
                'password': password
            }
        else:
            self.logger.info("Credentials were passed to the function directly...")

        key = self.get_login_token(credentials)

        self.session.headers.update({'x-access-token': key})
        self.logger.info('User \"%s\" sucessfully logged into AID', credentials['username'])

    def _get_story_content(self, story_id: str) -> Dict[str, Any]:
        self.story_query.update({"variables": {"publicId": story_id}})
        return self.session.post(self.url, json=self.story_query).json()["data"]["adventure"]
    
    def _get_scenario_content(self, scenario_id: str) -> Dict[str, Any]:
        self.scenario_query.update({"variables": {"publicId": scenario_id}})
        wi = self._get_wi(scenario_id)
        scenario = self.session.post(self.url, json=self.scenario_query).json()["data"]["scenario"]
        scenario.update({"worldInfo": wi})
        return scenario

    def _get_wi(self, scenario_id: str) -> Dict[str, Any]:
        self.wi_query["variables"].update({"contentPublicId": scenario_id})
        return self.session.post(self.url, json=self.wi_query).json()["data"]["worldInfoType"]

    def _get_object(self, query: dict) -> Dict[str, Any]:
        query['variables']['input']['searchTerm'] = self.adventures.title or self.prompts.title

        return self.session.post(
            self.url,
            data=json.dumps(
                query
            )
        ).json()['data']

    def get_stories(self) -> List[Dict[str, Any]]:
        while True:
            result = self._get_object(self.stories_query)['user']['search']

            if any(result):
                for story in result:
                    s = self._get_story_content(story["publicId"])
                    self.offset += 1
                    if not self.adventures.title:
                        # To optimize queries -- stop when we are under n actions
                        try:
                            self.adventures._add(s)
                        except ValidationError as exc:
                            self.logger.debug(exc)
                            # actions are under the limit. Abort.
                            return
                        
                    else:
                        self.adventures.add(s)
                    self.logger.info("Loaded story: \"%s\"", story["title"])
                self.logger.debug('Got %d stories so far', len(self.adventures))
                self.stories_query['variables']['input']['offset'] = self.offset
            else:
                self.logger.info('All stories downloaded')
                break

    def get_scenarios(self) -> List[Dict[str, Any]]:
        while True:
            result: List[Dict[str, Any]] = self._get_object(self.scenarios_query)['user']['search']

            if any(result):
                for scenario in result:
                    self.add_all_scenarios(scenario["publicId"])
                self.logger.debug('Got %d scenarios so far', len(self.prompts))
                self.scenarios_query['variables'] \
                                    ['input'] \
                                    ['offset'] = self.offset
            else:
                self.logger.info('All scenarios downloaded')
                self.offset = 0
                break

    def add_all_scenarios(self, pubid, isOption=False) -> List[Dict[str, Any]]:
        """Adds all scenarios and their children to memory"""

        scenario: Dict[str, Any] = self._get_scenario_content(pubid)
        scenario["isOption"] = isOption

        if "options" in scenario and isinstance(scenario["options"], Sequence):
            for option in scenario["options"]:
                self.add_all_scenarios(
                    option["publicId"], True
                )        
        self.prompts.add(scenario)
        self.offset += 1 if not isOption else 0
        self.logger.info("Added %s to memory", scenario['title'])

    def get_login_token(self, credentials: Dict[str, Any]):
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
            try:
                token = res['data']['login']['accessToken']
            except KeyError as exc:
                raise (KeyError("There was no token")) from exc

            assert token

            return token
        self.logger_err.error('There was no data')
        return None

    def upload_in_bulk(self, scenarios: Dict[str, Any]):
        for key in scenarios:
            scenario = scenarios[key]
            
            assert isinstance(scenario, dict)

            res = self.session.post(self.url,
                data=json.dumps(self.create_scen_payload)
            ).json()['data']['createScenario']
            scenario.update({'publicId': res['publicId']})
            new_scenario = self.update_scen_payload.copy()


            # (XXX) This process have been delegated to the
            # data models. Maybe wait for me to make a proper "Scenario" object 
            # to refactor it?
            clean_scenario = {k: v for k, v in scenario.items() if k in new_scenario['variables']['input']}

            new_scenario.update({'variables': {'input': clean_scenario}})
            self.session.post(
                self.url,
                data=json.dumps(new_scenario)
            )
            self.logger.info('%s successfully uploaded...', scenario["title"])


class ClubClient(BaseClient):

    def __init__(self):
        super().__init__()
        warnings.warn(
            "The Club Client is should be out of service due to "\
            "changes in aidg.club.com back-end."
        )

        self.url = 'https://prompts.aidg.club/'

        if not bs4:
            raise ImportError('You must install the BeautifulSoup library to use the Club client.')

    def _post(self, obj_url, params):
        url = self.url + obj_url
        self.session.headers.update(dict(Referer=url))

        params['__RequestVerificationToken'] = self.get_secret_token(url)

        self.session.post(url, data=params)

    @staticmethod
    def reformat_tags(tags):
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
            # TODO
            raise NotImplementedError
        assert self.session.cookies

    def create_scenario(self):
        res = self.session.post(self.url + 'create_story')
        return res.json()['story_id']

    def generate_output(self, context: Dict[str, Any] = None):
        if not self.curr_story_id:
            self.curr_story_id = self.create_scenario()

        self.generate_holo['story_id'] = self.curr_story_id
        self.generate_holo.update(context)
        payload = json.dumps(self.generate_holo)

        res = self.session.post(self.url + 'draw_completions', data=payload)
        return res.json()['outputs']
