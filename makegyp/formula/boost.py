import collections
import platform
import subprocess

from makegyp import formula
from makegyp.core import parser


class Boost(formula.Formula):
    parser = parser.GccParser()
    url = 'http://downloads.sourceforge.net/project/boost/boost/1.59.0/' \
          'boost_1_59_0.tar.gz'
    sha256 = '47f11c8844e579d02691a607fbd32540104a9ac7a2534a8ddaef50daf502baac'
    duplicated_basename_files = {
        'libboost_locale': ('libs/locale/src/posix/converter.cpp',
                            'libs/locale/src/posix/numeric.cpp',
                            'libs/locale/src/posix/codecvt.cpp',
                            'libs/locale/src/posix/collate.cpp')
    }
    target_dependencies = {
        'libboost_filesystem': ('libboost_system',),
    }

    def configure(self):
        system = platform.system()
        bootstrap = 'bootstrap'
        if system == 'Darwin':
            bootstrap += '.sh'
        elif system == 'Windows':
            bootstrap += '.bat'
        return './%s' % bootstrap

    def make(self):
        arguments = './b2 -d2 link=static'
        subprocess.call('%s --clean' % arguments, shell=True)  # clean
        return arguments

    def patch_gyp_dict(self, gyp_dict):
        """Adds the boost target for header-only libraries."""
        target = collections.OrderedDict()
        target['target_name'] = 'libboost_headers'
        target['type'] = 'none'
        target['include_dirs'] = ['.']
        target['direct_dependent_settings'] = {
            'include_dirs': target['include_dirs'],
        }
        gyp_dict['targets'].append(target)
