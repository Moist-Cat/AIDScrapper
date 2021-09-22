# import traceback
from abc import ABC, abstractmethod
from collections.abc import MutableSet
import json
import datetime

# from warnings import warn
from typing import Any, List, Dict

from aids.app.writelogs import log_error, log
from aids.app import settings

WARNINGS = settings.WARNINGS
BASE_DIR = settings.BASE_DIR

DEFAULT: Dict = {
    "title": None,
    "description": None,
    "tags": [],
    "createdAt": datetime.datetime.strftime(datetime.datetime.today(), "%Y/%m/%d"),
    "updatedAt": datetime.datetime.strftime(datetime.datetime.today(), "%Y/%m/%d"),
}


class ValidationError(Exception):
    pass


class Unique:
    def validate(self, obj, data):
        if data in obj:
            raise ValidationError(
                f'Object {data["title"]} already exists in '
                f"{obj.__class__.__name__}"
            )


class FieldValueIs:
    def __init__(self, field):
        self.field = field

    def validate(self, obj, data):
        default_val = getattr(obj, self.field)
        if default_val and data[self.field] != default_val:
            raise ValidationError(
                f"Invalid {self.field}. It should have been "
                f"{default_val} got {data[self.field]}"
            )


class FieldLenLargerThan:
    def __init__(self, field):
        self.field = field

    def validate(self, obj, data):
        if len(data[self.field]) <= (default_val := getattr(obj, self.field)):
            raise ValidationError(
                f"Too few {self.field}. Sould have been more than "
                f"{default_val} got {len(data[self.field])}"
            )

class FieldNotBlank:
    def __init__(self, fields):
        self.fields: tuple = fields

    def validate(self, obj, data):
        for field in self.fields:
            if not data[field]:
                raise ValidationError(f"{field} can not be blank")


class DataNormalizer:
    """Only update keys that already exist discarding all others."""

    # extra keys required, unique for each service or object
    aditional_keys: Dict[Any, Any]

    _data: dict

    def __init__(self):
        self._data = DEFAULT.copy()
        self._data.update(self.aditional_keys)

    def __get__(self, instance: Any, owner: type) -> Dict:
        return self._data

    def __set__(self, instance: Any, new_data):
        self._data = {k: v for k, v in new_data.items() if k in self._data.keys()}
        return self._data

class AIDBasicScenModel(DataNormalizer):
    """
    Containing the fields required to interact with AID\'s API.
    """

    aditional_keys = {
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
    }


class AIDScenModel(DataNormalizer):
    """Only containing relevant data to save locally, stripping everything
    else
    """

    aditional_keys = {
        "publicId": "",
        "prompt": "",
        "memory": None,
        "authorsNote": "",
        "worldInfo": [],
        "gameCode": None,
        "options": [],
        "nsfw": False,
    }


class AIDStoryModel(DataNormalizer):
    aditional_keys = {
        "publicId": "",
        "authorsNote": "",
        "worldInfo": [],
        "actions": [],
        "undoneWindow": [],
    }


class NAIScenModel(DataNormalizer):
    aditional_keys = {
        'scenarioVersion': 1,
        'prompt': '',
        'context': [
            {# memory
                'text': '',
                'contextConfig': {
                    'prefix': '',
                    'suffix': '\n',
                    'tokenBudget': 2048,
                    'reservedTokens': 0,
                    'budgetPriority': 800,
                    'trimDirection': 'trimBottom',
                    'insertionType': 'newline',
                    'maximumTrimType': 'sentence',
                    'insertionPosition': 0
                }
            },
            {# an
                'text': '',
                'contextConfig': {
                    'prefix': '',
                    'suffix': '\n',
                    'tokenBudget': 2048,
                    'reservedTokens': 2048,
                    'budgetPriority': -400,
                    'trimDirection': 'trimBottom',
                    'insertionType': 'newline',
                    'maximumTrimType': 'sentence',
                    'insertionPosition': -4
                }
            }
        ],
        'ephemeralContext': [],
        'placeholders': [],
        'settings': {
            'parameters': {
                'temperature': 0.72,
                'max_length': 40,
                'min_length': 1,
                'top_k': 0,
                'top_p': 0.725,
                'tail_free_sampling': 1,
                'repetition_penalty': 3,
                'repetition_penalty_range': 1024,
                'repetition_penalty_slope': 6.57,
                'bad_words_ids': []
            },
            'preset': 'default-optimalwhitepaper',
            'trimResponses': True,
            'banBrackets': True,
            'prefix': ''
        },
        'lorebook': {
            'lorebookVersion': 2,
            'entries': [
                {
                    'text': "",
                    'contextConfig': {
                        'prefix': '',
                        'suffix': '\n',
                        'tokenBudget': 2048,
                        'reservedTokens': 0,
                        'budgetPriority': 400,
                        'trimDirection': 'trimBottom',
                        'insertionType': 'newline',
                        'maximumTrimType': 'sentence',
                        'insertionPosition': -1
                    },
                    'lastUpdatedAt': 0,
                    'displayName': '',
                    'keys': [],
                    'searchRange': 1000,
                    'enabled': True,
                    'forceActivation': False,
                    'keyRelative': False,
                    'nonStoryActivatable': False
                }
            ],
            'settings': {'orderByKeyLocations': False}
        },
            'author': '',
            'storyContextConfig': {
                'prefix': '',
                'suffix': '',
                'tokenBudget': 2048,
                'reservedTokens': 512,
                'budgetPriority': 0,
                'trimDirection': 'trimTop',
                'insertionType': 'newline',
                'maximumTrimType': 'sentence',
                'insertionPosition': -1
            },
        'contextDefaults': {
            'ephemeralDefaults': [
                {
                    'text': '',
                    'contextConfig': {
                        'prefix': '',
                        'suffix': '\n',
                        'tokenBudget': 2048,
                        'reservedTokens': 2048,
                        'budgetPriority': -10000,
                        'trimDirection': 'doNotTrim',
                        'insertionType': 'newline',
                        'maximumTrimType': 'newline',
                        'insertionPosition': -2
                       },
                   'startingStep': 1,
                   'delay': 0,
                   'duration': 1,
                   'repeat': False, 'reverse': False
                }
            ], 'loreDefaults': [
                    {
                    'text': '',
                    'contextConfig': {
                        'prefix': '',
                        'suffix': '\n',
                        'tokenBudget': 2048,
                        'reservedTokens': 0,
                        'budgetPriority': 400,
                        'trimDirection': 'trimBottom',
                        'insertionType': 'newline',
                        'maximumTrimType': 'sentence',
                        'insertionPosition': -1
                    },
                    'lastUpdatedAt': 0,
                    'displayName': 'New Lorebook Entry',
                    'keys': [],
                    'searchRange': 1000,
                    'enabled': True,
                    'forceActivation': False,
                    'keyRelative': False,
                    'nonStoryActivatable': False
                    }
               ]
       }
    }

class AIDSObject(ABC, MutableSet):
    """Base aids object Container class from where all other containers
    must inherit
    """

    data: DataNormalizer
    validators: List

    def __init__(self):
        #(XXX) Remove this later - this is supposed to be the base container
        self.title: str = ""
        self.actions: int = 0

        self.out: List = []

        # notice that - unlike the backup path - this one is relative
        # using the module via commands from another directory will dump
        # the stories to that directory
        self.default_json_file = f"{self.__class__.__name__.lower()}.json"
        self.default_backups_file = (
            BASE_DIR / f"backups/"
            f"{self.__class__.__name__.lower()}_{datetime.datetime.today()}.json"
        )

    def __call__(self, title: str = "", actions: int = 0):
        """To change the filters on-the-go. It could have been a regular method,
        but this seems more intuitive.
        """
        #(XXX) Remove this too
        self.title = title
        self.actions = actions

    def __len__(self):
        return len(self.out)

    def __iter__(self):
        return iter(self.out)

    @abstractmethod
    def __contains__(self, other: Any):
        pass

    # --- core ---
    def _add(self, value: dict):
        self.data = value
        try:
            for validator in self.validators:
                validator.validate(self, self.data)
        except ValidationError as e:
            raise
        else:
            self.clean_titles(self.data)
            self.out.append(self.data)
    
    def add(self, value: dict):
        try:
            self._add(value)
        except ValidationError:
            pass

    def discard(self, obj_id: int):
        for index, obj in enumerate(self.out):
            if obj["id"] == obj_id:
                del self.out[index]

    def dump(self):
        try:
            with open(self.default_json_file, "w") as file:
                json.dump(self.out, file)
            with open(self.default_backups_file, "w") as file:
                json.dump(self.out, file)
        except json.decoder.JSONDecodeError:
            validated_data = (
                self.out
                if len(self.out) < 2
                else ", ".join([object["title"] for object in self.out])
            )
            log_error(f"Error while dumping the data. Validated data: {validated_data}")

    def load(self):
        """Load data form a json file.
        """
        try:
            with open(self.default_json_file) as file:
                raw_data = json.load(file)
            log(
                f"Loading data... {len(raw_data)} objects found, proceeding to validate."
            )
            if not isinstance(raw_data, List):
                raise TypeError(
                    f"Error while parsing the data. {file.name} json data is not "
                    f"correctly formatted. {self.__class__.__name__}s must be placed "
                    "in an array (or list)."
                )
            for scenario in raw_data:
                self.add(scenario)
        except json.decoder.JSONDecodeError:
            log_error(
                f"Error while loading the data. {file.name} does not contain valid JSON."
            )

    @staticmethod
    def clean_titles(data: dict):
        """Substitute dangerous characters from the data \"title\" key and
        its options if present.
        """
        try:
            data["title"] = data["title"].replace("/", "-").replace("\\", "-")
        except AttributeError:
            data["title"] = "Untitled"
        if "options" in data:
            data["options"] = [
                option.update(
                    {"title": option["title"].replace("/", "-").replace("\\", "-")}
                )
                for option in data["options"]
            ]
        return data

class BaseScenario(AIDSObject):

    validators = [
        FieldValueIs("title"),
        Unique(),
        FieldNotBlank(("title", "prompt"))
    ]

    def __init__(self, title: str = ""):
        super().__init__()

        self.title = title or settings.DEFAULT_TITLE

    def __contains__(self, other: Any):
        return any(s["title"] == other["title"] for s in self.out)

class BaseStory(AIDSObject):

    validators = [
        FieldLenLargerThan("actions"),
        FieldValueIs("title"),
        Unique(),
    ]

    def __init__(self, title: str = "", actions: int = 0):
        super().__init__()

        self.title = title or settings.DEFAULT_TITLE
        # use setattr to name the attribute containing the actions
        # for each aids service
        self.actions = actions or settings.DEFAULT_MIN_ACT

    def __contains__(self, other):
        return any(
            s["title"] == other["title"] and len(s["actions"]) == len(other["actions"])
            for s in self.out
        )

class Scenario(BaseScenario):
    """AID Scenario model container."""

    data = AIDScenModel()

class Story(BaseStory):
    """AID Story model container"""

    data = AIDStoryModel()

class NAIScenario(BaseScenario):
    """NAI scenario model container"""
    
    data = NAIScenModel()
    
    def dump_single_files(self):
        for scenario in self:
            try:
                with open(
                    f"{scenario['title']}-{str(datetime.datetime.today())}.scenario",
                    "w"
                ) as file:
                    json.dump(scenario, file)
            except json.decoder.JSONDecodeError:
                log_error(f"Error while dumping the data. Validated data: {scenario}")
