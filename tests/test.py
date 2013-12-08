#!/usr/bin/env python
import argparse
import os
import subprocess
import sys


module_path = os.path.abspath(__file__)
test_dir = os.path.dirname(module_path)

def test_library(name):
    print 'Test %r...' % name
    # Determines the directory of the tested library:
    test_dir = os.path.join(os.path.dirname(module_path), library_name)
    test_dir = os.path.abspath(test_dir)

    # Switches directory:
    os.chdir(test_dir)
    print '* Switched to directory: %r' % test_dir

    # Installs dependencies:
    print '* Installing dependencies...'
    mkgyp_binary = os.path.join(os.path.dirname(module_path),
                                '..', 'makegyp', 'bin', 'mkgyp.py')
    mkgyp_binary = os.path.abspath(mkgyp_binary)
    subprocess.call('python %s install' % mkgyp_binary, shell=True)

    # Gyp:
    gyp_command = 'gyp --depth=. -f ninja test.gyp'
    print '* Run %r' % gyp_command
    subprocess.call(gyp_command, shell=True)

    # Compiles:
    ninja_command = 'ninja -C out/Debug/'
    print '* Run %r' % ninja_command
    subprocess.call(ninja_command, shell=True)

    # Run executable:
    executable_command = 'out/Debug/test'
    print '* Run %r' % executable_command
    subprocess.call(executable_command, shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Test makegyp formulas.'
    )
    parser.add_argument('library_names', metavar='library_name', nargs='*')

    if len(sys.argv) == 1:
        parser.print_help()

    args = parser.parse_args()
    library_names = set(args.library_names)
    if not library_names:
        library_names = set()
        for library_name in os.listdir(test_dir):
            path = os.path.join(test_dir, library_name)
            if os.path.isdir(path):
                library_names.add(library_name)

    for library_name in library_names:
        test_library(library_name)
        print '=' * 3
