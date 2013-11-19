import argparse
import sys


def create(args):
    print 'create:', args

def edit(args):
    print 'edit:', args

def install(args):
    print 'install', args


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
parser_install.set_defaults(func=install)


parser.add_argument('library_name')

def execute_from_command_line():
    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()
    args.func(args)
