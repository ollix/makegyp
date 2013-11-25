import argparse


class ArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        self.__args = dict()
        super(ArgumentParser, self).__init__(*args, **kwargs)

    def add_argument(self, *args, **kwargs):
        super(ArgumentParser, self).add_argument(*args, **kwargs)

        # if hasattr(self, 'args'):
        self.__args[args] = kwargs

    def parse_args(self, *args, **kwargs):
        # If the first object in args is string, converts it to list:
        args = list(args)
        if isinstance(args[0], str):
            args[0] = args[0].strip().split()

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
        while (arg_index < len(args[0])):
            arg = args[0][arg_index]
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
                    if arg != arg_name:
                        nargs -= 1
                    for i in range(nargs):
                        new_optional_args.append(args[0][arg_index])
                        arg_index += 1
                    break
            if is_optional_arg:
                continue

            # The current argument is not an option. Just put it to the end of
            # the new list to match the original order.
            if not is_optional_arg:
                new_pure_args.append(arg)
                arg_index += 1

        args[0] = new_optional_args + new_pure_args

        # Removes duplicated values for list objects:
        result = super(ArgumentParser, self).parse_args(*args, **kwargs)
        for key, value in result._get_kwargs():
            if isinstance(value, list):
                new_value = list(set(value))
                new_value.sort()
                setattr(result, key, new_value)
        return result


class GccArgumentParser(ArgumentParser):

    def __init__(self, *args, **kwargs):
        super(GccArgumentParser, self).__init__(*args, **kwargs)

        self.add_argument('-c', action='store_true')
        self.add_argument('-f', action='append')
        self.add_argument('-D', action='append', dest='defines')
        self.add_argument('-l', action='append', dest='libs')
        self.add_argument('-I', action='append', dest='include_dirs')
        self.add_argument('-L', action='append', dest='library_dirs')
        self.add_argument('-M')
        self.add_argument('-MF')
        self.add_argument('-MT')
        self.add_argument('-no-undefined', action='store_true')
        self.add_argument('-o', dest='output')
        self.add_argument('-O')
        self.add_argument('-Q')
        self.add_argument('-rpath')
        self.add_argument('-version-info')
        self.add_argument('-Wall', action='store_true')
        self.add_argument('sources', metavar='source', nargs='*')
