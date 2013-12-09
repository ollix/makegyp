import argparse
import os
import sys

from makegyp.core import utils


def create(args):
    print 'create:', args

def edit(args):
    print 'edit:', args

def install(args):
    library_names = set(args.library_names)

    # Determines the current directory:
    curdir = os.path.abspath(os.path.curdir)

    # Adds libraries specified in `gyp_deps.txt` at the current directory:
    gyp_deps_path = os.path.join(curdir, 'gyp_deps.txt')
    if os.path.isfile(gyp_deps_path):
        gyp_deps_file = file(gyp_deps_path, 'r')
        for line in gyp_deps_file:
            library_name = line.split('#', 1)[0].strip()
            if library_name:
                library_names.add(library_name)
        gyp_deps_file.close()

    if not library_names:
        print 'No library is specified. You can specify libraries as ' \
        'arguments or list them in the `gyp_deps.txt` file at the current ' \
        'directory.'
        exit(1)

    # Creates the gyp_deps subdirectory at the current directory for keeping
    # installed libraries:
    dest_dir = args.dest if args.dest else os.path.join(curdir, 'gyp_deps')
    dest_dir = os.path.abspath(dest_dir)
    try:
        os.makedirs(dest_dir)
    except OSError as error:
        # Ignores error if the deps directory already exists.
        if not error.errno == 17:
            raise error

    for library_name in library_names:
        os.chdir(curdir)
        utils.install_formula(library_name, dest_dir)

    print '%r %s installed at %r' % (sorted(library_names),
                                     'is' if len(library_names) == 1 else 'are',
                                     dest_dir)


# Command configuration
parser = argparse.ArgumentParser(
    description='Generates existing C or C++ library with GYP support.'
)
subparsers = parser.add_subparsers(title='subcommands')

# Subcommand: create
parser_create = subparsers.add_parser('create', help='create a formula')
parser_create.set_defaults(func=create)

#Subcommand: edit
parser_edit = subparsers.add_parser('edit', help='edit a formula')
parser_edit.set_defaults(func=edit)

# Subcommand: install
parser_install = subparsers.add_parser('install', help='install a library')
parser_install.add_argument('-d', '--dest',
                            help='directory to install the library')
parser_install.add_argument('-t', '--test', action='store_true',
                            help='test the building process')
parser_install.add_argument('library_names', metavar='library_name', nargs='*')
parser_install.set_defaults(func=install)


def execute_from_command_line():
    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()
    args.func(args)
