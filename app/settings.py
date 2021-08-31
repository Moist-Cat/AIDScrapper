from pathlib import Path
import json
import warnings

class ImproperlyConfigured(Exception):
    pass

__all__ = [
    'stories_query',
    'ccs',
    'scenarios_query',
    'subscen_query',
    'headers',
    'aid_loginpayload',
    'generate_holo',
]

aid = [
    'stories_query',
    'scenarios_query',
    'subscen_query',
    'headers',
    'aid_loginpayload'
]

club = ['headers']

holo = ['headers', 'generate_holo']

# notice that '' is a catch-all. This does not 
# include Untitled scenarios, though.
default_title = ''
default_min_action = 10

# base path
BASE_DIR = Path(__file__).resolve().parent.parent

# validation warnings
WARNINGS = 1

# secrets
try:
    with open(BASE_DIR / 'app/secrets.json') as file: secrets = json.load(file)
except FileNotFoundError:
    if WARNINGS:
        warnings.warn('File with credentials was not found.')

def get_secret(secret):
    try:
        return secrets[secret]
    except (NameError, KeyError):
        raise ImproperlyConfigured(f'Setting {setting} was not found in your secrets.json file.')

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
ccs = """
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
""" + ccs).replace('\t', '')}

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
""" + ccs).replace('\t', '')}

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
        "keys": "",
        "entry": "",
        "type": "worldDescription",
        "generator": "Manual",
        "hidden": False,
        "isSelected": True,
        "contentPublicId": "",
        "contentType": "scenario"
      }
    },
    "query": """
        mutation ($input: WorldInformationInput) {
          createWorldInfoContent(input: $input) {
            id
            __typename
    """
}

# Holo
"https://www.writeholo.com/api/draw_completions"
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
"https://www.writeholo.com/api/create_story"
# Not required? OwO
"""
holo_create_story = {
	"story_title":"",
	"prompt":"{\"version\":6,\"title\":\"Title here\",\"content\":[{\"type\":\"paragraph\",\"children\":[{\"type\":\"text\",\"text\":\"Replace this with at least a few sentences before generating.\"}]}],\"memory\":\"\",\"authorsNote\":\"\",\"worldInfo\":[],\"snippets\":[],\"genMeta\":{\"dataset\":0,\"literotica\":{\"author\":\"\",\"category\":\"\",\"tags\":[],\"targetLength\":5000},\"goodreads\":{\"author\":\"\",\"pubDate\":2020,\"tags\":[],\"targetLength\":25000}},\"target_length\":25000,\"forkedFrom\":null}"
}
"""
