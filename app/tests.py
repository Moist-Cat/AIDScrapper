import json
import unittest
from unittest import skip

from bs4 import BeautifulSoup as bs

from .settings import BASE_DIR
from .client import AIDScrapper
from .models import Story, Scenario, ValidationError

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
    def tearDown(self):
        pass

    def test_story_validation(self):
        for story in self.stor_in:
            self.stories.add(story)
            self.assertEqual(story['actions'], self.stories.out[-1]['actions'])

    def test_scenario_validation(self):
        for scenario in self.scen_in:
            self.scenarios.add(scenario)
            self.assertEqual(scenario['prompt'], self.scenarios.out[-1]['prompt'])

    def test_invalid_title_raises(self):
        bad_title = self.stor_in[0]

        bad_title['title'] = 'not_sneed'
        self.stories.title = 'sneed'
        self.assertRaises(
            ValidationError,
            self.stories.add,
            bad_title
        )

        bad_title['title'] = 'sneed'
        self.stories.add(bad_title)

    def test_invalid_actions_raises(self):
        too_few_actions = self.stor_in[0]

        too_few_actions['actions'] = [1,2,3,4,5,6,7,8,9,10]

        self.assertRaises(
            ValidationError,
            self.stories.add,
            too_few_actions
        )

        too_few_actions['actions'].append(11)
        self.stories.add(too_few_actions)

    def duplicate_scenario_raises(self):
        duplicate_scenario = self.scen_in[0]

        self.scenarios.add(duplicate_scenario)

        self.assertRaises(
            ValidationError,
            self.stories.add,
            duplicate_scenario
        )

    def duplicate_story_raises(self):
        duplicate_story = self.stor_in[0]

        self.stories.add(duplicate_story)

        self.assertRaises(
            ValidationError,
            self.stories.add,
            duplicate_story
        )
@skip
class TestDowloadFiles(unittest.TestCase):

    def setUp(self):
        self.client = AIDScrapper()
        # you better have configured your secrets.json file.
        self.client.login()

    def tearDown(self):
        self.client.logout()

    def test_download(self):
        self.client.get_scenarios('Mormonism')
        self.client.get_stories('Mormonism')

class TestHtmlFiles(unittest.TestCase):

    def setUp(self):
        with open(TEST_DIR / 'test_stories.json') as file:
            self.stor_in = json.load(file)
        with open(TEST_DIR / 'test_scen.json') as file:
            self.scen_in = json.load(file)

    def tearDown(self):
        pass

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
            raise AssertionError('The story is not even there. Check the other tests.')

        self.assert_if_exists(body, story['title'])
        self.assert_if_exists(body, story['description'])
        self.assert_if_exists(body, story['authorsNote'])
        self.assert_if_exists(body, story['memory'])

        # all the actions were in a span, we get them all
        html_actions = html.findAll('span')
        matches = 0
        # Checking every action against ALL the other actions, to see if they
        # match since  they are not organized.
        for h_action in html_actions:
            for s_action in story['actions']:
                # One would argue that this could cause a false red flag 
                # but no one can do multiple actions in the same second (for now)
                # so it is fine.
                if h_action.attrs['title'] == s_action['createdAt']:
                    self.assertEqual(h_action.text.replace('\n', ''),
                                    s_action['text'].replace('\n', ''))
                    matches += 1

        # Discarded actions are counted, but we only care about 
        # the regular ones, so as long as every regular action is there...
        self.assertEqual(len(story['actions']), matches)

        for wi in story['worldInfo']:
            self.assert_if_exists(body, wi['keys'])
            self.assert_if_exists(body, wi['entry'])

def run():
    unittest.main(verbosity=5)
