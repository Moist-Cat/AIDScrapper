from pathlib import Path

__all__ = ['stories_query', 'ccs', 'scenarios_query', 'subscen_query', 'headers', 'aid_loginpayload']

aid = ['stories_query', 'ccs', 'scenarios_query', 'subscen_query', 'headers', 'aid_loginpayload']

club = ['headers']

# validation warnings
WARNINGS = False

# base path
BASE_DIR = Path(__file__).resolve().parent
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

headers = {
            'User-Agent':'Mozilla/5.0 (X11; Fedora; Linux x86_64) ' \
                         'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                         'Chrome/90.0.4430.93 Safari/537.36',
            'content-type': 'application/json',
}

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
