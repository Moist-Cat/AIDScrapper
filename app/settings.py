from pathlib import Path
import json
import warnings

class ImproperlyConfigured(Exception):
    pass

# notice that '' is a catch-all. This does not 
# include Untitled scenarios, though.
DEFAULT_TITLE = ''
DEFAULT_MIN_ACT = 10

# base path
# could be changed to cwd() to use this module from console after
# a pip install.
BASE_DIR = Path(__file__).resolve().parent.parent

# validation warnings. Remember to set this to 0 in production if you 
# do not want hundreds of warnings overflowing your screen.
WARNINGS = 1

# secrets
try:
    with open(BASE_DIR / 'app/secrets.json') as file:
        secrets = json.load(file)
except FileNotFoundError:
    if WARNINGS:
        warnings.warn('File with credentials was not found.')

def get_secret(setting):
    try:
        return secrets[setting]
    except (NameError, KeyError) as exc:
        raise ImproperlyConfigured(
            f'Setting {setting} was not found in your secrets.json file.'
        ) from exc

# requests settings
headers = {
            'User-Agent':'Mozilla/5.0 (X11; Fedora; Linux x86_64) ' \
                         'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                         'Chrome/90.0.4430.93 Safari/537.36',
            'content-type': 'application/json'
}

# AID
stories_query = {
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

# Scenarios
CSS = """
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
}"""

scenarios_query = {
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
""" + CSS).replace('\t', '')}

subscen_query = {
            "variables": {
                "publicId": ""
            },
            "query": ("""
        query ($publicId: String) {
            scenario(publicId: $publicId) {
                ...ContentCardSearchable
            }
        }
""" + CSS).replace('\t', '')}

aid_loginpayload = {
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

create_scen_payload = {
                      "variables":{},
                      "query":"""mutation {
                              createScenario {
                                ...ScenarioEditScenario
                                __typename
                              }
                            }
                            fragment ScenarioEditScenario on Scenario {
                              id
                              publicId
                              allowComments
                              createdAt
                              deletedAt
                              description
                              memory
                              authorsNote
                              mode
                              musicTheme
                              nsfw
                              prompt
                              published
                              featured
                              safeMode
                              quests
                              tags
                              thirdPerson
                              title
                              updatedAt
                              options {
                                id
                                publicId
                                title
                                __typename
                              }
                              ...ContentOptionsSearchable
                              ...DeleteButtonSearchable
                              __typename
                            }
                            fragment ContentOptionsSearchable on Searchable {
                              id
                              publicId
                              published
                              isOwner
                              tags
                              title
                              userId
                              ... on Savable {
                                isSaved
                                __typename
                              }
                              ... on Adventure {
                                userJoined
                                __typename
                              }
                              __typename
                            }
                            fragment DeleteButtonSearchable on Searchable {
                              id
                              publicId
                              published
                              __typename
                            }
"""
}

update_scen_payload = {"variables":{"input":{"publicId":"","title":"","description":"sneed","prompt":"","memory":"","authorsNote":"","quests":[],"musicTheme":None,"tags":[],"nsfw":False,"featured":False,"safeMode":True,"thirdPerson":False,"mode":"creative","allowComments":True}},"query":"mutation ($input: ScenarioInput) {\n  updateScenario(input: $input) {\n    ...ScenarioEditScenario\n    __typename\n  }\n}\n\nfragment ScenarioEditScenario on Scenario {\n  id\n  publicId\n  allowComments\n  createdAt\n  deletedAt\n  description\n  memory\n  authorsNote\n  mode\n  musicTheme\n  nsfw\n  prompt\n  published\n  featured\n  safeMode\n  quests\n  tags\n  thirdPerson\n  title\n  updatedAt\n  options {\n    id\n    publicId\n    title\n    __typename\n  }\n  ...ContentOptionsSearchable\n  ...DeleteButtonSearchable\n  __typename\n}\n\nfragment ContentOptionsSearchable on Searchable {\n  id\n  publicId\n  published\n  isOwner\n  tags\n  title\n  userId\n  ... on Savable {\n    isSaved\n    __typename\n  }\n  ... on Adventure {\n    userJoined\n    __typename\n  }\n  __typename\n}\n\nfragment DeleteButtonSearchable on Searchable {\n  id\n  publicId\n  published\n  __typename\n}\n"}

update_WI_payload = {
    "variables": {
        "input": {
            "id": "",
            "type": "",
            "keys": "",
            "entry": "",
            "hidden": False,
            "generator": "Manual",
            "name": None,
            "description": None,
            "attributes": {
                "name": None,
                "description": None
            }
        }
    },
    "query": """
        mutation ($input: WorldInformationInput) {
          updateWorldInformation(input: $input) {
            id
            name
            description
            genre
            type
            __typename
    """
}

make_WI_payload = {
    "variables": {
      "input": {
        "contentPublicId": "",
        "contentType": "scenario",
        "keys": "",
        "entry": "",
        "type": "Custom",
        "generator": "Manual",
        "hidden": False,
        "isSelected": False
      }
    },
    "query": """
        mutation ($input: WorldInformationInput) {
          createWorldInfoContent(input: $input) {
            id
            __typename
    """
}

action_continue_payload = {
    'variables': {
        'input': {
            'publicId': '',
            'type': 'continue',
            'characterName': None
        }
    }, 'query':"""
            mutation ($input: ActionInput) {
              addAction(input: $input) {
                message
                time
                hasBannedWord
                returnedInput
                __typename
               }
           }
       """
}

get_aid_user_payload =  {"variables":{"username": ""},"query":"query ($username: String) {\n  user(username: $username) {\n    id\n    friends {\n      ...UserTitleUser\n      ...FriendButtonUser\n      __typename\n    }\n    followers {\n      ...UserTitleUser\n      ...FollowButtonUser\n      __typename\n    }\n    following {\n      ...UserTitleUser\n      ...FollowButtonUser\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment FollowButtonUser on User {\n  isCurrentUser\n  isFollowedByCurrentUser\n  __typename\n}\n\nfragment FriendButtonUser on User {\n  id\n  username\n  isCurrentUser\n  friendedCurrentUser\n  friendedByCurrentUser\n  __typename\n}\n\nfragment UserTitleUser on User {\n  id\n  username\n  icon\n  ...UserAvatarUser\n  __typename\n}\n\nfragment UserAvatarUser on User {\n  id\n  username\n  avatar\n  __typename\n}\n"}

# Holo
#https://www.writeholo.com/api/draw_completions
generate_holo = {
    "story_id":"",
    "model_name":"goodreads-2-5",
    "input":[{
        "label":"prefix",
        "base_content":"{\"source\":\"literotica\",\"identifier\":930290,\"category\":\"\",\"author\":\"RavenSun\",\"rating\":4.98,\"tags\":[],\"view_count\":101409,\"series_meta\":null,\"location\":0,\"length\":5000}\n"},
        {
        "cutoff_settings":{
            "ellipsis":True,
            "cutoff_direction":"left",
            "strategy":{
                "priority":4,
                "max_length":1500,
                "min_length":1024}
            },
            "label":"prompt",
            "base_content":""
        }
    ]
}
#https://www.writeholo.com/api/create_story
# Not required? OwO
"""
holo_create_story = {
    "story_title":"",
    "prompt":"{\"version\":6,\"title\":\"Title here\",\"content\":[{\"type\":\"paragraph\",\"children\":[{\"type\":\"text\",\"text\":\"Replace this with at least a few sentences before generating.\"}]}],\"memory\":\"\",\"authorsNote\":\"\",\"worldInfo\":[],\"snippets\":[],\"genMeta\":{\"dataset\":0,\"literotica\":{\"author\":\"\",\"category\":\"\",\"tags\":[],\"targetLength\":5000},\"goodreads\":{\"author\":\"\",\"pubDate\":2020,\"tags\":[],\"targetLength\":25000}},\"target_length\":25000,\"forkedFrom\":null}"
}
"""
