import argparse
import os
import sys

from makegyp.core import utils


def create(args):
    print 'create:', args

def edit(args):
    print 'edit:', args

def install(args):
    formulas = set(args.formulas)

    # Initializes included gyp files.
    include_gyp_files = set()
    if args.includes is not None:
        for gyp_file in args.includes:
            include_gyp_files.add(os.path.abspath(gyp_file))

    # Determines the current directory:
    curdir = os.path.abspath(os.path.curdir)

    # Adds libraries specified in `gyp_deps.txt` at the current directory:
    gyp_deps_path = os.path.join(curdir, 'gyp_deps.txt')
    if os.path.isfile(gyp_deps_path):
        gyp_deps_file = file(gyp_deps_path, 'r')
        config = eval(gyp_deps_file.read())
        gyp_deps_file.close()
        if 'dependencies' in config and \
           isinstance(config['dependencies'], list):
            for dependency in config['dependencies']:
                formulas.add(dependency)
        if 'includes' in config and isinstance(config['includes'], list):
            base_dir = os.path.dirname(os.path.abspath(gyp_deps_path))
            for include in config['includes']:
                include_gyp_files.add(os.path.join(base_dir, include))

    if not formulas:
        print 'No formula is specified. You can specify formulas as ' \
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

    for formula in formulas:
        os.chdir(curdir)
        utils.install_formula(formula, dest_dir, args.prefix,
                              include_gyp_files=include_gyp_files)

    print '%r %s installed at %r' % (sorted(formulas),
                                     'is' if len(formulas) == 1 else 'are',
                                     dest_dir)


# Command configuration
parser = argparse.ArgumentParser(
    description='Generates existing C or C++ library with GYP support.'
)
subparsers = parser.add_subparsers(title='subcommands')

# Subcommand: install
parser_install = subparsers.add_parser('install', help='install libraries')
parser_install.add_argument('-d', '--dest',
                            help='directory to install libraries')
parser_install.add_argument('-i', '--include', dest='includes', action='append',
                            metavar='gypi', help='include other gyp files in ' \
                                                 'generated gyp file')
parser_install.add_argument('-p', '--prefix', dest='prefix', default='',
                            help='gyp file prefix')
parser_install.add_argument('formulas', metavar='formula', nargs='*')
parser_install.set_defaults(func=install)


def execute_from_command_line():
    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()
    args.func(args)
