import re


class Parser(object):
    pass


class MakeParser(Parser):
    def parse_configure(self, source):
        pattern = re.compile(r'config.status:\screating\s(.*config\.h)')
        result = []

        for line in source.split('\n'):
            if not pattern.match(line):
                continue

            config_file = re.sub(pattern, r'\1', line)
            if config_file:
                print 'Generated config file: %s' % config_file
                result.append(config_file)

        return result

if __name__ == "__main__":
    pattern = re.compile(r'config.status:\screating\s(.*config\.h)')
    string = "config.status: creating macosx/English.lproj/Makefile"
    print pattern.match(string)
    print 'Result:', re.sub(pattern, r"\1", string)
