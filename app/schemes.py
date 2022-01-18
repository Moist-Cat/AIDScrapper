from collections.abc import MutableMapping
from typing import Dict, Any
import datetime
import sys


class FrozenKeyDict(dict):
    """Freeze the keys while keeping the values updatable"""

    def __setitem__(self, key, value, /):
        if key not in self.keys():
            return
        super().__setitem__(key, value)

    def update(self, other=(), /, **kwds):
        MutableMapping.update(self, other, **kwds)


def merge(any_dict: dict, other: dict) -> Dict[str, Any]:
    return_dict = any_dict.copy()
    """To keep compatibility between versions. The | operator was implemented in
    Python 3.9"""
    if sys.version[:3] == "3.9":
        return any_dict | other
    return_dict.update(other)
    return return_dict


DEFAULT: Dict = {
    "title": None,
    "description": None,
    "tags": [],
    "createdAt": datetime.datetime.strftime(datetime.datetime.today(), "%Y/%m/%d"),
    "updatedAt": datetime.datetime.strftime(datetime.datetime.today(), "%Y/%m/%d"),
}

aditional_keys = {
    "aid_payload": {
        "publicId": "",
        "prompt": "",
        "authorsNote": "",
        "quests": [],
        "musicTheme": None,
        "memory": None,
        "nsfw": False,
        "featured": False,
        "safeMode": True,
        "thirdPerson": False,
        "mode": "creative",
        "allowComments": True,
    },
    "aid_scen": {
        "publicId": "",
        "prompt": "",
        "memory": None,
        "authorsNote": "",
        "worldInfo": [],
        "isOption": False,
        "gameCode": None,
        "options": [],
        "nsfw": False,
    },
    "aid_story": {
        "publicId": "",
        "authorsNote": "",
        "worldInfo": [],
        "actions": [],
        "undoneWindow": [],
    },
    "nai_scen": {
        "scenarioVersion": 1,
        "prompt": "",
        "context": [
            {  # memory
                "text": "",
                "contextConfig": {
                    "prefix": "",
                    "suffix": "\n",
                    "tokenBudget": 2048,
                    "reservedTokens": 0,
                    "budgetPriority": 800,
                    "trimDirection": "trimBottom",
                    "insertionType": "newline",
                    "maximumTrimType": "sentence",
                    "insertionPosition": 0,
                },
            },
            {  # an
                "text": "",
                "contextConfig": {
                    "prefix": "",
                    "suffix": "\n",
                    "tokenBudget": 2048,
                    "reservedTokens": 2048,
                    "budgetPriority": -400,
                    "trimDirection": "trimBottom",
                    "insertionType": "newline",
                    "maximumTrimType": "sentence",
                    "insertionPosition": -4,
                },
            },
        ],
        "ephemeralContext": [],
        "placeholders": [],
        "settings": {
            "parameters": {
                "temperature": 0.72,
                "max_length": 40,
                "min_length": 1,
                "top_k": 0,
                "top_p": 0.725,
                "tail_free_sampling": 1,
                "repetition_penalty": 3,
                "repetition_penalty_range": 1024,
                "repetition_penalty_slope": 6.57,
                "bad_words_ids": [],
            },
            "preset": "default-optimalwhitepaper",
            "trimResponses": True,
            "banBrackets": True,
            "prefix": "",
        },
        "lorebook": {
            "lorebookVersion": 2,
            "entries": [
                {
                    "text": "",
                    "contextConfig": {
                        "prefix": "",
                        "suffix": "\n",
                        "tokenBudget": 2048,
                        "reservedTokens": 0,
                        "budgetPriority": 400,
                        "trimDirection": "trimBottom",
                        "insertionType": "newline",
                        "maximumTrimType": "sentence",
                        "insertionPosition": -1,
                    },
                    "lastUpdatedAt": 0,
                    "displayName": "",
                    "keys": [],
                    "searchRange": 1000,
                    "enabled": True,
                    "forceActivation": False,
                    "keyRelative": False,
                    "nonStoryActivatable": False,
                }
            ],
            "settings": {"orderByKeyLocations": False},
        },
        "author": "",
        "storyContextConfig": {
            "prefix": "",
            "suffix": "",
            "tokenBudget": 2048,
            "reservedTokens": 512,
            "budgetPriority": 0,
            "trimDirection": "trimTop",
            "insertionType": "newline",
            "maximumTrimType": "sentence",
            "insertionPosition": -1,
        },
        "contextDefaults": {
            "ephemeralDefaults": [
                {
                    "text": "",
                    "contextConfig": {
                        "prefix": "",
                        "suffix": "\n",
                        "tokenBudget": 2048,
                        "reservedTokens": 2048,
                        "budgetPriority": -10000,
                        "trimDirection": "doNotTrim",
                        "insertionType": "newline",
                        "maximumTrimType": "newline",
                        "insertionPosition": -2,
                    },
                    "startingStep": 1,
                    "delay": 0,
                    "duration": 1,
                    "repeat": False,
                    "reverse": False,
                }
            ],
            "loreDefaults": [
                {
                    "text": "",
                    "contextConfig": {
                        "prefix": "",
                        "suffix": "\n",
                        "tokenBudget": 2048,
                        "reservedTokens": 0,
                        "budgetPriority": 400,
                        "trimDirection": "trimBottom",
                        "insertionType": "newline",
                        "maximumTrimType": "sentence",
                        "insertionPosition": -1,
                    },
                    "lastUpdatedAt": 0,
                    "displayName": "New Lorebook Entry",
                    "keys": [],
                    "searchRange": 1000,
                    "enabled": True,
                    "forceActivation": False,
                    "keyRelative": False,
                    "nonStoryActivatable": False,
                }
            ],
        },
    },
}

AIDPayloadScenScheme = FrozenKeyDict(merge(DEFAULT, aditional_keys["aid_payload"]))
AIDScenScheme = FrozenKeyDict(merge(DEFAULT, aditional_keys["aid_scen"]))
AIDStoryScheme = FrozenKeyDict(merge(DEFAULT, aditional_keys["aid_story"]))
NAIScenScheme = FrozenKeyDict(merge(DEFAULT, aditional_keys["nai_scen"]))

# AID
story_query = {
    "variables": {"publicId": ""},
    "query": "query ($publicId: String) {\n  adventure(publicId: $publicId) {\n    id\n    userId\n    isOwner\n    userJoined\n    publicId\n    published\n    storySummary\n    enableSummarization\n    blockedAt\n    actions {\n      id\n      text\n      __typename\n    }\n    ...ContentHeadingSearchable\n    ...ContentOptionsSearchable\n    __typename\n  }\n}\n\nfragment ContentHeadingSearchable on Searchable {\n  id\n  title\n  description\n  tags\n  published\n  publicId\n  ... on Adventure {\n    actionCount\n    __typename\n  }\n  createdAt\n  updatedAt\n  deletedAt\n  ... on Adventure {\n    scenario {\n      id\n      title\n      publicId\n      published\n      deletedAt\n      __typename\n    }\n    __typename\n  }\n  user {\n    isCurrentUser\n    ...UserTitleUser\n    __typename\n  }\n  ...ContentStatsVotable\n  ...ContentStatsCommentable\n  __typename\n}\n\nfragment ContentStatsVotable on Votable {\n  ...VoteButtonVotable\n  __typename\n}\n\nfragment VoteButtonVotable on Votable {\n  id\n  userVote\n  totalUpvotes\n  __typename\n}\n\nfragment ContentStatsCommentable on Commentable {\n  ...CommentButtonCommentable\n  __typename\n}\n\nfragment CommentButtonCommentable on Commentable {\n  id\n  publicId\n  allowComments\n  totalComments\n  __typename\n}\n\nfragment UserTitleUser on User {\n  id\n  username\n  icon\n  ...UserAvatarUser\n  __typename\n}\n\nfragment UserAvatarUser on User {\n  id\n  username\n  avatar\n  __typename\n}\n\nfragment ContentOptionsSearchable on Searchable {\n  id\n  publicId\n  published\n  isOwner\n  title\n  userId\n  deletedAt\n  blockedAt\n  ... on Savable {\n    isSaved\n    __typename\n  }\n  ... on Adventure {\n    userJoined\n    __typename\n  }\n  __typename\n}\n",
}

# notice the sorting order
stories_query = {
    "variables": {
        "input": {
            "searchTerm": "",
            "saved": False,
            "trash": False,
            "contentType": "adventure",
            "sortOrder": "actionCount",
        }
    },
    "query": "query ($input: SearchInput) {\n  user {\n    id\n    search(input: $input) {\n      ...ContentListSearchable\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment ContentListSearchable on Searchable {\n  ...ContentCardSearchable\n  __typename\n}\n\nfragment ContentCardSearchable on Searchable {\n  id\n  publicId\n  userId\n  title\n  description\n  tags\n  createdAt\n  publishedAt\n  updatedAt\n  deletedAt\n  published\n  isOwner\n  user {\n    ...UserTitleUser\n    __typename\n  }\n  ... on Adventure {\n    actionCount\n    userJoined\n    blockedAt\n    scenario {\n      id\n      title\n      publicId\n      published\n      deletedAt\n      __typename\n    }\n    __typename\n  }\n  ...ContentOptionsSearchable\n  ...DeleteButtonSearchable\n  ...SaveButtonSavable\n  __typename\n}\n\nfragment ContentOptionsSearchable on Searchable {\n  id\n  publicId\n  published\n  isOwner\n  title\n  userId\n  deletedAt\n  blockedAt\n  ... on Savable {\n    isSaved\n    __typename\n  }\n  ... on Adventure {\n    userJoined\n    __typename\n  }\n  __typename\n}\n\nfragment DeleteButtonSearchable on Searchable {\n  id\n  publicId\n  published\n  __typename\n}\n\nfragment SaveButtonSavable on Savable {\n  id\n  isSaved\n  __typename\n}\n\nfragment UserTitleUser on User {\n  id\n  username\n  icon\n  ...UserAvatarUser\n  __typename\n}\n\nfragment UserAvatarUser on User {\n  id\n  username\n  avatar\n  __typename\n}\n",
}
# Scenarios

scenarios_query = {
    "variables": {
        "input": {
            "searchTerm": "",
            "saved": False,
            "trash": False,
            "contentType": "scenario",
            "sortOrder": "createdAt",
            "offset": 0,
        }
    },
    "query": "query ($input: SearchInput) {\n  user {\n    id\n    search(input: $input) {\n      ...ContentListSearchable\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment ContentListSearchable on Searchable {\n  ...ContentCardSearchable\n  __typename\n}\n\nfragment ContentCardSearchable on Searchable {\n  id\n  publicId\n  userId\n  title\n  description\n  tags\n  createdAt\n  publishedAt\n  updatedAt\n  deletedAt\n  published\n  isOwner\n  user {\n    ...UserTitleUser\n    __typename\n  }\n  ... on Adventure {\n    actionCount\n    userJoined\n    blockedAt\n    scenario {\n      id\n      title\n      publicId\n      published\n      deletedAt\n      __typename\n    }\n    __typename\n  }\n  ...ContentOptionsSearchable\n  ...DeleteButtonSearchable\n  ...SaveButtonSavable\n  __typename\n}\n\nfragment ContentOptionsSearchable on Searchable {\n  id\n  publicId\n  published\n  isOwner\n  title\n  userId\n  deletedAt\n  blockedAt\n  ... on Savable {\n    isSaved\n    __typename\n  }\n  ... on Adventure {\n    userJoined\n    __typename\n  }\n  __typename\n}\n\nfragment DeleteButtonSearchable on Searchable {\n  id\n  publicId\n  published\n  __typename\n}\n\nfragment SaveButtonSavable on Savable {\n  id\n  isSaved\n  __typename\n}\n\nfragment UserTitleUser on User {\n  id\n  username\n  icon\n  ...UserAvatarUser\n  __typename\n}\n\nfragment UserAvatarUser on User {\n  id\n  username\n  avatar\n  __typename\n}\n",
}

scenario_query = {
    "variables": {"publicId": ""},
    "query": "query ($publicId: String) {\n  scenario(publicId: $publicId) {\n    ...ScenarioEditScenario\n    __typename\n  }\n}\n\nfragment ScenarioEditScenario on Scenario {\n  id\n  publicId\n  allowComments\n  createdAt\n  deletedAt\n  description\n  memory\n  authorsNote\n  musicTheme\n  nsfw\n  prompt\n  published\n  featured\n  safeMode\n  tags\n  thirdPerson\n  title\n  updatedAt\n  blockedAt\n  options {\n    id\n    publicId\n    title\n    __typename\n  }\n  ...ContentOptionsSearchable\n  ...DeleteButtonSearchable\n  __typename\n}\n\nfragment ContentOptionsSearchable on Searchable {\n  id\n  publicId\n  published\n  isOwner\n  title\n  userId\n  deletedAt\n  blockedAt\n  ... on Savable {\n    isSaved\n    __typename\n  }\n  ... on Adventure {\n    userJoined\n    __typename\n  }\n  __typename\n}\n\nfragment DeleteButtonSearchable on Searchable {\n  id\n  publicId\n  published\n  __typename\n}\n",
}

wi_query = {
    "variables": {
        "type": "Active",
        "page": 0,
        "match": "",
        "pageSize": 1000,
        "contentPublicId": "",
        "contentType": "scenario",
        "filterUnused": False,
    },
    "query": "query ($type: String, $page: Int, $match: String, $pageSize: Int, $contentPublicId: String, $contentType: String, $filterUnused: Boolean) {\n  worldInfoType(type: $type, page: $page, match: $match, pageSize: $pageSize, contentPublicId: $contentPublicId, contentType: $contentType, filterUnused: $filterUnused) {\n    id\n    description\n    name\n    genre\n    tags\n    userId\n    type\n    generator\n    attributes\n    keys\n    entry\n    countContentWorldInfo\n    publicId\n    __typename\n  }\n  currentWorldInfoCount(type: $type, match: $match, contentPublicId: $contentPublicId, contentType: $contentType, filterUnused: $filterUnused)\n}\n",
}

aid_loginpayload = {
    "variables": {"identifier": "", "email": "", "password": ""},
    "query": """
mutation ($identifier: String, $email: String, $password: String, $anonymousId: String) {
    login(identifier: $identifier, email: $email, password: $password, anonymousId: $anonymousId) {
        accessToken
    }
}
""",
}

create_scen_payload = {
    "variables": {},
    "query": """mutation {
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
""",
}

update_scen_payload = {
    "variables": {
        "input": {
            "publicId": "",
            "title": "",
            "description": "",
            "prompt": "",
            "memory": "",
            "authorsNote": "",
            "quests": [],
            "musicTheme": None,
            "tags": [],
            "nsfw": False,
            "featured": False,
            "safeMode": True,
            "thirdPerson": False,
            "mode": "creative",
            "allowComments": True,
        }
    },
    "query": "mutation ($input: ScenarioInput) {\n  updateScenario(input: $input) {\n    ...ScenarioEditScenario\n    __typename\n  }\n}\n\nfragment ScenarioEditScenario on Scenario {\n  id\n  publicId\n  allowComments\n  createdAt\n  deletedAt\n  description\n  memory\n  authorsNote\n  mode\n  musicTheme\n  nsfw\n  prompt\n  published\n  featured\n  safeMode\n  quests\n  tags\n  thirdPerson\n  title\n  updatedAt\n  options {\n    id\n    publicId\n    title\n    __typename\n  }\n  ...ContentOptionsSearchable\n  ...DeleteButtonSearchable\n  __typename\n}\n\nfragment ContentOptionsSearchable on Searchable {\n  id\n  publicId\n  published\n  isOwner\n  tags\n  title\n  userId\n  ... on Savable {\n    isSaved\n    __typename\n  }\n  ... on Adventure {\n    userJoined\n    __typename\n  }\n  __typename\n}\n\nfragment DeleteButtonSearchable on Searchable {\n  id\n  publicId\n  published\n  __typename\n}\n",
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
            "attributes": {"name": None, "description": None},
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
    """,
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
            "isSelected": False,
        }
    },
    "query": """
        mutation ($input: WorldInformationInput) {
          createWorldInfoContent(input: $input) {
            id
            __typename
    """,
}

action_continue_payload = {
    "variables": {"input": {"publicId": "", "type": "continue", "characterName": None}},
    "query": """
            mutation ($input: ActionInput) {
              addAction(input: $input) {
                message
                time
                hasBannedWord
                returnedInput
                __typename
               }
           }
       """,
}

get_aid_user_payload = {
    "variables": {"username": ""},
    "query": "query ($username: String) {\n  user(username: $username) {\n    id\n    friends {\n      ...UserTitleUser\n      ...FriendButtonUser\n      __typename\n    }\n    followers {\n      ...UserTitleUser\n      ...FollowButtonUser\n      __typename\n    }\n    following {\n      ...UserTitleUser\n      ...FollowButtonUser\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment FollowButtonUser on User {\n  isCurrentUser\n  isFollowedByCurrentUser\n  __typename\n}\n\nfragment FriendButtonUser on User {\n  id\n  username\n  isCurrentUser\n  friendedCurrentUser\n  friendedByCurrentUser\n  __typename\n}\n\nfragment UserTitleUser on User {\n  id\n  username\n  icon\n  ...UserAvatarUser\n  __typename\n}\n\nfragment UserAvatarUser on User {\n  id\n  username\n  avatar\n  __typename\n}\n",
}

# Holo
# https://www.writeholo.com/api/draw_completions
generate_holo = {
    "story_id": "",
    "model_name": "goodreads-2-5",
    "input": [
        {
            "label": "prefix",
            "base_content": '{"source":"literotica","identifier":930290,"category":"","author":"RavenSun","rating":4.98,"tags":[],"view_count":101409,"series_meta":null,"location":0,"length":5000}\n',
        },
        {
            "cutoff_settings": {
                "ellipsis": True,
                "cutoff_direction": "left",
                "strategy": {"priority": 4, "max_length": 1500, "min_length": 1024},
            },
            "label": "prompt",
            "base_content": "",
        },
    ],
}
# https://www.writeholo.com/api/create_story
# Not required? OwO
"""
holo_create_story = {
    "story_title":"",
    "prompt":"{\"version\":6,\"title\":\"Title here\",\"content\":[{\"type\":\"paragraph\",\"children\":[{\"type\":\"text\",\"text\":\"Replace this with at least a few sentences before generating.\"}]}],\"memory\":\"\",\"authorsNote\":\"\",\"worldInfo\":[],\"snippets\":[],\"genMeta\":{\"dataset\":0,\"literotica\":{\"author\":\"\",\"category\":\"\",\"tags\":[],\"targetLength\":5000},\"goodreads\":{\"author\":\"\",\"pubDate\":2020,\"tags\":[],\"targetLength\":25000}},\"target_length\":25000,\"forkedFrom\":null}"
}
"""
