import os
import glob
from pathlib import Path
# import traceback
from abc import ABC, abstractmethod
from collections.abc import MutableMapping
import json
# Compatibility with Windows -- we can not add : to the path there
import uuid
import sys

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
        if self.value and data[self.field] != self.value and not ("isOption" in data): # ignore subscens
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
            # options do not count
            if not data[field] and not ("options" in data and any(data["options"])):
                raise ValidationError(f"{field} can not be blank")


class AIDSObject(ABC, dict):
    """Base aids object Container class from where all other containers
    must inherit. It ineriths from the dict builtin object so it behaves pretty much
    like one - except with the fact that data should be passed to the add method for
    validation.
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
        self.unique_indendifier = str(uuid.uuid4())
        self.default_backups_file = (
            BASE_DIR / f"backups" /
            f"{self.__class__.__name__.lower()}_{self.unique_indendifier}.json"
        )

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        return super().__iter__()

    def __getitem__(self, key):
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        self.data.update(value)
        try:
            for validator in self._validators:
                validator.validate(self.data)
        except ValidationError:
            raise
        else:
            self.clean_titles(self.data)
            super().__setitem__(key, self.data.copy())

    def __delitem__(self, key):
        super().__delitem__(key)
    
    def update(self, other=(), /, **kwds):
        """For some reason, the builtin dict.update method
        does not use __setattr__ therefore we must use MutableMapping.update
        """
        MutableMapping.update(self, other, **kwds)

    # --- core ---
    @abstractmethod
    def add(self, value: dict):
        """This handles the exception that __setitem__ could raise.
        """
        key = value['uuid']
        try:
            self.__setitem__(key, value)
        except ValidationError:
            pass

    def dump(self):
        try:
            with open(self.default_json_file, "w") as file:
                json.dump(tuple(self.values()), file)
            # check if there are too many backups
            backup_files = glob.glob(str(self.default_backups_file.parent / "*.json"))
            if len(backup_files) > 100:
                # remove the last files
                for file in backup_files[99:]:
                    os.remove(file)
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
        log("log", f"{len(self)} objects loaded from the {file.name}")

    @abstractmethod
    def _validators(self) -> List[Any]:
        """To properly initialize validators when they are needed -- not before.
        This is the class you must override if you want to add more validators."""
        self.validators: List[Any] = []
        return self.validators

    @staticmethod
    def clean_titles(data: dict):
        """Substitute dangerous characters from the data \"title\" key and
        its options if present.
        """
        assert "title" in data
        try:
            data["title"] = data["title"].replace("/", "-").replace("\\", "-")
        except KeyError:
            data["title"] = "Untitled"
        if "options" in data:
            for option in data["options"]:
                option["title"] = option["title"].replace("/", "-").replace("\\", "-")
        return data

class BaseScenario(AIDSObject):
    """Base Scenario object.
    """

    def __init__(self, title: str = ""):
        super().__init__()

        self.title = title or settings.DEFAULT_TITLE

    def __call__(self, title):
        self.title = title

    def add(self, value: dict):
        """This handles the exception that __setitem__ could raise.
        """
        key = value['title']
        try:
            self.__setitem__(key, value)
        except ValidationError:
            pass

    @property
    def _validators(self):
        self.validators = [
            FieldValueIs('title', self.title),
            FieldNotBlank(('title', 'prompt'))
        ]
        return self.validators

class BaseStory(AIDSObject):
    """Base story object. The action_field attribute is
    a string that is meant to be passed to eval to get the action
    objects.
    """
    action_field: str = '[\"actions\"]'

    def __init__(self, title: str = "", actions: int = 0):
        super().__init__()

        self.title = title or settings.DEFAULT_TITLE
        self.actions = actions or settings.DEFAULT_MIN_ACT
    
    def __call__(self, title, actions):
        self.title = title
        self.actions = actions

    def add(self, value: dict):
        """This handles the exception that __setitem__ could raise.
        """
        key = (
            value['title'],
            len(eval('value' + self.action_field))
        )
        try:
            self.__setitem__(key, value)
        except ValidationError:
            pass

    @property
    def _validators(self):
        self.validators = [
            FieldValueIs('title', self.title),
            FieldLenLargerThan(self.action_field, self.actions),
            FieldNotBlank(('title',))
        ]
        return self.validators

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
                    f"{scenario['title']}_{self.unique_indendifier}.scenario",
                    "w"
                ) as file:
                    json.dump(scenario, file)
            except json.decoder.JSONDecodeError:
                log_error("error", f"Error while dumping the data. Validated data: {scenario}")
