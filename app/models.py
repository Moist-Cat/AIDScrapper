from . import settings
import json
import datetime

warnings = settings.WARNINGS
path = settings.BASE_DIR


class ValidationError(Exception):
    pass

class AIDObject:
    data = {
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
    out = []
    
    def __len__(self):
        return len(self.out)

    def validate(self, data: dict) -> bool:
        raise NotImplementedError('You must override this method in the subclass')

    def add(self, data: dict) -> None:
        for k, v in data.items():
            if k in self.data.keys():
                self.data[k] = v
            elif warnings:
                print(
                    f'Warning: {k} is not a valid value for ' \
                    f'a {self.__class__.__name__.lower()}'
                )
        try:
            self.validate(data)
        except ValidationError:
            valid_actions = not (len(data["actions"]) <= self.min_act)
            valid_title = not (self.title and data['title'] != self.title)
            
            bad_title_msg = f', Should have been {self.title} got {data["title"]}'
            few_act_msg = f', Sould have been at least {self.min_act} got {len(data["actions"])}'
            
            invalid_title = f'valid title: {valid_title}' \
                             f'{bad_title_msg if not valid_title else ""}'
            invalid_action_total = f'valid actions: {valid_actions}' \
                                   f'{few_act_msg if not valid_actions else ""}'
            
            
            raise ValidationError(invalid_title, invalid_action_total)
        else:
            # So the data is not appended even if the exception is handled
            self.out.append(data)

    def dump(self) -> None:
        with open(path / f'{self.__class__.__name__.lower()}.json', 'w') as file:
            json.dump(self.data, file)
        with open(
            path / f'backups/{lower(self.__class__.__name__).lower()}' \
                   f'_{datetime.today()}.json', 'w'
        ) as file:
            json.dump(self.data, file)
        

class Scenario(AIDObject):
    def __new__(cls, title=""):
        result = super().__new__(cls)
        result.title = title
        result.data.update({
            "gameCode": None,
            "options": []
        })
        return result

    def validate(self, data: dict) -> bool:
        if data['title'] is None or \
                (self.title and data['title'] != self.title):
            raise ValidationError

class Story(AIDObject):
    def __new__(cls, title="", min_act=10):
        result = super().__new__(cls)
        result.title = title
        result.min_act = min_act
        cls.data.update({
            'actions': [],
            'undoneWindow': [],
        })
        return result

    def validate(self, data: dict):
        if len(data["actions"]) <= self.min_act or (
            self.title and data['title'] != self.title
        ):
            raise ValidationError
