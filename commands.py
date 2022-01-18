from getpass import getpass
import json
import glob
import os
from pathlib import Path
from typing import Union

try:
    import pytest
except ImportError:
    pytest = None

from aids.app.client import AIDScrapper, ClubClient, HoloClient, bs4
import aids.to_html as to_html
from aids.app.settings import BASE_DIR, secrets_form, DEBUG
from aids.app.models import NAIScenario, Scenario


command_arg_dict = {
    'Aid': {
        'stories': ('title', 'actions'),
        'scenarios': ('title',),
        'all': ('title', 'actions'),
        'fenix': ()
    },
    'Club':{
        'publish': ('title',)
    },
    'Holo': {},
}

class Aid(AIDScrapper):
    def __init__(self):
        super().__init__()
        self.login()
        self.th = to_html.toHtml()

    def stories(self, title, min_act):
        self.adventures(title, min_act)

        self.get_stories()

        self.adventures.dump()
        self.th.story_to_html()

    def scenarios(self, title):
        self.prompts(title)

        self.get_scenarios()

        self.prompts.dump()
        self.th.scenario_to_html()

    def all(self, title, min_act):
        self.stories(title, min_act)
        self.scenarios(title)

    def fenix(self):
        try:
            self.prompts.load()
            self.upload_in_bulk(self.prompts)
        except FileNotFoundError:
            self.get_scenarios()
            self.prompts.dump()
            self.upload_in_bulk(self.prompts)

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

def makejson(source_files: str='*.scenario', target: str=''):
    data = _scenario_to_json(source_files)

    if target:
        data.default_json_file = target
    data.dump()

def _reformat_context(json_data):
    """reformat the context as memory and AN
    usually, 0 is memory whilst 1 is AN. But as 
    the russians say, \"Trust, but verify\"
    """
    for data in json_data['context']:
        if (
            not data['contextConfig']['insertionPosition'] or  
            data['contextConfig']['insertionPosition'] < -4
        ):
            json_data['memory'] = data['text']

        elif data['contextConfig']['insertionPosition'] == -4:
            json_data['authorsNote'] = data['text']

        else:
            # we can not verify, I guess.
            json_data['memory'] = json_data['context'][0]['text']
            json_data['authorsNote'] = json_data['context'][1]['text']

def _scenario_to_json(source_files: Union[str, Path]):
    nai_file_name = glob.glob(str(source_files))
    model = Scenario()

    for name in nai_file_name:

        with open(name) as file:
            json_data = json.load(file)

        _reformat_context(json_data)

        # lorebook to worldInfo is way easier
        json_data['worldInfo'] = [
            {
            'keys': entry['keys'], 'entry': entry['text']
            } for entry in json_data['lorebook']['entries']
        ]
        model.add(json_data.copy())

        if DEBUG is False:
            print('-------------------------------------')
            print(f'Your NAI scenario \"{json_data["title"]}\" was successfully ' \
                    're-formatted.')
            print('-------------------------------------')
    return model

def makenai(
        source_file: str='scenario.json',
        target: str='',
        single_files: bool=True
    ):
    data = _json_to_scenario(source_file)

    if target:
        data.default_json_file = target
        data.default_scenario_path = target
    if single_files:
        data.dump_single_files()
    else:
        data.dump()

def _json_to_scenario(source_file: Union[str, Path]) -> 'NAIScenario':
    model = NAIScenario()

    data_scheme = model.data.copy()
    an_scheme = data_scheme['context'].pop()
    memory_scheme = data_scheme['context'].pop()
    wi_entries_scheme = data_scheme['lorebook']['entries'].pop()

    with open(source_file) as file:
        json_data = json.load(file)
    
    for scenario in json_data:
        data_scheme.update(scenario)
        if 'worldInfo' in scenario and scenario['worldInfo']:
            entries = []
            for wi in scenario['worldInfo']:
                wi_entries_scheme.update({'text': wi['entry'], 'keys': wi['keys']})
                entries.append(wi_entries_scheme.copy())

        an_scheme.update({'text': scenario['authorsNote']})
        memory_scheme.update({'text': scenario['memory']})

        data_scheme.update({
            'context':[memory_scheme.copy(), an_scheme.copy()],
            'lorebook': {'entries': entries.copy()}
        })
        model.add(data_scheme.copy())
        if DEBUG is False:
            print('-------------------------------------')
            print(f'Your AID scenario \"{scenario["title"]}\" was successfully ' \
                    're-formatted.')
            print('-------------------------------------')

    return model

def test():
    if pytest:
        os.system(f'pytest {str(BASE_DIR)}/app/tests.py')
    else:
        os.system(f'python -m unittest -v aids.app.tests')

def help():
    with open(BASE_DIR / 'help.txt') as file:
        print(file.read())

def register():
    with open(BASE_DIR / 'app/secrets.json', 'w') as file:
        secrets_form.update({
            "AID_USERNAME": (user := input("AID username: ")),
            "AID_PASSWORD": getpass("AID password: ")
        })
        json.dump(secrets_form, file)
        print(f"User {user} successfully registered.")

def alltohtml(
        file_dir: Union[str, Path]='',
        story_outfile: str='',
        scenario_outfile: str=''
    ):
    th = to_html.toHtml()
    if file_dir:
        th.out_path = file_dir
    if story_outfile:
        th.story_out_file = story_outfile
    if scenario_outfile:
        th.scen_out_file = scenario_outfile
    try:
        th.story_to_html()
    except FileNotFoundError:
        print('The were no stories to transform into .html')
    try:
        th.scenario_to_html()
    except FileNotFoundError:
        print('The were no scenarios to transform into .html')
