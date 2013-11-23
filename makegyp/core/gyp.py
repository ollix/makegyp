import collections
import json
import os
import platform
import re


def get_arch():
    """Returns the arch type.

    An empty string is returned if the value cannot be determined.
    """
    machine = platform.machine()
    if machine == 'i386':
        return 'ia32'
    elif machine == 'x86_64':
        return 'x64'
    else:
        return ''

def get_os():
    system = platform.system()
    if system == 'Windows':
        return 'win'
    elif system == 'Darwin':
        return 'mac'
    else:
        return system.lower()


class Target(object):
    library_name_pattern = re.compile(r'^lib.*\.\w+$')
    target_name_pattern = re.compile(r'^(lib)?(.*)(\.\w+)$')

    def __init__(self, target_output_name):
        if re.match(self.library_name_pattern, target_output_name):
            self.type = 'library'
        else:
            self.type = 'executable'

        self.name = re.sub(self.target_name_pattern, r'\2', target_output_name)
        self.defines = set()
        self.dependencies = set()
        self.include_dirs = set()
        self.sources = set()

    def __repr__(self):
        return '<Target: %s>' % self.name

    def add_dependency_by_path(self, path):
        filename = os.path.basename(path)
        name = re.sub(self.target_name_pattern, r'\2', filename)
        self.dependencies.add(name)

    def dump(self):
        obj = collections.OrderedDict()
        obj['name'] = self.name
        obj['type'] = self.type
        obj['sources'] = sorted(self.sources)
        obj['include_dirs'] = sorted(self.include_dirs)
        obj['defines'] = sorted(self.defines)
        obj['dependencies'] = sorted(self.dependencies)
        return json.dumps(obj, indent=4)
