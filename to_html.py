import sys
import os
import json
import html

from jinja2 import Environment, FileSystemLoader


env = Environment(loader=FileSystemLoader('templates'))

def new_dir(folder):
    if folder:
        try:
            os.mkdir(folder)
        except FileExistsError:
            pass
    with open('style.css', 'r') as file:
        style = file.read()
    with open(f'{folder}/style.css', 'w') as file:
        file.write(style)

def story_to_html():
    new_dir('stories')
    stories = json.load(open('stories.json'))

    story_templ = env.get_template('story.html')
    story_number = {}
    for story in stories:
        try:
            story_number[story["title"]]
        except KeyError:
            # new story
            story_number = {story["title"]: ""}
        if not os.path.exists(
            f'stories/{story["title"]}{story_number[story["title"]]}.html'
        ):
            htmlfile = open(f'stories/{story["title"]}.html', 'w')
        else:
            # story from same scenario
            if story_number[story["title"]]:
                story_number[story["title"]] += 1
                htmlfile = open(
                    f'stories/{story["title"]}{story_number[story["title"]]}.html',
                    'w'
                )
            else:
                story_number[story["title"]] = 2
                htmlfile = open(
                    f'stories/{story["title"]}{story_number[story["title"]]}.html',
                    'w'
                )
        htmlfile.write(
            story_templ.render({
                'story': story,
                'story_number': story_number
            })
        )
        htmlfile.close()
    print('Stories successfully formatted')

def scenario_to_html():
    new_dir('scenarios')
    scenarios = json.load(open('scenario.json'))

    subscen_paths = {}
    parent_scen = []
    for scenario in scenarios:
        scenario['title'] == scenario['title'].replace('/', '-')
        if 'isOption' not in scenario or scenario['isOption'] != True:
            # base scenario, initializing the path
            scenario['path'] = f'scenarios/'
            with open(f'{scenario["path"] + scenario["title"]}.html', 'w') as file:
                scen_templ = env.get_template('scenario.html')
                file.write(
                    scen_templ.render({
                        'scenario': scenario,
                        'content_type': 'scenario'
                    })
                )
            parent_scen.append(scenario)
        else:
            scenario['path'] = subscen_paths[scenario['title']]
        if 'options' in scenario:
            for subscen in scenario['options']:
                subscen['title'] = subscen['title'].replace('/', '-')
                subscen['path'] = f'{scenario["path"]}{scenario["title"]}'
                subscen_paths[subscen['title']] = subscen['path'] + '/'
                new_dir(subscen['path'])
                print(subscen['path'])

                with open(f'{subscen["path"]}/{subscen["title"]}.html', 'w') as file:
                    scen_templ = env.get_template('scenario.html')
                    file.write(
                        scen_templ.render({
                            'scenario': scenario,
                            'content_type': 'scenario'
                        })
                    )

    print(subscen_paths)
    index = env.get_template('index.html')
    with open('scen_index.html', 'w') as outfile:
        outfile.write(
            index.render(
                {'objects': parent_scen, 'content_type': 'scenario'
            })
        )
    print('Scenarios successfully formatted')
