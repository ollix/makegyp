import argparse


class ArgumentParser(argparse.ArgumentParser):

    def parse_args(self, *args, **kwargs):
        # If the first object in args is string, converts it to list:
        args = list(args)
        if isinstance(args[0], str):
            args[0] = args[0].strip().split()

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

        self.add_argument('-c', dest='source')
        self.add_argument('-f', action='append')
        self.add_argument('-D', action='append', dest='defines')
        self.add_argument('-l', action='append', dest='libs')
        self.add_argument('-I', action='append', dest='include_dirs')
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
        self.add_argument('linked_files', metavar='linked_file', nargs='*')
