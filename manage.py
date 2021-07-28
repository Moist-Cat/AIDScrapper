import requests
import json
import sys
import glob
import getpass

import bs4

import app.client
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


    if command not in ('publish', 'makenai', 'help'):
        aid = client.AIDScrapper(title, actions)
    elif command != 'help':
        club = client.ClubClient()

    if command == ('stories' or 'all'):
        aid.get_stories(title, actions)
        aid.adventures.dump()
        to_html.scenario_to_html()

    if command == ('scenarios' or 'all'):
        aid.get_scenarios(title)
        aid.prompt.dump()
        to_html.scenario_to_html()

    if command == 'publish':
        club.publish(title)
    
    if command == 'makenai':
        scenario_to_json()
    
    if command == 'fenix':
        try:
            with open('scenario.json') as file:
                data = json.load(file)
                aid.upload_in_bulk(data)
        except FileNotFoundError:
            aid.get_scenarios()
            aid.prompt.dump()
            a.upload_in_bulk(aid.prompt.out)
    if command == 'help':
        print('''
Usage: python manage.py [publish/stories/scenarios/makenai/fenix] [title] [min_number_of_actions]

-------------------

Ex: python manage.py stories "My Story" 1000

Downloads any story from your account named "My Story",
then proceeds to dump it to the stories.json. mystuff_json_to_html.py is called
then to convert the file to html, so be sure you named it that way. Also you need style.css to be
in the folder too (is not important, so you can just make a blank file with that name).

It will not download any story with less than 1000 actions in this case, if you want to download 
any story with more than 1000 actions use:

python manage.py stories \"\" 1000

Note the \"\" and note that if you put python manage.py stories 1000 it will download any story 
named \"1000\".

---------------------

Ex: python manage.py scenarios "My Scenario"

Same as before.

--------------------

Ex: publish "My Scenario"

Publishes a scenario which the given name. You must have it in stories.json in the directory.
You need an account to do so, but you can register from here.

--------------------
Ex: makenai

Formats a .scenario file into a club friendly .json file, saved in stories.json
You can publish it afterwards.

--------------------

Ex: fenix

Posts all your stuff (stored in the .json) on your account.

--------------------

Ex: python manage.py all is the default, gets everything in your account (stories with
less than 10 actions are ignored) and makes the html

--------------------

(REMEMBER TO \"QUOTE\" the [title] option, or else it will give a nasty error.)
        ''')        

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
