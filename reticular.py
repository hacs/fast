from functools import wraps
import os
import sys
from argparse import ArgumentParser

_COMMAND_GROUPS = {}


class CLI(object):
    def __init__(self, message='Welcome!', directory='.', package='commands'):
        self.message = message
        self.directory = directory
        self.groups = {}
        self.interactive_mode = False

        for path in self.list(directory, package):
            if path not in _COMMAND_GROUPS:
                _COMMAND_GROUPS[path] = CommandGroup(path)

            group = _COMMAND_GROUPS[path]
            self.groups[group.name] = group

        try:
            self.base = self.groups.pop('base')
            self.base.load()
        except KeyError:
            raise RuntimeError('Base commands module not found in: %s.base' % package)

        self.load_all()

    def run(self, args=sys.argv[1:]):
        if len(args) < 1:
            if self.interactive_mode:
                return
            else:
                return self.interactive()

        try:
            os.chdir(self.directory)
            parsed_args = self.base.parser.parse_args(args)
            parsed_args = vars(parsed_args)
            func = parsed_args.pop('func')
            func(**parsed_args)
        except RuntimeError as e:
            print 'ERROR: ' + e.message

    def interactive(self):
        self.interactive_mode = True
        print self.message

        while True:
            try:
                args = raw_input('>> ').split()
                self.run(args)
            except EOFError:
                print
                exit(0)
            except KeyboardInterrupt:
                print
                exit(1)
            except SystemExit:
                pass

    def load_all(self):
        for name, cmd_group in self.groups.iteritems():
            cmd_group.load(self.base.parser_generator)

    @staticmethod
    def list(directory, package):
        return ("%s.%s" % (package, os.path.splitext(f)[0])
                for f in os.listdir(os.path.join(directory, package)) if f.endswith('.py') and not f.startswith('_'))


class CommandGroup(object):
    def __init__(self, path):
        self.name = path.split('.')[-1]
        self.path = path
        self._module = None
        self.parser = None
        self.parser_generator = None
        self.parsers = {}

    def load(self, subparsers=None):
        if not self._module:
            add_help = False if subparsers else True
            prog = ' '+self.name if subparsers else ''
            title = 'commands' if subparsers else 'base commands'
            metavar = '<command>' if subparsers else '<base_command>'

            self.parser = DefaultHelpParser(add_help=add_help, prog=sys.argv[0]+prog)
            self.parser_generator = self.parser.add_subparsers(title=title, metavar=metavar)

            global _current_group
            _current_group = self
            self._module = __import__(self.path, fromlist=[self.name])
            self.parser.description = self._module.__doc__

        if subparsers:
            subparsers.add_parser(self.name, parents=[self.parser], help=self._module.__doc__)

        return self._module


class DefaultHelpParser(ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


def argument(*args, **kwargs):
    def decorator(f):
        try:
            _get_parser(f).add_argument(*args, **kwargs)
        except KeyError:
            pass

        return f
    return decorator


def command(f):
    try:
        _get_parser(f)
    except KeyError:
        pass

    return f


def _get_parser(f):
    """
    Gets the parser for the command f, if it not exists it creates a new one
    """
    if f.__name__ not in _COMMAND_GROUPS[f.__module__].parsers:
        parser = _current_group.parser_generator.add_parser(f.__name__, help=f.__doc__, description=f.__doc__)
        parser.set_defaults(func=f)
        _COMMAND_GROUPS[f.__module__].parsers[f.__name__] = parser

    return _COMMAND_GROUPS[f.__module__].parsers[f.__name__]


def superuser(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if os.getuid() != 0:
            raise RuntimeError('To perform this command you need super user privileges.')

        return f(*args, **kwargs)
    return wrapper
