import requests
import json
import sys

import bs4

from SA2_SA_mystuff_scrapper import AIDStuffGetter


def download(*args):
    """
    Made a switch to 
    """
    try:
        contentype = args[0][1]
    except:
        # assume "all"
        contentype = "all"
    try:
        title=args[0][2]
    except IndexError:
        title=""
    try:
        actions = args[0][3]
    except IndexError:
        actions="10"

    a = AIDStuffGetter()
    if contentype == 'stories':
        a.get_stories(title, actions)
        with open('stories.json', 'w') as outfile:
            json.dump(a.out, outfile)
        try:
            import SA2_my_stuff_json_to_html
        except ModuleNotFoundError:
            print('SA2_my_stuff_json_to_html.py was not found. Be sure you named it correctly.')
    if contentype == 'scenarios':
        a.get_scenarios(title)
        with open('stories.json', 'w') as outfile:
           json.dump(a.out, outfile)
        try:
            import SA2_my_stuff_json_to_html
        except ModuleNotFoundError:
            print('SA2_my_stuff_json_to_html.py was not found. Be sure you named it correctly.')
    if contentype == 'all':
        a.get_stories(title, actions)
        a.get_scenarios()
        with open('stories.json', 'w') as outfile:
            json.dump(a.out, outfile)
        try:
            import SA2_my_stuff_json_to_html
        except ModuleNotFoundError:
            print('SA2_my_stuff_json_to_html.py was not found. Be sure you named it correctly.')

    if contentype == 'publish':
        publish(title)
    if contentype == 'help':
        print('''
            Usage: python manage.py [publish/stories/scenarios] [title] [min_number_of_actions]

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

            Publishes a scenario which the given name. You must have it in stories.json in the directory

            --------------------
            Ex: python manage.py all is the default, gets everything in your account (stories with
            less than 10 actions are ignored) and makes the html
            --------------------

            (REMEMBER TO \"QUOTE\" the [title] option, or else it will give a nasty error.)
        ''')

def publish(title, url='https://prompts.aidg.club/prompts/create'):
    """
    Publish a scenario with the given name to the club.
    """
    # requests settings
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'})
    # variables
    variables = ['?savedraft=true', '?confirm=false#']
    with open('stories.json') as file:
        infile = json.load(file)
        for scenario in infile['scenarios']:
            if scenario['title'] == title:
                # prepare the rueqest
                #if 'Antiforgery' in session.cookies:
				# prepare tags
                nsfw = 'false'
                tags = ''
                for tag in scenario['tags']:
                    if tag == 'nsfw':
                        nsfw = 'true'
                    tags+=tag + ', '
                params = {
                    "Honey": "",
                    "Command.ParentId": "",
                    "Command.Title": scenario['title'],
                    "Command.Description": scenario['description'],
                    "Command.PromptContent": scenario['prompt'],
                    "Command.PromptTags": tags,
                    "Command.Memory": scenario['memory'],
                    "Command.Quests": "\n".join(scenario['quests']['quest']),
                    "Command.AuthorsNote": scenario['authorsNote'],
                    "Command.Nsfw": nsfw,
                    "ScriptZip": "",#filename
                    "WorldInfoFile": "",#filename
                }
                # prepare WI
                counter = 0
                for wi_entry in scenario['worldInfo']:
                    params[f'Command.WorldInfos[{counter}].Keys'] = wi_entry['keys']
                    params[f'Command.WorldInfos[{counter}].Entry'] = wi_entry['entry']
                    counter+=1
                res = session.get(url)
                body = bs4.BeautifulSoup(res.text)
                hidden_token = body.find('input', {'name': '__RequestVerificationToken'})
                params['__RequestVerificationToken'] = hidden_token.attrs['value']

                res = session.post(url + variables[1], data=params, headers=dict(Referer=url))
                # the url has the prompt number
                #prompt_number = body.find('a', text='Edit')
                #prompt_number = prompt_number.split('/')[1]
                print(f'Your prompt number is {res.url.split("/")[-1]}')
                # we have a number now
                #del params['Command.ParentId']
                #params['Command.Id'] = prompt_number
                #res = session.post(url + variables[1], data=params, headers=dict(Referer=url))
                print(res)
                # just in case, one scenario per request
                break

#session = requests.Session()
#session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 6.1;    WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'})
if __name__ == '__main__':
    download(sys.argv)
