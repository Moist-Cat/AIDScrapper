import abc
from abc import abstractmethod
import json
import datetime
from warnings import warn
from typing import Sequence, Any

from aids.app.writelogs import log_error, log
from aids.app import settings

WARNINGS = settings.WARNINGS
BASE_DIR = settings.BASE_DIR


def clean_titles(data: dict):
    try:
        data['title'] = data['title'].replace('/', '-').replace('\\', '-')
    except AttributeError:
        data['title'] = 'Untitled'
    if 'options' in data:
        data['options'] = [
            option.update(
                {
                    'title': option['title'].replace('/', '-').replace('\\', '-')
                }
            ) for option in data['options']
        ]
    return data

class ValidationError(Exception):
    pass

class AIDObject(metaclass=abc.ABCMeta):
    """
    Base AID Model class
    """
    def __init__(self):
        self.title: str = ''
        self.min_act: int = 0
        self.data: dict = {
            "id": None,
            "publicId": None,
            "title": None,
            "description": None,
            "tags": [],
            "createdAt": None,
            "updatedAt": None,
            "memory": None,
            "authorsNote": None,
            "isOption": False,
            "prompt": None,
            "worldInfo": None,
            "createdAt": datetime.datetime.strftime(
                             datetime.datetime.today(),
                             '%Y/%m/%d'
                         ),
            "updatedAt": datetime.datetime.strftime(
                             datetime.datetime.today(),
                             '%Y/%m/%d'
                         )
        }
        self.out: list = []
        
        # notice that - unlike the backup path - this one is relative
        # using the module via commands from another directory will dump
        # the stories to that directory
        self.default_json_file =  f'{self.__class__.__name__.lower()}.json'
        self.default_backups_file = BASE_DIR /  f'backups/' \
                f'{self.__class__.__name__.lower()}_{datetime.datetime.today()}.json'

    def __call__(self, title: str = '', min_act: int = 0):
        """
        To change the filters on-the-go. It could have been a regular method,
        but this seems more intuitive.
        """
        self.title = title
        self.min_act = min_act

    def __len__(self) -> int:
        return len(self.out)
    
    @abstractmethod
    def __contains__(self, other: Any) -> bool:
        raise NotImplementedError('You must override this method in the subclass')

    def _data_is_valid(self) -> bool:
        """
        Required for handling the exception from validate() and providing the adequate warning 
        for each case.
        """
        try:
            self.validate(self.data)
        except ValidationError:
            warn(f'Validation failed for {self.data["title"]}')
        else:
            return True
        return False

    # --- core ---
    @abstractmethod
    def validate(self, data: dict):
        raise NotImplementedError('You must override this method in the subclass')

    def add(self, dirty_data: dict):
        for k, v in dirty_data.items():
            if k in self.data.keys():
                self.data[k] = v
            elif WARNINGS:
                if k not in ('type', 'score', 'mode', 'quests'):
                    warn(
                        f'{k} is not a valid value for ' \
                        f'a {self.__class__.__name__.lower()}'
                    )
        if self._data_is_valid():
            clean_titles(self.data)
            self.out.append(self.data)
        self.data = self.data.fromkeys(self.data, '')
        self.data['createdAt'] = self.data['updatedAt'] = datetime.datetime.strftime(
                                                             datetime.datetime.today(),
                                                             '%Y/%m/%d'
                                                         )

    def dump(self):
        try:
            with open(self.default_json_file, 'w') as file:
                json.dump(self.out, file)
            with open(self.default_backups_file, 'w') as file:
                json.dump(self.out, file)
        except json.decoder.JSONDecodeError:
            validated_data = self.out if len(self.out) < 2 else ", ".join(
                    [object["title"] for object in self.out]
                )
            log_error(
                f'Error while dumping the data. Validated data: {validated_data}'
            )
   
    def load(self):
        try:
            with open(self.default_json_file) as file:
                raw_data = json.load(file)
            log(f'Loading data... {len(raw_data)} objects found, proceeding to validate.')
            if not isinstance(raw_data, Sequence):
                raise TypeError(
                    f'Error while parsing the data. {file.name} json data is not ' \
                    f'correctly formatted. {self.__class__.__name__}s must be placed '\
                    'in an array (or list).'
                )
            for scenario in raw_data:
                try:
                    self.add(scenario)
                except ValidationError:
                    pass
        except json.decoder.JSONDecodeError:
            log_error(
                f'Error while loading the data. {file.name} does not contain valid JSON.'
            )

class Scenario(AIDObject):
    def __init__(self, title: str = ''):
        super().__init__()

        self.title = title or settings.DEFAULT_TITLE

        self.data.update({
            "gameCode": None,
            "options": []
        })

    def __contains__(self, other) -> bool:
        return any(s['title'] == other['title'] for s in self.out)

    def _data_is_valid(self):
        try:
            self.validate(self.data)
        except ValidationError:
            if WARNINGS:
                valid_title = not (not self.data['title'] or (self.title and self.data['title'] != self.title))
                unique = not (self.data in self)

                bad_title_msg = f', Should have been {self.title} got {self.data["title"]}'
                is_duplicate_msg = f', A {self.__class__.__name__} titled {self.data["title"]} already exists'
                
                invalid_title = f'valid title: {valid_title}' \
                                 f'{bad_title_msg if not valid_title else ""}'
                is_duplicate = f'is unique: {unique}' \
                                       f'{is_duplicate_msg if not unique else ""}'

                final_warning = '\n'.join([invalid_title, is_duplicate])

                warn(final_warning)
        else:
            return True
        return False

    def validate(self, data: dict):
        if not data['title'] or \
                (self.title and data['title'] != self.title
        ) or data in self:
            raise ValidationError

class Story(AIDObject):
    def __init__(
        self,
        title: str = '',
        min_act: int = 0
    ):
        super().__init__()

        self.title = title or settings.DEFAULT_TITLE
        self.min_act = min_act or settings.DEFAULT_MIN_ACT

        self.data.update({
            'actions': [],
            'undoneWindow': [],
        })

    def __contains__(self, other) -> bool:
        return any(
            s['title'] == other['title'] and len(s['actions']) == len(other['actions']) for s in self.out
        )

    def _data_is_valid(self):
        try:
            self.validate(self.data)
        except ValidationError:
            if WARNINGS:
                valid_actions = not (len(self.data['actions']) <= self.min_act)
                valid_title = not (self.title and self.data['title'] != self.title)
                unique = not (self.data in self)

                bad_title_msg = f', Should have been {self.title} got {self.data["title"]}'
                few_act_msg = f', Sould have been more than {self.min_act} got {len(self.data["actions"])}'
                is_duplicate_msg = f', The {self.__class__.__name__} titled {self.data["title"]} ' \
                                   f' with {len(self.data["actions"])} already exists'

                invalid_title = f'valid title: {valid_title}' \
                                 f'{bad_title_msg if not valid_title else ""}'
                invalid_action_total = f'valid actions: {valid_actions}' \
                                       f'{few_act_msg if not valid_actions else ""}'
                is_duplicate = f'is unique: {unique}' \
                                       f'{is_duplicate_msg if not unique else ""}'

                final_warning = '\n'.join([invalid_title, invalid_action_total, is_duplicate])

                warn(final_warning)
        else:
            return True
        return False

    def validate(self, data: dict):
        if len(data['actions']) <= self.min_act or (
            self.title and data['title'] != self.title
        ) or data in self:
            raise ValidationError
