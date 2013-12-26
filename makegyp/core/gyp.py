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
    target_default_keywords = ('cflags', 'defines', 'dependencies',
                               'include_dirs')
    library_name_pattern = re.compile(r'^/?(.+?/)*(lib)(\w+?)\.(a|la|.*dylib)$')
    ignored_cflags = ('defines', 'frameworks', 'include_dirs', 'MF', 'MT',
                      'output', 'sources')

    def __init__(self, target_output_name):
        if re.match(self.library_name_pattern, target_output_name):
            self.type = 'library'
        else:
            self.type = 'executable'

        self.name = re.sub(self.library_name_pattern, r'\3', target_output_name)
        # Makes sure the name of a library target always starts with "lib".
        if self.type == 'library':
            self.name = 'lib%s' % self.name
        self.cflags = set()
        self.defines = set()
        self.dependencies = set()  # should be a list of Target objects or str
        self.frameworks = set()
        self.libraries = set()
        self.include_dirs = set()
        self.sources = set()

    def __repr__(self):
        return '<Target: %s>' % self.name

    def add_cflags(self, parsed_args):
        """Add a dictionary of C flags.

        The specified parsed_args must be a dictionary type.
        """
        for key, value in parsed_args.iteritems():
            if key in self.ignored_cflags or not value:
                continue

            cflags = '-%s' % key
            if isinstance(value, str):
                self.cflags.add(cflags + value)
            elif isinstance(value, list):
                for item in value:
                    self.cflags.add(cflags + item)

    def add_dependency_by_path(self, path):
        filename = os.path.basename(path)
        name = re.sub(self.target_name_pattern, r'\1', filename)
        self.dependencies.add(name)

    def gyp_dict(self, dependencies=None):
        obj = collections.OrderedDict()
        obj['target_name'] = self.name
        obj['type'] = 'static_library' if self.type == 'library' else self.type
        if self.sources:
            obj['sources'] = sorted(self.sources)
        if self.include_dirs:
            obj['include_dirs'] = sorted(self.include_dirs)
        if self.libraries or self.frameworks:
            obj['link_settings'] = collections.OrderedDict()
            libraries = obj['link_settings']['libraries'] = list()
            for framework in sorted(self.frameworks):
                libraries.append('-framework %s' % framework)
            for library in sorted(self.libraries):
                libraries.append('-l%s' % library)
        if self.defines:
            obj['defines'] = sorted(self.defines)
        if self.cflags:
            obj['cflags'] = sorted(self.cflags)
        if self.dependencies:
            dependencies = set()
            for dependency in self.dependencies:
                if isinstance(dependency, Target):
                    dependencies.add(dependency.name)
                elif isinstance(dependency, str):
                    dependencies.add(dependency)
            obj['dependencies'] = sorted(dependencies)
            obj['export_dependent_settings'] = obj['dependencies']

        return obj
