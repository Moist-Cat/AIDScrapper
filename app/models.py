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

    def _run_validation(self):
        raise NotImplementedError('You must override this method in the subclass')

    def validate(self, data: dict):
        raise NotImplementedError('You must override this method in the subclass')

    def add(self, dirty_data: dict):
        for k, v in dirty_data.items():
            if k in self.data.keys():
                # get rid of "/"s that break paths
                if k == 'title':
                    v = v.replace('/', '-')
                self.data[k] = v
            elif warnings:
                if k not in ('type', 'score'):
                    warn(
                        f'{k} is not a valid value for ' \
                        f'a {self.__class__.__name__.lower()}'
                    )
        self._run_validation()
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
    def __init__(self, title=settings.default_title):
        super().__init__()
        self.title = title
        self.data.update({
            "gameCode": None,
            "options": []
        })
        # to make sure we don't get duplicates with scenarios
        self.current_scenarios: set = set()

    def _run_validation(self):
        try:
            self.validate(self.data)
        except ValidationError:
            if warnings:
                valid_title = not (not self.data['title'] or (self.title and self.data['title'] != self.title))
                unique = not (self.data['title'] in self.current_scenarios)
                
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
            # So the data is not appended even if the exception is handled
            self.current_scenarios.add(self.data['title'])
            self.out.append(self.data)

    def validate(self, data: dict):
        if not data['title'] or \
                (self.title and data['title'] != self.title
        ) or data['title'] in self.current_scenarios:
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
        # with stories is a little more complicated. One would normally 
        # think that grabbing the ID would be the best choice, but unless we 
        # assign each one of them an ID ourselves and keep those stored there 
        # is no way of knowing if a story is unique without checking it line by line
        # doing so with thousand of stories would be pretty slow so we get the len() of 
        # the story plus the title to get a unique "key".
        # We are moving stories around so the date is not unique, by any means.
        self.current_stories: set = set()

    def __contains__(self, other) -> bool:
        raise any(s['title'] == other['title'] and len(s['actions']) == len(other['actions']) for s in self.out)

    def _run_validation(self):
        try:
            self.validate(self.data)
        except ValidationError:
            if warnings:
                valid_actions = not (len(self.data["actions"]) <= self.min_act)
                valid_title = not (self.title and self.data['title'] != self.title)
                unique = not ((self.data['title'], len(self.data['actions'])) in self.current_stories)
                
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
            # So the data is not appended even if the exception is handled
            self.current_stories.add((self.data['title'], len(self.data['actions'])))
            self.out.append(self.data)

    def validate(self, data: dict):
        if len(data['actions']) <= self.min_act or (
            self.title and data['title'] != self.title
        ) or (data['title'], len(data['actions'])) in self.current_stories:
            raise ValidationError
