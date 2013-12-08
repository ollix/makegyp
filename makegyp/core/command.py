import argparse
import imp
import os
import sys

import makegyp


def create(args):
    print 'create:', args

def edit(args):
    print 'edit:', args

def install(args):
    library_names = args.library_names
    package_root = os.path.dirname(makegyp.__file__)
    formula_root = os.path.join(package_root, 'formula')

    # Creates the gyp_deps subdirectory at the current directory for keeping
    # installed libraries:
    deps_dir = os.path.join(os.path.curdir, 'gyp_deps')
    deps_dir = os.path.abspath(deps_dir)
    try:
        os.mkdir(deps_dir)
    except OSError as error:
        # Ignores error if the deps directory already exists.
        if not error.errno == 17:
            raise error

    for library_name in library_names:
        try:
            find_module_result = imp.find_module(library_name, [formula_root])
        except ImportError:
            print 'No matched formula found for library:', library_name
            exit(1)

        module = imp.load_module(library_name, *find_module_result)
        class_ = getattr(module, library_name.title())
        instance = class_(deps_dir)
        instance.install()


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
parser_install.add_argument('-d', '--dest', help='path to install the library')
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
