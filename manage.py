import sys
from typing import List
import argparse

import aids.commands as commands
from aids.commands import command_arg_dict

def get_command(argv: List[str] = sys.argv[1:]):

    parser = argparse.ArgumentParser(
        description='Command line utilily for the "aids" module'
    )
    parser.add_argument(
        'command', metavar='C', type=str, help='main command'
    )
    parser.add_argument(
        '-t', '--title', type=str, default='', help='object title'
    )
    parser.add_argument(
        '-a', '--actions', type=int, default=0, help='stories minimal lenght in actions'
    )
    parser.add_argument(
        '-p', '--platform', type=str, help='platform where the client should point to'
    )
    
    cmd = parser.parse_args(argv)


    # (TODO) I have to figure out a way to call the commands without using black magic.
    if cmd.platform:
        # to match class names
        cmd.platform = cmd.platform.lower().capitalize()
        try:
            args = command_arg_dict[cmd.platform][cmd.command]
            required_args = [{'title': cmd.title, 'actions': cmd.actions}.get(arg) for arg in args]

        except KeyError:
            print('Unrecognized command.')
            return

        try:
            # initialized in site
            platform = getattr(commands, cmd.platform)()
            command = getattr(platform, cmd.command)
        except AttributeError:
            print('Unrecognized command. Are you using a command meant for other platform?')
            return
        command(*required_args)

    else:
        try:
            main_command = getattr(commands, cmd.command)
        except AttributeError:
            print(f'{cmd.command} is not a valid command. Did you forget to add the -p flag?')
        else:
            # to the date, all other commands do not require args
            main_command()

if __name__ == '__main__':
    get_command()
