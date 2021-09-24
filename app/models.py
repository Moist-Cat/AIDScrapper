from pathlib import Path
# import traceback
from abc import ABC, abstractmethod
from collections.abc import MutableMapping
import json
import datetime

from typing import Any, List, Dict

from aids.app.writelogs import log_error, log
from aids.app import settings
from aids.app.schemes import AIDStoryScheme, AIDScenScheme, NAIScenScheme

BASE_DIR = settings.BASE_DIR

class ValidationError(Exception):
    pass


class FieldValueIs:
    def __init__(self, field, value):
        self.field = field
        self.value = value

    def validate(self, data):
        if self.value and data[self.field] != self.value:
            raise ValidationError(
                f"Invalid {self.field}. It should have been "
                f"{self.value} got {data[self.field]}"
            )


class FieldLenLargerThan:
    def __init__(self, field, value):
        self.field = field
        self.value = value

    def validate(self, data):
        # We need to identify to wich service the data belongs here
        # AID's publicId is unique
        if (actions := len(eval('data' + self.field))) <= self.value:
            raise ValidationError(
                'Too few actions. It must have been more than '
                f'{self.value} got {actions}'
            )

class FieldNotBlank:
    def __init__(self, fields):
        self.fields: tuple = fields

    def validate(self, data):
        for field in self.fields:
            if not data[field]:
                raise ValidationError(f"{field} can not be blank")


class AIDSObject(ABC, dict):
    """Base aids object Container class from where all other containers
    must inherit
    """

    data: Dict
    validators: List

    def __init__(self):

        # notice that - unlike the backup path - this one is relative
        # using the module via commands from another directory will dump
        # the stories to that directory
        self.default_json_file = f"{self.__class__.__name__.lower()}.json"
        # right here
        self.default_scenario_path = Path().cwd()
        self.default_backups_file = (
            BASE_DIR / f"backups/"
            f"{self.__class__.__name__.lower()}_{datetime.datetime.today()}.json"
        )

    def __len__(self):
        super().__len__()

    def __iter__(self):
        return super().__iter__()

    def __getitem__(self, key):
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    def __delitem__(self, key):
        super().__delitem__(key)

    @abstractmethod
    def validate(self, value):
        pass

    # --- core ---
    @abstractmethod
    def _add(self, value: dict):
        raise ValidationError

    def add(self, value: dict):
        try:
            self._add(value)
        except ValidationError:
            pass

    def dump(self):
        try:
            with open(self.default_json_file, "w") as file:
                json.dump(tuple(self.values()), file)
            with open(self.default_backups_file, "w") as file:
                json.dump(tuple(self.values()), file)
        except json.decoder.JSONDecodeError:
            validated_data = (
                self.values()
                if len(self) < 2
                else list(self.keys())
            )
            log_error("error", f"Error while dumping the data. Validated data: {validated_data}")

    def load(self):
        """Load data form a json file.
        """
        try:
            with open(self.default_json_file) as file:
                raw_data = json.load(file)
            log(
                 "log",
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
                 "error",
                f"Error while loading the data. {file.name} does not contain valid JSON."
            )
        log("log", "{len(self)} objects loaded from the {file}")

    @staticmethod
    def clean_titles(data: dict):
        """Substitute dangerous characters from the data \"title\" key and
        its options if present.
        """
        try:
            data["title"] = data["title"].replace("/", "-").replace("\\", "-")
        except (KeyError, AttributeError):
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

    def __init__(self, title: str = ""):
        super().__init__()

        self.title = title or settings.DEFAULT_TITLE

    def __call__(self, title):
        self.title = title

    def _add(self, value: dict):
        self.data.update(value)
        data = self.data.copy()
        try:
            self.validate(value)
        except ValidationError as e:
            raise
        else:
            self.clean_titles(data)
            self.update({value['title']: data})

    def validate(self, value):
        validators = [
            FieldValueIs('title', self.title),
            FieldNotBlank(('title', 'prompt'))
        ]
        for validator in validators:
            validator.validate(value)

class BaseStory(AIDSObject):
    action_field: str = '[\"actions\"]'

    def __init__(self, title: str = "", actions: int = 0):
        super().__init__()

        self.title = title or settings.DEFAULT_TITLE
        self.actions = actions or settings.DEFAULT_MIN_ACT
    
    def __call__(self, title, actions):
        self.title = title
        self.actions = actions

    def _add(self, value: dict):
        self.data.update(value)
        try:
            self.validate(value)
        except ValidationError as e:
            raise
        else:
            self.clean_titles(self.data)
            self.update({((value['title']),len(eval('value' + self.action_field))): self.data})

    def validate(self, value):
        validators = [
            FieldValueIs('title', self.title),
            FieldLenLargerThan(self.action_field, self.actions),
            FieldNotBlank(('title',))
        ]
        for validator in validators:
            validator.validate(value)

class Scenario(BaseScenario):
    """AID Scenario model container."""

    data = AIDScenScheme

class Story(BaseStory):
    """AID Story model container"""

    data = AIDStoryScheme

class NAIScenario(BaseScenario):
    """NAI scenario model container"""

    data = NAIScenScheme
    action_field = '[\"story\"][\"fragments\"]'
    
    def dump_single_files(self):
        for scenario in self.values():
            try:
                with open(
                    self.default_scenario_path /
                    f"{scenario['title']}-{str(datetime.datetime.today())}.scenario",
                    "w"
                ) as file:
                    json.dump(scenario, file)
            except json.decoder.JSONDecodeError:
                log_error("error", f"Error while dumping the data. Validated data: {scenario}")
