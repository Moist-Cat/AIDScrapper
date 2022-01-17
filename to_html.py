import os
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from aids.app.settings import BASE_DIR

class toHtml:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(BASE_DIR / 'templates'))

        self.out_path = Path().cwd()
        self.scen_out_file = 'scenario.json'
        self.story_out_file = 'story.json'

    def new_dir(self, folder):
        if folder:
            try:
                os.mkdir(self.out_path / folder)
            except FileExistsError:
                pass
        with open(BASE_DIR / 'static/style.css', 'r') as file:
            style = file.read()
        with open(self.out_path / f'{folder}/style.css', 'w') as file:
            file.write(style)

    def story_to_html(self, infile: str=None):
        infile = infile or self.out_path / self.story_out_file

        self.new_dir('stories')
        with open(infile) as file:
            stories = json.load(file)

        story_templ = self.env.get_template('story.html')
        story_number = {}
        for story in reversed(stories):
            if story['title']:
                story['title'] = story['title'].replace('/', '-')
            try:
                story_number[story["title"]]
            except KeyError:
                # new story
                story_number = {story["title"]: ""}
            if not os.path.exists(
                self.out_path /
                f'stories/{story["title"]}{story_number[story["title"]]}.html'
            ):
                htmlfile = open(self.out_path / f'stories/{story["title"]}.html', 'w', encoding='utf-8')
            else:
                # story from same scenario
                if story_number[story["title"]]:
                    story_number[story["title"]] += 1
                    htmlfile = open(
                        self.out_path /
                        f'stories/{story["title"]}{story_number[story["title"]]}.html',
                        'w',
                        encoding='utf-8'
                    )
                else:
                    story_number[story["title"]] = 2
                    htmlfile = open(
                        self.out_path /
                        f'stories/{story["title"]}{story_number[story["title"]]}.html',
                        'w',
                        encoding='utf-8'
                    )
            htmlfile.write(
                story_templ.render({
                    'story': story,
                    'story_number': story_number
                })
            )
            htmlfile.close()
        index = self.env.get_template('index.html')
        with open(self.out_path / 'story_index.html', 'w') as outfile:
            outfile.write(
                index.render(
                    {'objects': stories, 'content_type': 'stories'
                })
            )
        print('Stories successfully formatted')

    def scenario_to_html(self, infile: str=None):
        infile = infile or self.out_path / self.scen_out_file
        self.new_dir('scenarios')
        with open(infile) as file:
            scenarios = json.load(file)

        subscen_paths = {}
        parent_scen = []
        for scenario in reversed(scenarios):
            scenario['title'] = scenario['title'].replace('/', '-')
            if 'isOption' not in scenario or not scenario['isOption']:
                # base scenario, initializing the path
                scenario['path'] = 'scenarios/'
                with open(
                        self.out_path /
                        f'{scenario["path"] + scenario["title"]}.html',
                        'w'
                ) as file:
                    scen_templ = self.env.get_template('scenario.html')
                    file.write(
                        scen_templ.render({
                            'scenario': scenario,
                            'content_type': 'scenario'
                        })
                    )
                parent_scen.append(scenario)
            else:
                scenario['path'] = subscen_paths[scenario['title']]
                
                with open(
                        self.out_path /
                        f'{scenario["path"]}/{scenario["title"]}.html',
                        'w'
                ) as file:
                    scen_templ = self.env.get_template('scenario.html')
                    file.write(
                        scen_templ.render({
                            'scenario': scenario,
                            'content_type': 'scenario'
                        })
                    )
            if "options" in scenario and any(scenario['options']):
                for subscen in scenario['options']:
                    if subscen and "title" in subscen:
                        subscen['title'] = subscen['title'].replace('/', '-')
                        subscen['path'] = f'{scenario["path"]}{scenario["title"]}'
                        subscen_paths[subscen['title']] = subscen['path'] + '/'
                        self.new_dir(subscen['path'])

        index = self.env.get_template('index.html')
        with open(self.out_path / 'scen_index.html', 'w') as outfile:
            outfile.write(
                index.render(
                    {'objects': parent_scen, 'content_type': 'scenarios'
                })
            )
        print('Scenarios successfully formatted')
