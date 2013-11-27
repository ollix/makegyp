import argparse
import re


class ArgumentParser(argparse.ArgumentParser):
    # A list of matched patterns. The list should contain three-value tuples
    # where the first defines the compiled reqular expression pattern,
    # the second defines a regular expression sub to extract the arguments,
    # and the last indicates the corresponded buid type.
    patterns = list()

    def __init__(self, *args, **kwargs):
        self.__args = dict()
        # Compiles patterns:
        patterns = list()
        for pattern, repl, build_type in self.__class__.patterns:
            patterns.append((re.compile(pattern), repl, build_type))
        self.__class__.patterns = patterns

        super(ArgumentParser, self).__init__(*args, **kwargs)

    def add_argument(self, *args, **kwargs):
        super(ArgumentParser, self).add_argument(*args, **kwargs)
        self.__args[args] = kwargs

    def match_pattern(self, args):
        for pattern in self.patterns:
            if re.match(pattern[0], args):
                return pattern

    def parse_args(self, arg_string):
        """Parse the argument string.

        The specified arg_string must conform to one of the defined patterns.
        A normal Namespace object is returned along the current build type.
        """
        # Finds the real argument string will be passed to parent's
        # parse_args() by checking acceptble patterns.
        arg_string = arg_string.strip()
        pattern = self.match_pattern(arg_string)
        if pattern:
            args = re.sub(pattern[0], pattern[1], arg_string).split()
        else:
            print '%r cannot parse argument %r' % (self.__class__.__name,
                                                   arg_string)
            exit(1)

        # Reorders the arguments by moving all pure arguments to the back:
        reversed_args = list()
        for arg_names in self.__args:
            arg_options = self.__args[arg_names]
            for arg_name in arg_names:
                reversed_args.append((arg_name, arg_options))
        reversed_args.sort(reverse=True)

        new_optional_args = list()
        new_pure_args = list()
        arg_index = 0
        while (arg_index < len(args)):
            arg = args[arg_index]
            is_optional_arg = False
            for arg_name, options in reversed_args:
                if arg_name.startswith('-') and arg.startswith(arg_name):
                    # The argument is an option. Now check how many
                    # arguments needed consumed.
                    is_optional_arg = True
                    new_optional_args.append(arg)
                    arg_index += 1

                    # If the action is 'store_true' or 'store_false', only
                    # the current argument is consumed.
                    if 'action' in options and \
                       options['action'].startswith('store_'):
                        break  # only the current

                    # The option consumes at least 1 argument:
                    nargs = options['nargs'] if 'nargs' in options else 1
                    if nargs == '*' or nargs == '+':
                        # Skips argument until found the next optional argument:
                        while arg_index < len(args):
                            next_arg = args[arg_index]

                            next_arg_is_option = False
                            for arg_name, options in reversed_args:
                                if arg_name.startswith('-') and \
                                   next_arg.startswith(arg_name):
                                    next_arg_is_option = True
                                    break
                            else:
                                new_optional_args.append(args[arg_index])
                                arg_index += 1

                            if next_arg_is_option:
                                break
                    else:
                        if arg != arg_name:
                            nargs -= 1
                        for i in range(nargs):
                            new_optional_args.append(args[arg_index])
                            arg_index += 1
                    break
            if is_optional_arg:
                continue

            # The current argument is not an option. Just put it to the end of
            # the new list to match the original order.
            if not is_optional_arg:
                new_pure_args.append(arg)
                arg_index += 1

        args = new_optional_args + new_pure_args

        # Removes duplicated values for list objects:
        result = super(ArgumentParser, self).parse_args(args)
        for key, value in result._get_kwargs():
            if isinstance(value, list):
                new_value = list(set(value))
                new_value.sort()
                setattr(result, key, new_value)

        # Adds the build type to the parsed arguments
        result.build_type = pattern[2]
        return result


class ArchiverArgumentParser(ArgumentParser):
    patterns = [(r'^libtool: link:\s+ar\s+(.*)$', r'\1', 'link'),
                (r'^(.+?/)*ar\s+(.*)$', r'\2', 'link')]  # CMake's link.txt

    def __init__(self, *args, **kwargs):
        super(ArchiverArgumentParser, self).__init__(*args, **kwargs)
        self.add_argument('options')
        self.add_argument('output')
        self.add_argument('sources', metavar='source', nargs='+')


class GccArgumentParser(ArgumentParser):
    patterns = [(r'^(.*?--mode=compile\s)?\s?gcc\s(.*?)$', r'\2', 'compile'),
                (r'^(.*?--mode=link\s)?\s?gcc\s(.*?)$', r'\2', 'link'),
                (r'^libtool:\s+compile:\s+gcc\s+(.*)$', r'\1', 'compile'),
                (r'^libtool:\s+link:\s+gcc\s+(.*)$', r'\1', 'link'),
                (r'^libtool\s+(.+)$', r'\1', 'link')]

    def __init__(self, *args, **kwargs):
        super(GccArgumentParser, self).__init__(*args, **kwargs)
        self.add_argument('-c', action='store_true')
        self.add_argument('-compatibility_version')
        self.add_argument('-current_version')
        self.add_argument('-f', action='append')
        self.add_argument('-g', action='store_true')
        self.add_argument('-dynamiclib', action='store_true')
        self.add_argument('-D', action='append', dest='defines')
        self.add_argument('-l', action='append', dest='libs')
        self.add_argument('-L', action='append', dest='linkers')
        self.add_argument('-iquote', action='append')
        self.add_argument('-I', action='append', dest='include_dirs')
        self.add_argument('-install_name')
        self.add_argument('-M')
        self.add_argument('-MF')
        self.add_argument('-MT')
        self.add_argument('-no-undefined', action='store_true')
        self.add_argument('-o', dest='output')
        self.add_argument('-O')
        self.add_argument('-static', action='store_true')
        self.add_argument('-Q')
        self.add_argument('-rpath')
        self.add_argument('-version-info')
        self.add_argument('-W')
        self.add_argument('sources', metavar='source', nargs='*')

    def parse_args(self, *args, **kwargs):
        parsed_args = super(GccArgumentParser, self).parse_args(*args, **kwargs)

        if not parsed_args.sources and len(parsed_args.c) == 1:
            parsed_args.sources = parsed_args.c

        if parsed_args is not None:
            if parsed_args.dynamiclib or parsed_args.linkers:
                parsed_args.build_type = 'link'

        return parsed_args


if __name__ == '__main__':
    args = ''
    parser = GccArgumentParser()
    pattern = parser.match_pattern(args)
    if pattern:
        print 'Matched pattern:', pattern[0].pattern
        print 'Matched sub:', re.sub(pattern[0], pattern[1], args)
    else:
        print 'Not Matched'
