from . import settings
import json
import datetime
from warnings import warn

warnings = settings.WARNINGS
path = settings.BASE_DIR


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
    
    def __len__(self):
        return len(self.out)

    def validate(self, data: dict):
        raise NotImplementedError('You must override this method in the subclass')

    def add(self, data: dict):
        for k, v in data.items():
            if k in self.data.keys():
                self.data[k] = v
            elif warnings:
                if k not in ['type', 'score']:
                    warn(
                        f'{k} is not a valid value for ' \
                        f'a {self.__class__.__name__.lower()}'
                    )
        try:
            self.validate(data)
        except ValidationError:
            # (TODO) it might be better to put this in the subclasses if 
            # we get more models
            if warnings:
                valid_actions = not (len(data["actions"]) <= self.min_act)
                valid_title = not (self.title and data['title'] != self.title)
                
                bad_title_msg = f', Should have been more than {self.title} got {data["title"]}'
                few_act_msg = f', Sould have been at least {self.min_act} got {len(data["actions"])}'
                
                invalid_title = f'valid title: {valid_title}' \
                                 f'{bad_title_msg if not valid_title else ""}'
                invalid_action_total = f'valid actions: {valid_actions}' \
                                       f'{few_act_msg if not valid_actions else ""}'
                final_warning = '\n'.join([invalid_title, invalid_action_total])

                warn(final_warning)

            raise
        else:
            # So the data is not appended even if the exception is handled
            self.out.append(data)

    def dump(self):
        with open(path / f'{self.__class__.__name__.lower()}.json', 'w') as file:
            json.dump(self.data, file)
        with open(
            path / f'backups/{lower(self.__class__.__name__).lower()}' \
                   f'_{datetime.today()}.json', 'w'
        ) as file:
            json.dump(self.data, file)
        

class Scenario(AIDObject):
    def __init__(self, title=""):
        super().__init__()
        self.title = title
        self.data.update({
            "gameCode": None,
            "options": []
        })

    def validate(self, data: dict):
        if data['title'] is None or \
                (self.title and data['title'] != self.title):
            raise ValidationError

class Story(AIDObject):
    def __init__(self, title="", min_act=10):
        super().__init__()
        self.title = title
        self.min_act = min_act
        self.data.update({
            'actions': [],
            'undoneWindow': [],
        })

    def validate(self, data: dict):
        if len(data["actions"]) <= self.min_act or (
            self.title and data['title'] != self.title
        ):
            raise ValidationError
