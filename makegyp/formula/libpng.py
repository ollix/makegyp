from makegyp import formula
from makegyp.core import parser


class Libpng(formula.Formula):
    config_files = ['pnglibconf.h']
    ignored_objects = [('.', 'pnglibconf.c'), ('.', 'scripts/sym.c')]
    parser = parser.GccParser(ignored_objects)
    url = 'http://downloads.sourceforge.net/project/libpng/libpng16/1.6.8/libpng-1.6.8.tar.gz'
    sha256 = '32c7acf1608b9c8b71b743b9780adb7a7b347563dbfb4a5263761056da44cc96'
    dependencies = ['zlib']
    include_dirs = {'libpng16': ('..',)}

    def configure(self):
        return './configure'

    def make(self):
         return 'make'
