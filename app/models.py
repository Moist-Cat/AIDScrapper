import settings
import json
import datetime

class ValidationErorr(Exception):
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
        "createdAt": datetime.today(),
        "updatedAt": datetime.today()
    }
    out = []
    
    def __len__(self):
        return len(out)

    def validate(self, data: dict) -> bool:
        raise NotImplementedError('You must override this method in the subclass')

    def add(self, data: dict) -> None:
        for k, v in data.items():
            if k in self.data.keys():
                self.data[k] = v
            else:
                print(
                    f'Warning: {k} is not a valid value for ' \
                    f'a {self.__class__.__name__.lower()}'
                )
        self.validate(data)
        self.out.append(data)

    def dump(self) -> None:
        with open(f'{self.__class__.__name__.lower()}.json', 'w') as file:
            json.dump(self.data, file)
        with open(
           f'backups/{lower(self.__class__.__name__).lower()}_ ' \
            '{datetime.today()}.json}', 'w'
        ) as file:
            json.dump(self.data, file)
        

class Scenario(AIDObject):
    def __new__(cls):
        result = super().__new__(cls)
        result.data.update({
            "gameCode": None,
            "options": []
        })
        return result
    
    def __init__(self, title=""):
        self.title = title
   
    def validate(self, data):
        if data['title'] is None or \
                (self.title and data['title'] != self.title):
            raise ValidationError

class Story(AIDObject):
    def __new__(cls):
        result = super().__new__(cls)
        result.data.update({
            'actions': [],
            'undoneWindow': []
        })
        return result

    def __init__(self, title="", actions=10):
        self.title = title
        self.actions

    def validate(self, data):
        if not data['actions'] or \
                (self.title and data['title'] != self.title) or \
                (len(data['actions']) <= self.actions):
            raise ValidationError
