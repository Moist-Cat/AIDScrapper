import json
import glob
import os

from aids.app.client import AIDScrapper, ClubClient, HoloClient, bs4
import aids.to_html as to_html
from aids.app.settings import BASE_DIR
from aids.app.models import NAIScenario

# notice that these are sets inside a dict
command_arg_dict = {
    'Aid': {
        'stories': {'title', 'actions'},
        'scenarios': {'title'},
        'all': {'title', 'actions'},
        'fenix': set()
    },
    'Club':{
        'publish': {'title'}
    },
    'Holo': set(),
}

class Aid(AIDScrapper):
    def __init__(self):
        super().__init__()
        self.login()

    def stories(self, title, min_act):
        self.adventures(title, min_act)
        for story in self.my_stories:
            self.adventures.add(story)
        self.adventures.dump()
        to_html.story_to_html()

    def scenarios(self, title):
        self.prompts(title)
        for scenario in self.my_scenarios:
            self.prompts.add(scenario)
        self.prompts.dump()
        to_html.scenario_to_html()

    def all(self, title, min_act):
        self.stories(title, min_act)
        self.scenarios(title)

    def fenix(self):
        try:
            self.prompts.load()
            self.upload_in_bulk(self.prompts.out)
        except FileNotFoundError:
            for scenario in self.my_scenarios:
                self.prompts.add(scenario)
            self.prompts.dump()
            self.upload_in_bulk(self.prompts.out)
class Holo(HoloClient):
    pass

class Club(ClubClient):
    def publish(self, title):
        await_completition = True
        while await_completition:
            if bs4:
                self.publish_scenario(title)
                await_completition = False
            else:
                selection = input(
                    'bs4 not installed, unable to continue... want to install it now?' \
                    '(Enter to install bs4)'
                )
                if not selection:
                    os.system('pip3 install bs4')
                else:
                    break

def makenai():
    _scenario_to_json()

def _reformat_context(json_data):
    # reformat the context as memory and AN
    # usually, 0 is memory whilst 1 is AN. But as 
    # the russians say, \"Trust, but verify\"
    for data in json_data['context']:
        if (
            not data['contextConfig']['insertionPosition'] or  
            data['contextConfig']['insertionPosition'] < -4
        ):
            json_data['memory'] = data['text']

        elif data['contextConfig']['insertionPosition'] == -4:
            json_data['authorsNote'] = data['text']

        else:
            print('Uh-oh...')
            # we can not verify, I guess.
            json_data['memory'] = json_data['context'][0]['text']
            json_data['authorsNote'] = json_data['context'][1]['text']

            print(f'Memory: {json_data["memory"]}')
            print(f'AN: {json_data["authorsNote"]}')

            answer = input('Is this right?(Enter if it is):')
            if not answer:
                break
            print('Well, shit. You will have to ' \
                 'change those manually.')

def makejson():
    data = _json_to_scenario()
    data.dump()

def _json_to_scenario() -> 'NAIScenario':
    model = NAIScenario()

    data_scheme = model.data.copy()
    memory_scheme = data_scheme['context'][0].copy()
    an_scheme = data_scheme['context'][1].copy()
    wi_entries_scheme = data_scheme['lorebook']['entries'][0].copy()

    with open('scenario.json') as file:
        json_data = json.load(file)
    
    for scenario in json_data:
        data_scheme.update(scenario)
        if 'worldInfo' in scenario and scenario['worldInfo']:
            for wi in scenario['worldInfo']:
                wi_entries_scheme.update({'text': wi['entry']})
                wi_entries_scheme.update({'keys': wi['keys']})
                data_scheme['lorebook']['entries'].append(wi_entries_scheme)

        an_scheme.update({'text': scenario['authorsNote']})
        memory_scheme.update({'text': scenario['memory']})
        data_scheme.update({'context':[memory_scheme.copy(), an_scheme.copy()]})

        model.add(data_scheme)

    return model

def _scenario_to_json():
    nai_file_name = glob.glob('*.scenario')
    scenario = []

    for name in nai_file_name:
        with open(name) as file:
            json_data = json.load(file)

        _reformat_context(json_data)

        # lorebook to worldInfo is way easier
        json_data['worldInfo'] = json_data['lorebook']['entries']
        # and, a smol detail
        for entry in json_data['worldInfo']:
            entry['entry'] = entry['text']
        # required param
        json_data['quests'] = []
        # compatibility
        json_data['title'] = json_data['title'].replace('/', '-')
        json_data['createdAt'] = ''
        json_data['updatedAt'] = '' 

        # Extra details wont matter on the payload, as long we have 
        # the required info, so I will not bother on cleaing the NAI 
        # specific details form the json.
        scenario.append(json_data)

        print('-------------------------------------')
        print(f'Your NAI scenario \"{json_data["title"]}\" was successfully ' \
                're-formatted. You can publish it in the club whenever you want to.')
        print('-------------------------------------')
    with open('scenario.json', 'w') as file:
        json.dump(scenario, file)

def test():
    os.system('python -m unittest -v aids.app.tests')

def help():
    with open(BASE_DIR / 'help.txt') as file:
        print(file.read())
