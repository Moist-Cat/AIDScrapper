# AIDScrapper

Based off a small script made by an Anonymous user. Now it's a full featured client which supports not only [AID][0] but also [Holo][0]. Alternatively, it can transform AID scenario objects in .scenario files for compatibility with the different AI Dynamic Storytelling platforms, specially [NAI][2]
The json files can be transformed into .html for better readability although that's not the main purpose of this tool - you should upload it to one of the supported websites to use the stories.

# Requirements
To install all requirements, use the following snippet after installing python on your machine.

    pip install -r requirements.txt

Or just use:

    pip install aids


# Usage
To install the whole thing. You can manage it directly from console. Use:

    aids help

Afterwards for a list of commands or:

    aids-windows.bat help

If you use Windows.

You can also use the package directly via:

    python3 -m aids help

Or in outside the package directory with:

    python aids/manage.py help

# Testing
If you feel like messing around with the code make sure none of the tests are failing using the *test* command. It uses pytest if you have it installed or unittest as a fallback.

[0]: https://play.aidungeon.io
[1]: https://www.writeholo.com
[2]: https://novelai.net/
