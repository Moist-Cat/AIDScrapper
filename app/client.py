import json
import requests
import getpass
from typing import Any, Type, Tuple, Dict
import time

from .models import Story, Scenario
from .obfuscate import get_tor_session, renew_connection
from . import settings

class AIDScrapper:
    """
    AID Client to make API calls via requests.
    """
    def __init__(self):
        
        self.url = 'https://api.aidungeon.io/graphql'

        # Get all settings
        for setting in settings.aid:
            setattr(self, setting, getattr(settings, setting))

        # requests settings
        self.session = requests.Session()
        self.session.headers.update(settings.headers)

        self.adventures = Story
        self.prompts = Scenario

        self.discarded_stories = 0

    def __delete__(self):
        self.session.close()
    
    def quit(self):
        self.session.close()

    def logout(self):
        self.session.headers.update({'x-access-token':''})

    def log_in(self, username, password):
        try:
            with open('token.txt') as file:
                key = file.read()
        
        except:
            if not username and password:
                username = input('Your username or e-mail: ')
                password = getpass.getpass('Your password: ')

            key = self.get_login_token(username, password)

        self.session.headers.update({'x-access-token': key})

    def get_object(query):
        query['variables']['input']['searchTerm'] = self.adventures.title

        try:
            res = self.session.post(
                self.url,
                data=json.dumps(
                    query
                )
            )
            if res.status_code > '399' or res.json()['errors']:
                raise AssertionError(f'Error: {[res.status_code, res.json()["errors"]]}')
            res = res.json()
        except requests.exceptions.ConnectionError or requests.HTTPError as e:
            print(e)
            print(e.read())

        result = res['data']
        return result

    def get_stories(self):
        while True:
            print('Getting a page of stories...')
            
            result = get_object(self.stories_query)['user']['search']

            if result:
                for story in result:
                    try:
                        self.adventure.add(story)
                    except ValidationError:
                        self.discarded_stories += 1
                print(f'Got {len(self.adventure)} stories so far')
                self.stories_query['variables']['input']['offset'] = len(self.adventure) + self.discarded_stories
            else:
                print('Looks like there\'s no more.')
                # return discarded stories to 0, since we are done
                self.discarded_stories = 0
                break

    def get_scenarios(self):
        while True:
            self.scenarios_query['variables']['input']['searchTerm'] = name
            print('Getting a page of scenarios...')
            
            result = get_object(self.scenarios_query)['user']['search']

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
                            
                print('Got {len(self.prompts)} scenarios so far')
                self.scenarios_query['variables'] \
                                    ['input'] \
                                    ['offset'] = len(
                                                     self.prompts
                                                 ) + self.discarded_stories
            else:
                print('Looks like there\'s no more.')
                self.discarded_stories = 0
                break

    def get_subscenario(self, pubid):
        print(f'Getting subscenario {pubid}...')

        self.subscen_query['variables']['publicId'] = pubid
        
        result = self.get_object(self.subscen_query)['scenario']
        
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
        while True:
            self.aid_loginpayload['variables']['identifier'] = \
                self.aid_loginpayload['variables']['email'] = user
            self.aid_loginpayload['variables']['password'] = password
            try:
                res = self.session.post(
                    self.url,
                    data=json.dumps(
                        self.aid_loginpayload
                    )
                ).json()
                if 'errors' in res:
                    print('Couldn\'t log in.')
                    for error in payload['errors']:
                        print(error['message'])
                        return ''
                elif 'data' in res:
                    return res['data']['login']['accessToken']
                else:
                    print('no data?!')
            except requests.exceptions.ConnectionError or requests.HTTPError as e:
                print(e, '\nRetrying...')
                time.sleep(3)

    def upload_in_bulk(self, stories):
        for scenario in stories['scenarios']:
            res = self.session.post(self.url,
                data=json.dumps(
                    self.create_scen_payload
                 )
            )
            if 'errors' in res:
                raise Exception(res, res.json)
            res = self.session.post(
                self.url,
                data=json.dumps(
                    self.update_scen_payload
                )
            )
            print(f'{scenario["title"]} successfully uploaded..')


class ClubClient:

    def __init__(self):
        self.url = 'https://promptss.aidg.club/'

        # Get all settings
        for setting in settings.club:
            setattr(self, setting, getattr(settings, setting))

        # requests settings
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _post(self, obj_url, params):
        url = self.url + obj_url
        self.session.headers.update(dict(Referer=url))

        params['__RequestVerificationToken'] = self.get_secret_token(url)

        res = self.session.post(url, data=params)
        if res.status_code >= 200:
            print('Successfully registered')
        else:
           print('Uh-oh...', res.text, res.status_code)

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

    def make_club_account(self):
        params = {
                 'ReturnUrl': '',
                 'Honey': '',
                 'Username': input('Username: '),
                 'Password': getpass.getpass('Password: '),
                 'PasswordConfirm': getpass.getpass('Password(Again): ')
        }

        res = self._post('user/register/', params)


    def login_into_the_club(self):
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
        print('Already have a club account?')
        print('\n[1] Register')
        print('\n[2] Log-in')

        selection = input('>')
        if selection == '1':
            self.make_club_account()
        elif selection == '2':
            self.login_into_the_club()
        else:
            print('Invalid selection...')
            return
        # variables
        variables = ('?savedraft=true', '?confirm=false#')


        with open('stories.json') as file:
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
                    "ScriptZip": "",#filename
                    "WorldInfoFile": "",#filename
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

class HoloClient():

    def __init__(self):
        
        self.base_url = 'https://writeholo.com/'
        self.url = self.base_url + 'api/'
        self.session = requests.Session()


        # Get all settings
        for setting in settings.holo:
            setattr(self, setting, getattr(settings, setting))

        # requests settings
        self.session = requests.Session()
        self.session.headers.update(settings.headers)
        
        self.curr_story_id = ''

    def __delete__(self):
        self.session.close()
    
    def quit(self):
        self.session.close()

    def renew(self):
        while True:
            renew_connection()
            self.session = get_tor_session(self.session)
            try:
                self.curr_story_id = self.create_scenario()
            except json.decoder.JSONDecodeError:
                time.sleep(1)
                print('Fail...')
                continue
            else:
                break
            
    def login(self, credentials: dict = {}):
        # we need to get the cookies to interact with the API
        res = self.session.get(self.base_url)
        print(res)
        if credentials:
            # TODO
            raise NotImplementedError
        assert self.session.cookies

    def logout(self):
        self.session.cookies.clear()

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

    
