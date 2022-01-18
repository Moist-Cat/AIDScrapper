import os
import glob
import json
import unittest
import unittest.mock
from unittest import skip

import requests
from bs4 import BeautifulSoup as bs

import aids.app.client
from aids.app.settings import BASE_DIR, ImproperlyConfigured
from aids.app.client import AIDScrapper
from aids.app.models import Story, Scenario, ValidationError
from aids.app.schemes import FrozenKeyDict
from aids.commands import makejson, makenai, alltohtml

TEST_DIR = BASE_DIR / 'app/test_files'

def do_regex(string):
    return f'[{string}]'

class TestModel(unittest.TestCase):
    def setUp(self):
        self.stories = Story()
        with open(TEST_DIR / 'test_stories.json') as file:
            self.stor_in = json.load(file)
        self.scenarios = Scenario()
        with open(TEST_DIR / 'test_scen.json') as file:
            self.scen_in = json.load(file)

    def test_story_validation(self):
        for story in self.stor_in:
            # It cannot raise a validation error
            self.stories.add(story)
            self.assertEqual(
                story['actions'],
                self.stories[story['title'], len(story['actions'])]['actions']
            )

    def test_scenario_validation(self):
        for scenario in self.scen_in:
            # It cannot raise a validation error
            self.scenarios.add(scenario)
            self.assertEqual(
                scenario['prompt'],
                self.scenarios[scenario['title']]['prompt']
            )

    def test_invalid_title_raises(self):
        bad_title = self.stor_in[0]
        self.stories('sneed', 1)
        
        bad_title['title'] = 'not_sneed'
        self.assertRaises(
            ValidationError,
            self.stories.update,
            {'sneed': bad_title}
        )
        
        bad_title.update({'title':'sneed'})
        self.stories.update({'sneed': bad_title})

    def test_invalid_actions_raises(self):
        too_few_actions = self.stor_in[0]

        too_few_actions['actions'] = [1,2,3,4,5,6,7,8,9,10]

        self.assertRaises(
            ValidationError,
            self.stories.update,
            {'sneed': too_few_actions}
        )

        too_few_actions['actions'].append(11)
        self.stories.update({'sneed': too_few_actions})

    def test_duplicate_scenario_raises(self):
        duplicate_scenario = self.scen_in[0]

        self.scenarios.add(duplicate_scenario)

        self.assertRaises(
            ValidationError,
            self.stories.update,
            {'sneed': duplicate_scenario}
        )

    def duplicate_story_raises(self):
        duplicate_story = self.stor_in[0]

        self.stories['sneed'] = duplicate_story

        self.assertRaises(
            ValidationError,
            self.stories.update,
            {'sneed': duplicate_story}
        )


class TestDataStructures(unittest.TestCase):

    def setUp(self):
        self.d = FrozenKeyDict([(1,2), (3,4)])
    
    def tearDown(self):
        del self.d

    def test_frozen_dict(self):
        self.d[4] = 4

        self.assertNotIn(4, self.d.keys())

        self.d[1] = 3

        self.assertEqual(3, self.d[1])

        self.d.update({7:3})

        self.assertNotIn(7, self.d.keys())

class TestReformatters(unittest.TestCase):

    def setUp(self):
        self.scenario_infile = TEST_DIR / 'The_Layover.scenario'
        self.json_outfile = TEST_DIR / 'test_Lay.json'
        
        self.json_infile = TEST_DIR / 'test_scen.json'
        self.scenario_outfile = TEST_DIR / 'test_naiscen.json'
    
    def tearDown(self):
        nai_file_names = glob.glob(str(TEST_DIR / '*.scenario'))
        for file_path in nai_file_names:
            if str(file_path) != str(self.scenario_infile):
                os.remove(file_path)
        try:
            os.remove(self.json_outfile)
        except FileNotFoundError:
            pass
        try:
            os.remove(self.scenario_outfile)
        except FileNotFoundError:
            pass

    def test_makejson(self):
        makejson(self.scenario_infile, self.json_outfile)

        with open(self.scenario_infile) as scen:
            in_f = json.load(scen)

        with open(self.json_outfile) as scen:
            out_f = json.load(scen)

        map(
            self.assertIn, (
                in_f['title'],
                in_f['prompt'],
                in_f['context'][0]['text']
            ), out_f[0].values()
        )

    def test_makenai(self):
        makenai(self.json_infile, self.scenario_outfile, single_files=False)
        
        with open(self.json_infile) as scen:
            in_f = json.load(scen)

        with open(self.scenario_outfile) as scen:
            for s in json.load(scen):
                if s['title'] == 'Snowed In':
                    out_f = s
                    break

        try:
            map(
                self.assertIn, (
                    in_f[0]['title'],
                    in_f[0]['prompt'],
                    in_f[0]['memory']
                ), out_f.values()
            )
        except UnboundLocalError as exc:
            raise AssertionError(
                'The scenario was not in the file. Possibly because the same reference' \
                'for an object was used and, when changed, updated all other objects. Use .copy()' \
                'to avoid this.'
            ) from exc
        
        makenai(self.json_infile, TEST_DIR)
        
        assert len(glob.glob(str(TEST_DIR / '*.scenario'))) > 60

# Schizo test cases to mock API calls so everything can be tested without 
# relying on their server
class TestLogin(unittest.TestCase):

    def setUp(self):

        self.client = AIDScrapper()
        self.client.session.get = unittest.mock.Mock
        self.client.session.post = unittest.mock.Mock

        self.client.session.post.json = lambda cls: {"data": {"login": {"accessToken": "dummyToken"}}}

    def test_get_login_token(self):
        
        token = self.client.get_login_token({"username": "dummy", "password": "dummypass"})

        self.assertEqual(token, "dummyToken")

    def test_regular_login(self):
        aids.app.client.settings.get_secret = lambda string: "dummy"

        self.client.login()

        self.client.session.headers["x-access-token"] == "dummyToken"

    def test_console_login(self):
        aids.app.client.__builtins__["input"] = lambda string: "dummy"
        aids.app.client.getpass.getpass = lambda string: "dummypass"

        aids.app.client.settings.get_secret = lambda string: exec("raise ImproperlyConfigured")

        self.client.login()

        self.client.session.headers["x-access-token"] == "dummyToken"

    def test_direct_login(self):
        self.client.login({"username": "dummy", "password": "dummypass"})

class ClientGetStories(unittest.TestCase):
    def setUp(self):

        self.client = AIDScrapper()
        self.client.session.get = unittest.mock.Mock
        self.client.session.post = unittest.mock.Mock





class TestHtmlFiles(unittest.TestCase):

    def setUp(self):
        with open(TEST_DIR / 'test_stories.json') as file:
            self.stor_in = json.load(file)
        with open(TEST_DIR / 'test_scen.json') as file:
            self.scen_in = json.load(file)

        alltohtml(
            TEST_DIR,
            'test_stories.json',
            'test_scen.json'
        )

    def tearDown(self):
        html_indexes = glob.glob(str(TEST_DIR / '**/*.html'), recursive=True)
        for file in html_indexes:
            os.remove(file)

    def assert_if_exists(self, body, element):
        # \"formatting\" is not compatible with the regex
        body = body.replace('[' and ']', '')
        element = element.replace('[' and ']', '')
        if element:
            self.assertRegex(body, do_regex(element))

    def test_scenario_properly_formatted_to_html(self):
        # We pick a scenario with quests, rem, WI, etc.. to
        # test everything with one file
        with open(TEST_DIR / 'scenarios/Eiyuu Senki: The World Conquest(Japan).html') as file:
            html = bs(file.read(), 'html5lib')
            body = html.text

        for scenario in self.scen_in:
            if scenario['title'] == 'Eiyuu Senki: The World Conquest(Japan)':
                # we got the scenario we were looking for.
                break
        else:
            raise AssertionError('The scenario is not even there. Check the other tests.')

        self.assert_if_exists(body, scenario['title'])
        self.assert_if_exists(body, scenario['description'])
        self.assert_if_exists(body, scenario['authorsNote'])
        self.assert_if_exists(body, scenario['memory'])
        self.assert_if_exists(body, scenario['prompt'])
        for wi in scenario['worldInfo']:
            self.assert_if_exists(body, wi['keys'])
            self.assert_if_exists(body, wi['entry'])
        for quest in scenario['quests']:
            self.assert_if_exists(body, quest['quest'])

    def test_story_properly_formatted_to_html(self):
        # We pick a scenario with quests, rem, WI, etc.. to
        # test everything with one file
        with open(TEST_DIR / 'stories/Eiyuu Senki: The World Conquest.html') as file:
            html = bs(file.read(), 'html5lib')
            body = html.text

        for story in self.stor_in:
            if story['title'] == 'Eiyuu Senki: The World Conquest':
                # we got the story we were looking for.
                break
        else:
            raise AssertionError('The story is not even there.')

        self.assert_if_exists(body, story['title'])
        self.assert_if_exists(body, story['description'])
        self.assert_if_exists(body, story['authorsNote'])
        self.assert_if_exists(body, story['memory'])

        # all the actions are in a span, we get them all
        html_actions = html.findAll('span')
        assert html_actions
        matches = 0
        # Checking every action against ALL the other actions, to see if they
        # match since  they are not organized.
        for h_action in html_actions:
            for s_action in story['actions']:
                # One could argue that this could cause a false red flag 
                # but no one can do multiple actions in the same second (for now)
                # so it is fine.
                if h_action.attrs['date'] == s_action['createdAt']:
                    self.assertEqual(h_action.text.strip().replace('\n', ''),
                                    s_action['text'].strip().replace('\n', ''))
                    matches += 1

        self.assertEqual(matches, len(story['actions']))

        for wi in story['worldInfo']:
            self.assert_if_exists(body, wi['keys'])
            self.assert_if_exists(body, wi['entry'])
    
    def test_subscen_properly_structured(self):
        alltohtml(TEST_DIR, scenario_outfile='Family.json')
        # just check the path
        with open(f'{TEST_DIR}/scenarios/Family Matters/Mom/Duty Calls(Mom).html', 'r') as file: pass
        # check the files one by one
        with open(f'{TEST_DIR}/scen_index.html') as file:
            html = bs(file.read(), 'html5lib')
            assert html.a.attrs['href'] == "scenarios/Family Matters.html"
        with open(f'{TEST_DIR}/scenarios/Family Matters.html') as file:
            html = bs(file.read(), 'html5lib')
            assert html.a.attrs['href'] == "Family Matters/Mom.html"
        with open(f'{TEST_DIR}/scenarios/Family Matters/Mom.html') as file:
            html = bs(file.read(), 'html5lib')
            assert html.a.attrs['href'] == "Mom/Duty Calls(Mom).html"

def run():
    unittest.main(verbosity=5)
