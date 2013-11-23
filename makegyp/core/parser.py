import os
import re

from makegyp.core import argparser
from makegyp.core import gyp


class Parser(object):
    pass


class MakeParser(Parser):
    # Regular expression patterns:
    compile_re = '^\s+CC\s+(\w+)'
    # For extracting generated config files
    config_file_re = re.compile(r'config.status:\screating\s(.*config\.h)')
    # End make: looks like "make[3]: Nothing to be done for `all-am'"
    end_make_re = re.compile(r'^make\[\d\]:\sNothing to be done')
    link_re = re.compile(r'^\s+CCLD\s+(\w+)')
    # Make mode: for example, all-am, all-recursive
    make_mode_re = re.compile(r'^.+?/make\s+([a-z\-]+)$')
    # Start make: looks like "Making all in something"
    start_make_re = re.compile(r'^Making all in ([\.\/\w]+)')

    def _get_arg_type(self, message):
        """Accept a single-line message and returns the corresponded type."""

        # Start make:
        if re.match(self.start_make_re, message):
            return 'start_make'
        # End make:
        elif re.match(self.end_make_re, message):
            return 'end_make'
        # Make mode:
        elif re.match(self.make_mode_re, message):
            return 'make_mode'

    def _handle_end_make_args(self, args):
        print 'END_MAKE'

        self.current_directory = os.path.relpath(
            os.path.join(self.current_directory, '..'))

    def _handle_make_mode_args(self, args):
        self.make_mode = re.sub(self.make_mode_re, r'\1', args)
        print 'MAKE MODE:', self.make_mode

    def _handle_start_make_args(self, args):
        directory_name = re.sub(self.start_make_re, r'\1', args)


        path = os.path.join(self.current_directory, directory_name)
        if not os.path.isdir(path):
            path = os.path.join(self.current_directory, '..', directory_name)
        path = os.path.relpath(path)

        print 'START MAKE:', path

        self.current_directory = path

    def _handle_unknown_args(self, args):
        pass

    def get_config_files(self, configure_output):
        config_files = list()

        for line in configure_output.split('\n'):
            if not self.config_file_re.match(line):
                continue

            config_file = re.sub(self.config_file_re, r'\1', line)
            if config_file:
                config_files.append(config_file)

        return config_files

    def get_targets(self, make_output):
        """Parse the make output and returns a list of targets."""
        self.current_directory = ''
        self.make_mode = None
        self.previous_arg_type = None
        self.targets = list()
        self.compiled_objects = dict()

        for line in make_output.split('\n'):
            arg_type = self._get_arg_type(line)
            if arg_type == 'start_make':
                self._handle_start_make_args(line)
            elif arg_type == 'end_make':
                self._handle_end_make_args(line)
            elif arg_type == 'make_mode':
                self._handle_make_mode_args(line)
            else:
                self._handle_unknown_args(line)

            self.previous_arg_type = arg_type

        for target in self.targets:
            print target.dump()

        return self.targets


class LibtoolParser(MakeParser):
    gcc_parser = argparser.GccArgumentParser()

    compile_re = re.compile(r'^libtool: compile:\s+gcc\s+?(.+?)$')
    link_re = re.compile(r'^.+?libtool\s.*?\s--mode=link\s+?gcc\s+?(.*?)$')

    def _get_arg_type(self, message):
        arg_type = super(LibtoolParser, self)._get_arg_type(message)
        if arg_type:
            return arg_type
        elif re.match(self.compile_re, message):
            return 'compile'
        elif re.match(self.link_re, message):
            return 'link'

    def __get_compiled_object(self, filename):
        for dirname, compiled_objects in self.compiled_objects.items():
            for compiled_object in compiled_objects:
                if compiled_object.MT == filename:
                    compiled_object.dirname = dirname
                    return compiled_object

    def _handle_unknown_args(self, args):
        arg_type = self._get_arg_type(args)

        if arg_type == 'compile':
            args = re.sub(self.compile_re, r'\1', args)
            args = self.gcc_parser.parse_args(args)
            print 'COMPILE: %s > %s' % (args.source,  args.output)
            print args

            if self.current_directory not in self.compiled_objects:
                self.compiled_objects[self.current_directory] = []
            self.compiled_objects[self.current_directory].append(args)

        elif arg_type == 'link':
            args = re.sub(self.link_re, r'\1', args)
            args = self.gcc_parser.parse_args(args)
            print 'LINK: %s > %r' % (args.output, args.linked_files)
            print args

            self.current_directory = os.path.relpath(
                os.path.join(self.current_directory, '..'))

            target_name = re.sub(r'^(lib)?(.+?)(\.\w+)$', r'\2', args.output)
            target = gyp.Target(args.output)
            for linked_file in args.linked_files:
                if linked_file.endswith('.la'):
                    target.add_dependency_by_path(linked_file)
                elif linked_file.endswith('.lo'):
                    compiled_object = self.__get_compiled_object(linked_file)
                    source = os.path.join(compiled_object.dirname,
                                          compiled_object.source)
                    target.sources.add(source)
                    # Updates include_dirs:
                    for include_dir in compiled_object.include_dirs:
                        include_dir = os.path.join(compiled_object.dirname,
                                                   include_dir)
                        include_dir = os.path.relpath(include_dir)
                        target.include_dirs.add(include_dir)
                    # Updates defines:
                    target.defines.update(compiled_object.defines)

            self.targets.append(target)
