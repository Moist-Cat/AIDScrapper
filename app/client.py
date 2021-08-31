import json
import requests
import getpass
from typing import Any, Type, Tuple, Dict
import time
from datetime import datetime
import traceback

from .models import Story, Scenario
from .obfuscate import get_tor_session, renew_connection
from .logging import log_error, log
from . import settings

def check_for_errors(request):
    def inner_func(cls, method, url, **kwargs):
        connection_success = False
        while not connection_success:
            try:
                response = request(cls, method, url, **kwargs)
            except requests.exceptions.ConnectionError:
                error_message = '\n-------------------ERROR-------------------------\n' \
                                f'{str(datetime.today())} [fatal] Server URL: {url}), ' \
                                f'failed while trying to connect.\n'
                with open(settings.error_file, 'a') as error:
                    traceback.print_exc(file=error)

                log('Something went wrong. Retrying...\n') 
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
            error_message = '-------------------ERROR-------------------------\n' \
                            f'{str(datetime.today())} [crit] Server URL: {response.url}, ' \
                            f'failed with status code ({response.status_code}). Errors: {errors}. ' \
                            f'Raw response: {response.content[:20] if len(response.content) > 50 else response.content}\n'
            log_error(error_message)
            raise
        return response
    return inner_func

# Overrriden version of requests.Session that checks for errors 
# after completing the request.
class Session(requests.Session):
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
    
    def __delete__(self):
        self.session.close()
    
    def _initial_logging(self):
        message = '--------------------INIT-----------------------\n' \
                  f'{str(datetime.today())}: {self.__class__.__name__} successfully initialized.\n'
        log(message)
    
    def quit(self):
        self.session.close()

    def renew(self):
        """
        Use Tor to fake our IP address. Note that couldfare is going to be a 
        PITA so this method is pretty useless as it is.
        """
        renew_connection()
        self.session = get_tor_session(self.session)

    def login(self):
        raise NotImplementedError('You must override this method in the subclass')
    
    def logout(self):
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
        for setting in settings.aid:
            setattr(self, setting, getattr(settings, setting))

        self.adventures = Story()
        self.prompts = Scenario()

        self.discarded_stories = 0

    def login(self, username='', password=''):
        if not username and password:
            try:
                username = settings.get_setting('AID_USERNAME')
                password = settings.get_setting('AID_PASSWORD')
            except settings.ImproperlyConfigured:
                username = input('Your username or e-mail: ')
                password = getpass.getpass('Your password: ')

        key = self.get_login_token(username, password)

        self.session.headers.update({'x-access-token': key})

    def _get_object(query):
        query['variables']['input']['searchTerm'] = self.adventures.title

        res = self.session.post(
            self.url,
            data=json.dumps(
                query
            )
        )

        res = res.json()

        result = res['data']
        return result

    def get_stories(self):
        while True:
            log('Getting a page of stories...\n')
            
            result = _get_object(self.stories_query)['user']['search']

            if result:
                for story in result:
                    try:
                        self.adventure.add(story)
                    except ValidationError:
                        self.discarded_stories += 1
                    log(f'Got {len(self.adventure)} stories so far\n')
                self.stories_query['variables']['input']['offset'] = len(self.adventure) + self.discarded_stories
            else:
                log('Looks like there\'s no more.\n')
                # return discarded stories to 0, since we are done
                self.discarded_stories = 0
                break

    def get_scenarios(self):
        while True:
            self.scenarios_query['variables']['input']['searchTerm'] = name
            log('Getting a page of scenarios...\n')
            
            result = _get_object(self.scenarios_query)['user']['search']

            if len(result):
                for scenario in result:
                    try:
                        self.prompts.add(scenario)
                    except ValidationError:
                        self.discarded_stories += 1
                    if type(scenario['options']) is list:
                        for option in scenario['options']:
                            self.get_subscenario(option['publicId'])
                            # don not count suscens
                            self.discarded_stories -= 1
                    log('Got {len(self.prompts)} scenarios so far\n')
                self.scenarios_query['variables'] \
                                    ['input'] \
                                    ['offset'] = len(
                                                     self.prompts
                                                 ) + self.discarded_stories
            else:
                log('Looks like there\'s no more.\n')
                self.discarded_stories = 0
                break

    def get_subscenario(self, pubid):        
        log(f'Getting subscenario {pubid}...\n')

        self.subscen_query['variables']['publicId'] = pubid
        
        result = self._get_object(self.subscen_query)['scenario']
        
        result['isOption'] = True
        try:
            self.prompts.add(result)
        except ValidationError:
            # With subscens there is no problem with offset
            pass
        if type(result['options']) is list:
            for option in result['options']:
                self.get_subscenario(option['publicId'])
                self.discarded_stories -= 1

    def get_login_token(self, user, password):
        self.aid_loginpayload['variables']['identifier'] = \
            self.aid_loginpayload['variables']['email'] = user
        self.aid_loginpayload['variables']['password'] = password
        res = self.session.post(
            self.url,
            data=json.dumps(
                self.aid_loginpayload
            )
        ).json()
        if 'data' in res:
            return res['data']['login']['accessToken']
        else:            
            log('no data?!\n')

    def upload_in_bulk(self, stories):
        for scenario in stories['scenarios']:
            res = self.session.post(self.url,
                data=json.dumps(
                    self.create_scen_payload
                 )
            )
            res = self.session.post(
                self.url,
                data=json.dumps(
                    self.update_scen_payload
                )
            )            
            log(f'{scenario["title"]} successfully uploaded...\n')


class ClubClient(BaseClient):

    def __init__(self):
        self.url = 'https://prompts.aidg.club/'

        # Get all settings
        for setting in settings.club:
            setattr(self, setting, getattr(settings, setting))

        # requests settings
        self.session = Session()
        self.session.headers.update(self.headers)

    def _post(self, obj_url, params):
        url = self.url + obj_url
        self.session.headers.update(dict(Referer=url))

        params['__RequestVerificationToken'] = self.get_secret_token(url)

        res = self.session.post(url, data=params)

    def _get_scenario_tags(self, tags):
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

    def register(self):
        params = {
                 'ReturnUrl': '',
                 'Honey': '',
                 'Username': input('Username: '),
                 'Password': getpass.getpass('Password: '),
                 'PasswordConfirm': getpass.getpass('Password(Again): ')
        }

        res = self._post('user/register/', params)


    def login(self):
        params = {
                 'ReturnUrl': '',
                 'Honey': '',
                 'Username': input('Username: '),
                 'Password': getpass.getpass('Password: ')
        }

        res = self._post('user/login/', params)

    def publish(self, title=''):
        """
        Publish a scenario with the given name to the club.
        """

        # variables
        variables = ('?savedraft=true', '?confirm=false#')

        with open('scenario.json') as file:
            infile = json.load(file)

        for scenario in infile['scenarios']:
            if scenario['title'] == title or title == '*':
                # prepare the request
                # prepare tags
                tags = self._get_scenario_tags(scenario['tags'])

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

                res = session.post(variables[1], params)

                print(f'Your prompts number is {res.url.split("/")[-1]}')
                # I don't want to overload his servers...
                time.sleep(1)

class HoloClient(BaseClient):

    def __init__(self):
        
        self.base_url = 'https://writeholo.com/'
        self.url = self.base_url + 'api/'

        # Get all settings
        for setting in settings.holo:
            setattr(self, setting, getattr(settings, setting))

        # requests settings
        self.session = Session()
        self.session.headers.update(settings.headers)
        
        self.curr_story_id = ''
            
    def login(self, credentials: dict = {}):
        # we need to get the cookies to interact with the API
        res = self.session.get(self.base_url)
        if credentials:
            # TODO
            raise NotImplementedError
        assert self.session.cookies

    def create_scenario(self):
        res = self.session.post(self.url + 'create_story')
        return res.json()['story_id']

    def generate_output(self, context: dict = {}):
        if not self.curr_story_id:
            self.curr_story_id = self.create_scenario()

        self.generate_holo['story_id'] = self.curr_story_id
        payload = json.dumps(self.generate_holo)

        res = self.session.post(self.url + 'draw_completions', data=payload)
        return res.json()['outputs']

if __name__ == '__main__':
    pass

    
