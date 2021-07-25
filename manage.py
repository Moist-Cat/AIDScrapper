import requests
import json
import sys
import glob
import getpass

import bs4

from mystuff_scrapper import AIDStuffGetter


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


    if contentype not in ('publish', 'makenai', 'help'):
        a = AIDStuffGetter()
    if contentype == 'stories':
        a.get_stories(title, actions)
        with open('stories.json', 'w') as outfile:
            json.dump(a.out, outfile)
        try:
            import mystuff_json_to_html
        except ModuleNotFoundError:
            print('mystuff_json_to_html.py was not found. Make sure you named it correctly.')
    if contentype == 'scenarios':
        a.get_scenarios(title)
        with open('stories.json', 'w') as outfile:
           json.dump(a.out, outfile)
        try:
            import mystuff_json_to_html
        except ModuleNotFoundError:
            print('mystuff_json_to_html.py was not found. Make sure you named it correctly.')
    if contentype == 'all':
        a.get_stories(title, actions)
        a.get_scenarios()
        with open('stories.json', 'w') as outfile:
            json.dump(a.out, outfile)
        try:
            import mystuff_json_to_html
        except ModuleNotFoundError:
            print('mystuff_json_to_html.py was not found. Make sure you named it correctly.')

    if contentype == 'publish':
        publish(title)
    
    if contentype == 'makenai':
        story_to_json()
    
    if contentype == 'fenix':
        try:
            with open('stories.json') as file:
                data = json.load(file)
                a.upload_in_bulk(data)
        except FileNotFoundError:
            scenarios = a.get_scenarios()
            with open('stories.json', 'w') as outfile:
                json.dump(a.out, outfile)
            a.upload_in_bulk(a.out['scenarios'])
    if contentype == 'help':
        print('''
Usage: python manage.py [publish/stories/scenarios/makenai] [title] [min_number_of_actions]

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
Ex: python manage.py all is the default, gets everything in your account (stories with
less than 10 actions are ignored) and makes the html
--------------------

(REMEMBER TO \"QUOTE\" the [title] option, or else it will give a nasty error.)
        ''')

def get_secret_token(session, url):
    res = session.get(url)
    body = bs4.BeautifulSoup(res.text)
    hidden_token = body.find('input', {'name': '__RequestVerificationToken'})
    return hidden_token.attrs['value']

def make_club_account(session):
    url = 'https://prompts.aidg.club/user/register'

    params = {
             'ReturnUrl': '',
             'Honey': '',
             'Username': input('Username: '),
             'Password': getpass.getpass('Password: '),
             'PasswordConfirm': getpass.getpass('Password(Again): ')
    }

    params['__RequestVerificationToken'] = get_secret_token(session, url)

    res = session.post(url, data=params,
                       headers=dict(Referer=url))
    if res.status_code == 200:
        print('Successfully registered')
    else:
       print('Uh-oh...', res.text)


def login_into_the_club(session, params={}):
    url = 'https://prompts.aidg.club/user/login'
    
    if not params:
        params = {
                 'ReturnUrl': '',
                 'Honey': '',
                 'Username': input('Username: '),
                 'Password': getpass.getpass('Password: ')
        }

    params['__RequestVerificationToken'] = get_secret_token(session, url)

    res = session.post(url, data=params,
                       headers=dict(Referer=url))
    if res.status_code == 200:
        print('Successfully loged-in')
    else:
       print('Uh-oh...', res.text)

def publish(title, url='https://prompts.aidg.club/prompts/create'):
    """
    Publish a scenario with the given name to the club.
    """
    # requests settings
    session = requests.Session()
    session.headers.update({'User-Agent':
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) '\
        'Gecko/20100101 Firefox/20.0'})
    print('Already have a club account?')
    print('\n[1] Register')
    print('\n[2] Log-in')

    selection = input('>')
    if selection == "1":
        make_club_account(session)
    else:
        login_into_the_club(session)
    # variables
    variables = ('?savedraft=true', '?confirm=false#')
    with open('stories.json') as file:
        infile = json.load(file)
    for scenario in infile['scenarios']:
        if scenario['title'] == title:
            # prepare the request
            # prepare tags
            nsfw = 'false'
            tags = ', '.join(tag for tag in scenario['tags'])
            for tag in tags:
                if tag == 'nsfw':
                    nsfw = 'true'

            try:
                quests = "\n".join(scenario['quests']['quest'])
            except KeyError:
                quests = []

            params = {
                "Honey": "",
                "Command.ParentId": "",
                "Command.Title": scenario['title'],
                "Command.Description": scenario['description'],
                "Command.PromptContent": scenario['prompt'],
                "Command.PromptTags": tags,
                "Command.Memory": scenario['memory'],
                "Command.Quests": quests,
                "Command.AuthorsNote": scenario['authorsNote'],
                "Command.Nsfw": nsfw,
                "ScriptZip": "",#filename
                "WorldInfoFile": "",#filename
            }
            # prepare WI
            counter = 0
            try:
                for wi_entry in scenario['worldInfo']:
                    params[f'Command.WorldInfos[{counter}].Keys'] = wi_entry['keys']
                    params[f'Command.WorldInfos[{counter}].Entry'] = wi_entry['entry']
                    counter+=1
            except KeyError:
                pass

            # we need the secret token that is generated
            # in every request to post the data.
            res = session.get(url)
            body = bs4.BeautifulSoup(res.text)
            hidden_token = body.find('input', {'name': '__RequestVerificationToken'})
            params['__RequestVerificationToken'] = hidden_token.attrs['value']

            res = session.post(url + variables[1], data=params, headers=dict(Referer=url))
            print(f'Your prompt number is {res.url.split("/")[-1]}')
            # just in case, one scenario per request
            break

def context_to_an_and_memory(json_data):
    # reformat the context as memory and AN
    # usually, 0 is memory whilst 1 is AN. But as 
    # the russians say, \"Trust, but verify\"
    for data in json_data['context']:
        if not data['contextConfig']['reservedTokens']:
            json_data['memory'] = data['text']

        elif data['contextConfig']['reservedTokens'] == 2048:
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


def story_to_json():
    nai_file_name = glob.glob('*.scenario')
    scenario = {'scenarios': []}
    
    
    for name in nai_file_name:
        with open(name) as file:
            json_data = json.load(file)
        

        context_to_an_and_memory(json_data)
        
        del json_data['context']
        
        # lorebook to worldInfo is way easier
        json_data['worldInfo'] = json_data['lorebook']['entries']
        # and, a smol detail
        for entry in json_data['worldInfo']:
           entry['entry'] = entry['text']
           del entry['text']
        
        # required param
        json_data['quests'] = []
        
        
        # Extra details wont matteron the payload, as long we have 
        # the required info, so I will not bother on cleaing the NAI 
        # specific details form the json.
        scenario['scenarios'].append(json_data)
        
        print(f'Your NAI scenario \"{json_data["title"]}\" was successfully ' \
               're-formatted. You can publish it in the club whenever you want to.')
    with open('stories.json', 'w') as file:
        json.dump(scenario, file)
        

if __name__ == '__main__':
    download(sys.argv)
