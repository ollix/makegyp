import os
import re

from makegyp.core import argparser


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

    def parse_configure(self, source):
        result = list()

        for line in source.split('\n'):
            if not self.config_file_re.match(line):
                continue

            config_file = re.sub(self.config_file_re, r'\1', line)
            if config_file:
                result.append(config_file)

        return result

    def parse_make(self, source):
        self.current_directory = ''
        self.make_mode = None
        self.previous_arg_type = None
        self.targets = list()
        self.compiled_objects = dict()

        for line in source.split('\n'):
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

        print '\n\n'
        import json
        print json.dumps(self.targets, sort_keys=True, indent=4)
        return self.targets


class LibtoolParser(MakeParser):
    gcc_parser = argparser.GccArgumentParser()

    compile_re = re.compile(r'^libtool: compile:\s+gcc\s+?(.+?)$')
    link_re = re.compile(r'^.+?libtool\s.*?\s--mode=link\s+?gcc\s+?(.*?)$')

    def __get_arg_type(self, message):
        if re.match(self.compile_re, message):
            return 'compile'
        elif re.match(self.link_re, message):
            return 'link'

    def _handle_unknown_args(self, args):
        arg_type = self.__get_arg_type(args)

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

            target = {}
            target['name'] = re.sub(r'^(lib)?(.+?)(\.\w+)$', r'\2', args.output)
            target['dependencies'] = []
            target['include_dirs'] = set()
            target['defines'] = set()
            target['sources'] = []
            for linked_file in args.linked_files:
                if linked_file.endswith('.la'):
                    library_name = os.path.basename(linked_file)
                    library_name = re.sub(r'^(lib)(.+?)(\.\w+)$', r'\2', library_name)
                    target['dependencies'].append(library_name)
                elif linked_file.endswith('.lo'):
                    for directory, objs in self.compiled_objects.items():
                        for obj in objs:
                            if obj.MT == linked_file:
                                source = os.path.join(directory, obj.source)
                                target['sources'].append(source)

                                for include_dir in obj.include_dirs:
                                    include_dir = os.path.join(directory,
                                                  include_dir)
                                    include_dir = os.path.relpath(include_dir)
                                    target['include_dirs'].add(include_dir)
                                break
                            if hasattr(obj, 'D'):
                                target['defines'].update(obj.D)

            if '.' in target['include_dirs']:
                target['include_dirs'].remove('.')
            target['include_dirs'] = list(target['include_dirs'])
            target['include_dirs'].sort()

            target['defines'] = list(target['defines'])
            target['defines'].sort()

            self.targets.append(target)

