import os
import glob
from pathlib import Path
from abc import ABC, abstractmethod
from collections.abc import MutableMapping
import json
import uuid

from typing import Any, List, Dict

from aids.app.writelogs import logged
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
        if self.value and data[self.field] != self.value and "isOption" not in data: # ignore subscens
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

@logged
class AIDSObject(ABC, dict):
    """Base aids object Container class from where all other containers
    must inherit. It ineriths from the dict builtin object so it behaves pretty much
    like one -- except with the fact that data should be passed to the add method to 
    properly form the keys.
    """

    data: Dict
    validators: List

    def __init__(self):
        super().__init__()

        # notice that - unlike the backup path - this one is relative
        # using the module via commands from another directory will dump
        # the stories to that directory
        self.default_json_file = f"{self.__class__.__name__.lower()}.json"
        # right here
        self.default_scenario_path = Path().cwd()
        self.unique_indendifier = str(uuid.uuid4())
        self.default_backups_file = (
            BASE_DIR / "backups" /
            f"{self.__class__.__name__.lower()}_{self.unique_indendifier}.json"
        )

    def __len__(self):
        return len(self.keys())

    def __setitem__(self, key, value):
        self.data.update(value)
        self.clean_titles(self.data)
        try:
            for validator in self._validators():
                validator.validate(self.data)
        except ValidationError as exc:
            raise ValidationError from exc
        else:
            super().__setitem__(key, self.data.copy())
    
    def update(self, other=(), /, **kwds):
        # The builtin dict.update method
        # does not use __setattr__ (because it is implemented in C) 
        # therefore we must use MutableMapping.update
        MutableMapping.update(self, other, **kwds)

    # --- core ---
    @abstractmethod
    def _add(self, value: dict):
        """This saves the object with a proper key. Letting the Validation error raise."""
        raise NotImplementedError
        

    def add(self, value: dict):
        """This handles the exception that __setitem__ could raise.
        """
        try:
            self._add(value)
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
            self.logger_err.error(
                "Error while dumping the data. Validated data: %s",
                validated_data
            )
        self.logger.info("Dumped all data to %s", self.default_json_file)

    def load(self):
        """Load data form a json file.
        """
        try:
            with open(self.default_json_file) as file:
                raw_data = json.load(file)
            self.logger.info(
                "Loading data... %d objects found, proceeding to validate.",
                len(raw_data)
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
            self.logger_err.error(
                "Error while loading the data. %s does not contain valid JSON.",
                file.name
            )
        self.logger.info("%d objects loaded from the %s", len(self), file.name)

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
            if data["title"]:
                data["title"] = data["title"].replace("/", "-").replace("\\", "-")
            else:
                data["title"] = "Untitled"
        except (KeyError, AttributeError):
            data["title"] = "Untitled"
        if "options" in data:
            for option in data["options"]:
                option["title"] = option["title"].replace("/", "-").replace("\\", "-")
        return data

class BaseScenario(AIDSObject):
    """
    Base Scenario object.
    """

    def __init__(self, title: str = ""):
        super().__init__()

        self.title = title or settings.DEFAULT_TITLE

    def __call__(self, title):
        self.title = title

    def _add(self, value: dict):
        key = value['title']
        self.__setitem__(key, value)

    def _validators(self):
        self.validators = [
            FieldValueIs('title', self.title),
            FieldNotBlank(('title', 'prompt'))
        ]
        return self.validators

class BaseStory(AIDSObject):
    """
    Base story object.
    """
    # The action_field attribute is 
    # a string that is meant to be passed to eval to get the action
    # objects from the data.
    action_field: str = '[\"actions\"]'

    def __init__(self, title: str = "", actions: int = 0):
        super().__init__()

        self.title = title or settings.DEFAULT_TITLE
        self.actions = actions or settings.DEFAULT_MIN_ACT
    
    def __call__(self, title, actions):
        self.title = title
        self.actions = actions

    def _add(self, value: dict):
        key = (
            value['title'],
            len(eval('value' + self.action_field))
        )
        self.__setitem__(key, value)

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
            scenario = self.clean_titles(scenario)
            try:
                with open(
                    self.default_scenario_path /
                    f"{scenario['title']}_{self.unique_indendifier}.scenario",
                    "w"
                ) as file:
                    json.dump(scenario, file)
            except json.decoder.JSONDecodeError:
                self.logger_err.error("Error while dumping the data. Validated data: %s", scenario)
