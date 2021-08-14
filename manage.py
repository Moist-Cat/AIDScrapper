import requests
import json
import sys
import glob
import getpass
import os

import bs4

from app.client import AIDScrapper, ClubClient
import to_html


def command(*args):
    try:
        command = args[0][1]
    except:
        # assume "all"
        command = "all"
    try:
        title=args[0][2]
    except IndexError:
        title=""
    try:
        actions = args[0][3]
    except IndexError:
        actions="10"


    if command in ('scenarios', 'stories', 'all'):
        aid = AIDScrapper()
        aid.adventures(title, actions)
        aid.prompts(title)

        aid.get_keys()
    elif command != 'help':
        club = ClubClient()

    if command == ('stories' or 'all'):
        aid.get_stories()
        aid.adventures.dump()
        to_html.story_to_html()

    if command == ('scenarios' or 'all'):
        aid.get_scenarios()
        aid.prompts.dump()
        to_html.scenario_to_html()

    elif command == 'publish':
        club.publish(title)
    
    elif command == 'makenai':
        scenario_to_json()
    
    elif command == 'fenix':
        try:
            with open('scenario.json') as file:
                data = json.load(file)
                aid.upload_in_bulk(data)
        except FileNotFoundError:
            aid.get_scenarios()
            aid.prompt.dump()
            a.upload_in_bulk(aid.prompt.out)
    
    elif command == 'test':
        os.system('python -m unittest -v app.tests')

    elif command == 'help':
        with open('help.txt') as file: print(file.read())

def reformat_context(json_data):
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
	       print(f'Uh-oh...')
	       # we can not verify, I guess.
	       json_data['memory'] = json_data['context'][0]['text']
	       json_data['authorsNote'] = json_data['context'][1]['text']
	       
	       print(f'Memory: {json_data["memory"]}')
	       print(f'AN: {json_data["authorsNote"]}')
	        
	       answer = input('Is this right?(Enter if it is):')
	       if not answer:
	           break
	       else:
	           print('Well, shit. You will have to ' \
	                 'change those manually. Be sure to report this bug')

def scenario_to_json():
	nai_file_name = glob.glob('*.scenario')
	scenario = []
	
	
	for name in nai_file_name:
	    with open(name) as file:
	        json_data = json.load(file)
	    

	    reformat_context(json_data)
	    
	    del json_data['context']
	    
	    # lorebook to worldInfo is way easier
	    json_data['worldInfo'] = json_data['lorebook']['entries']
	    # and, a smol detail
	    for entry in json_data['worldInfo']:
	       entry['entry'] = entry['text']
	       del entry['text']
	    
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

if __name__ == '__main__':
    command(sys.argv)
