import re

from makegyp.core import argparser


class Parser(object):

    def __init__(self):
        self.parse_result = list()


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

    def _handle_make_mode_args(self, args):
        self.make_mode = re.sub(self.make_mode_re, r'\1', args)
        print 'MAKE MODE:', self.make_mode

    def _handle_start_make_args(self, args):
        directory_name = re.sub(self.start_make_re, r'\1', args)
        print 'START MAKE:', directory_name

    def _handle_unknown_args(self, args):
        pass

    def parse_configure(self, source):
        self.parse_result = list()

        for line in source.split('\n'):
            if not self.config_file_re.match(line):
                continue

            config_file = re.sub(self.config_file_re, r'\1', line)
            if config_file:
                self.parse_result.append(config_file)

        return self.parse_result

    def parse_make(self, source):
        self.parse_result = list()
        self.make_mode = None
        self.previous_arg_type = None

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

        return self.parse_result


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
        elif arg_type == 'link':
            args = re.sub(self.link_re, r'\1', args)
            args = self.gcc_parser.parse_args(args)
            print 'LINK: %s > %r' % (args.output, args.linked_files)
            print args
