# AIDScrapper

Tweaked version of ScriptAnon stuff getter.

Added/Changed functions:

	--publish
		publish scenario form story.json to the Club, so you do not need to copy-paste.
	--selective save: 
		Save the stories that actually had content by giving a min number of actions for saving a story.
		Also, you have the chance to save an unique scenario or stories with the same name.
	--neater save:
		When the scenarios are converted form JSON to html you do not get a mess of ids, but 
		a human-friendly, folder-divided directory with all your stories placed in a intuitive way. Is also integrated with 
		scriptanon index.

# Requirements

Needs BeautifulSoup and requests for scrapping.
pip install -r requirements.txt to install all dependencies.

After install type "python manage.py help" for commands

