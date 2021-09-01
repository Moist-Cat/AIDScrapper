import abc
from abc import abstractmethod
import json
import datetime
from warnings import warn

from .logging import log_error, log
from . import settings

warnings = settings.WARNINGS
BASE_DIR = settings.BASE_DIR


class ValidationError(Exception):
    pass

class AIDObject:
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
            "mode": 'creative',
            "isOption": False,
            "prompt": None,
            "quests": [],
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
        
        self.default_json_file = BASE_DIR / f'{self.__class__.__name__.lower()}.json'
        self.default_backups_file = BASE_DIR /  f'backups/{self.__class__.__name__.lower()}.json' \
                                     f'_{datetime.datetime.today()}.json'
    
    def __len__(self) -> int:
        return len(self.out)
    
    @abstractmethod
    def __contains__(self) -> bool:
        raise NotImplementedError('You must override this method in the subclass')

    @abstractmethod
    def _data_is_valid(self):
        raise NotImplementedError('You must override this method in the subclass')

    # --- core ---
    @abstractmethod
    def validate(self, data: dict):
        raise NotImplementedError('You must override this method in the subclass')


    def add(self, dirty_data: dict):
        for k, v in dirty_data.items():
            if k in self.data.keys():
                self.data[k] = v
            elif warnings:
                if k not in ('type', 'score'):
                    warn(
                        f'{k} is not a valid value for ' \
                        f'a {self.__class__.__name__.lower()}'
                    )
        if self._data_is_valid():
            self.clean_titles(self.data)
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
            log_error(
                'Error while dumping the data. Validated data:' \
                f'{self.out if len(self.out) < 4 else self.out[0]["title"]}'
            )
   
    def load(self):
        try:
            with open(self.default_json_file) as file:
                raw_data = json.load(file)
            log(f'Loading data... {len(raw_data)} objects found, proceeding to validate.')
            if type(raw_data) != list:
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

    # --- helpers ---
    def clean_titles(self, data: dict):
        data['title'] = data['title'].replace('/', '-').replace('\\', '-')
        if 'options' in data:
            data['options'] = [
                option.update(
                    {
                        'title': option['title'].replace('/', '-').replace('\\', '-')
                    }
                ) for option in data['options']
            ]
        return data

class Scenario(AIDObject):
    def __init__(self, title=settings.default_title):
        super().__init__()
        self.title = title
        self.data.update({
            "gameCode": None,
            "options": []
        })

    def __contains__(self, other) -> bool:
        return any(s['title'] == other['title'] for s in self.out)

    def _data_is_valid(self):
        """
        Here we handle the exceptions raised by validate() and 
        give the apropriate warning.
        """
        try:
            self.validate(self.data)
        except ValidationError:
            if warnings:
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
            raise
        else:
            return True

    def validate(self, data: dict):
        if not data['title'] or \
                (self.title and data['title'] != self.title
        ) or data in self:
            raise ValidationError

class Story(AIDObject):
    def __init__(
        self,
        title=settings.default_title,
        min_act=settings.default_min_action
    ):
        super().__init__()
        self.title = title
        self.min_act = min_act
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
            if warnings:
                valid_actions = not (len(self.data["actions"]) <= self.min_act)
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
            raise
        else:
            return True

    def validate(self, data: dict):
        if len(data['actions']) <= self.min_act or (
            self.title and data['title'] != self.title
        ) or data in self:
            raise ValidationError
