import os
import shutil

from makegyp import formula
from makegyp.core import gyp
from makegyp.core import parser


class Openssl(formula.Formula):
    parser = parser.GccParser()
    url = 'http://www.openssl.org/source/openssl-1.0.1e.tar.gz'
    sha256 = 'f74f15e8c8ff11aa3d5bb5f276d202ec18d7246e95f961db76054199c69c1ae3'
    dependencies = ['zlib']
    default_target_arch = 'ia32'

    def configure(self):
        return './config zlib no-shared'

    def make(self):
         return 'make'

    def patch_gyp_dict(self, gyp_dict):
        # Patchs the libcrypto target:
        for target in gyp_dict['targets']:
            if target['target_name'] == 'libcrypto':
                # Adds the missing `mem_clr.c` source:
                target['sources'].append('crypto/mem_clr.c')
                target['sources'].sort()
                # Adds zlib as dependency:
                target['dependencies'] = ['../zlib/zlib.gyp:libz']
                break

    def post_process(self, package_root):
        # Copies the generated "*.s" files to package:
        for target in self.gyp['targets']:
            for source in target['sources']:
                if source.endswith('.s'):
                    print('Copying source file: %s' % source)
                    path_components = source.split('/')
                    source = os.path.join(self.tmp_package_root,
                                          *path_components)
                    dest = os.path.join(package_root, *path_components)
                    shutil.copyfile(source, dest)

        # Copies config files:
        config_file_paths = ['crypto/buildinf.h']
        for path in config_file_paths:
            print('Copying config file: %s' % path)
            source = os.path.join(self.tmp_package_root, *path.split('/'))
            dest = os.path.join(package_root, formula.kConfigRootDirectoryName,
                                gyp.get_os(), self.default_target_arch,
                                os.path.basename(source))
            shutil.copyfile(source, dest)
