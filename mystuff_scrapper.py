import json
import requests
import getpass

class AIDStuffGetter(object):
    """
    Based on ScripAnon stuff getter script.
    """
    def __init__(self):
        self.url = 'https://api.aidungeon.io/graphql'

        self.stories_query = {
            "variables": {
                "input": {
                    "searchTerm": "",
                    "saved": False,
                    "trash": False,
                    "contentType": "adventure",
                    "sortOrder": "createdAt",
                    "offset": 0
                }
            },
            "query": """
        query ($input: SearchInput) {
            user {
                search(input: $input) {
                    ...ContentListSearchable
                }
            }
        }

        fragment ContentListSearchable on Searchable {
            ...ContentCardSearchable
        }

        fragment ContentCardSearchable on Searchable {
            id
            publicId
            title
            description
            createdAt
            updatedAt

            ... on Adventure {
                type
                score
                memory
                authorsNote
                worldInfo
                score

                actions {
                    ...ActionSubscriptionAction
                }

                undoneWindow {
                    ...ActionSubscriptionAction
                }
            }
        }

        fragment ActionSubscriptionAction on Action {
            id
            text
            type
            createdAt
        }
        """.replace('\t', '')
        }

        self.ccs = """
        fragment ContentCardSearchable on Scenario {
            id
            publicId
            title
            description
            tags
            createdAt
            updatedAt
            memory
            authorsNote
            mode
            prompt
            quests
            worldInfo
            gameCode
            options {
                publicId
                title
                createdAt
            }
        }
        """

        self.scenarios_query = {
            "variables": {
                "input": {
                    "searchTerm": "",
                    "saved": False,
                    "trash": False,
                    "contentType": "scenario",
                    "sortOrder": "createdAt",
                    "offset": 0
                }
            },
            "query": ("""
        query ($input: SearchInput) {
            user {
                id
                search(input: $input) {
                    ...ContentCardSearchable
                }
            }
        }
        """ + self.ccs).replace('\t', '')
        }

        self.subscen_query = {
            "variables": {
                "publicId": ""
            },
            "query": ("""
        query ($publicId: String) {
            scenario(publicId: $publicId) {
                ...ContentCardSearchable
            }
        }
        """ + self.ccs).replace('\t', '')
        }

        # requests settings
        self.session = requests.Session()
        
        key = self.get_login_token()

        self.session.headers.update({'content-type': 'application/json',
                                    'x-access-token': key})

        self.out = {"stories": [], "scenarios": []}
        self.subscen = []

        self.discarded_stories = 0

    def get_stories(self, name="", min_act=0):
        """
        Gets a story based on a search term(name) 
        discarding any with less than the given actions(min_act)
        """
        while True:
            self.stories_query['variables']['input']['searchTerm'] = name

            print('Getting a page of stories...')

            res = None

            try:
                res = self.session.post(self.url, data=json.dumps(self.stories_query)).json()
            except requests.exceptions.ConnectionError or requests.HTTPError as e:
                print(e)
                print(e.read())
            result = res['data']['user']['search']
            if 'data' in res and 'user' in res['data'] and 'search' in res['data']['user']:
                if len(result) > 0:
                    for story in result:
                        if len(story['actions']) > int(min_act):
                            self.out['stories'].append(story)
                        else:
                            self.discarded_stories+=1
                    print('Got %d stories so far' % len(self.out['stories']))
                    self.stories_query['variables']['input']['offset'] = len(self.out['stories']) + self.discarded_stories
                else:
                    print('Looks like there\'s no more.')
                    # return discarded stories to 0, since we are done
                    self.discarded_stories = 0
                    break
            else:
                print('There was no data...')
                print(res)
                break


    def get_scenarios(self, name=""):
        while True:
            self.scenarios_query['variables']['input']['searchTerm'] = name
            print('Getting a page of scenarios...')

            res = None

            try:
                res = self.session.post(self.url, data=json.dumps(self.scenarios_query)).json()
            except requests.exceptions.ConnectionError or requests.HTTPError as e:
                print(e)
                print(e.read())
            result = res['data']['user']['search']
            if 'data' in res:
                if len(result) > 0:
                    self.out['scenarios'] += result
                    for scenario in result:
                        if 'options' in scenario and type(scenario['options']) is list:
                            for option in scenario['options']:
                                self.get_subscenario(option['publicId'])
                                
                    print('Got %d scenarios so far' % len(self.out['scenarios']))
                    self.scenarios_query['variables']['input']['offset'] = len(self.out['scenarios']) - self.discarded_stories
                else:
                    print('Looks like there\'s no more.')
                    break
            else:
                print('There was no data...')
                print(res)
                break

    def get_subscenario(self, pubid):
        self.discarded_stories+=1
        print('Getting subscenario %s...' % pubid)

        self.subscen_query['variables']['publicId'] = pubid
        res = None

        try:
            res = self.session.post(self.url, data=json.dumps(self.subscen_query)).json()
        except requests.exceptions.ConnectionError or requests.HTTPError as e:
            print(e)
            print(e.read())
        if 'data' in res and 'scenario' in res['data']:
            res['data']['scenario']['isOption'] = True
            self.out['scenarios'].append(res['data']['scenario'])
            if 'options' in res['data']['scenario'] and type(res['data']['scenario']['options']) is list:
                for option in res['data']['scenario']['options']:
                    self.get_subscenario(option['publicId'])
        else:
            print('There was no data...')
            print(res)

    def get_login_token(self):
        while True:
            loginpayload = {
                "variables": {
                    "identifier": "",
                    "email": "",
                    "password": ""
                },
                "query": """
            mutation ($identifier: String, $email: String, $password: String, $anonymousId: String) {
                login(identifier: $identifier, email: $email, password: $password, anonymousId: $anonymousId) {
                    accessToken
                }
            }
            """
            }

            loginpayload['variables']['identifier'] = loginpayload['variables']['email'] = input('Your username or e-mail: ')
            loginpayload['variables']['password'] = getpass.getpass('Your password: ')
            try:
                payload = self.session.post(self.url, data=json.dumps(loginpayload)).json()
                if 'errors' in payload:
                    print('Couldn\'t log in.')
                    for error in payload['errors']:
                        print(error['message'])
                        return ''
                elif 'data' in payload:
                    return payload['data']['login']['accessToken']
                else:
                    print('no data?!')
            except requests.exceptions.ConnectionError or requests.HTTPError as e:
                print(e)
if __name__ == '__main__':
    a = AIDStuffGetter()
    a.get_scenarios()
    with open('stories.json', 'w') as outfile:
        json.dump(a.out, outfile)