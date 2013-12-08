import os

from makegyp import formula
from makegyp.core import parser


class Faad2(formula.Formula):
    parser = parser.GccParser()
    url = 'http://downloads.sourceforge.net/project/faac/faad2-src/faad2-2.7/faad2-2.7.tar.gz'
    sha256 = 'ee26ed1e177c0cd8fa8458a481b14a0b24ca0b51468c8b4c8b676fd3ceccd330'

    def configure(self):
        return './configure --disable-shared --enable-static --with-pic'

    def make(self):
        return 'make'

    def post_process(self, package_root):
        # Fixes the include path in libfaad/common.h
        source_path = os.path.join(package_root, 'libfaad', 'common.h')
        source_file = open(source_path, 'r')
        source = source_file.read()
        source_file.close()

        source_file = open(source_path, 'w')
        source = source.replace('../config.h', 'config.h')
        source_file.write(source)
        source_file.close()
