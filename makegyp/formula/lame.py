from makegyp import formula
from makegyp.core import parser


class Lame(formula.Formula):
    parser = parser.MakeParser()
    url = 'http://downloads.sourceforge.net/project/lame/lame/3.99/lame-3.99.5.tar.gz'
    sha1 = '86a8f52e8097e8bf45eeb0a5e828be1ea0b099cd'

    def configure(self):
        return ['./configure', '--enable-static', '--disable-shared',
                '--with-pic', '--disable-rpath', '--disable-frontend',
                '--disable-gtktest']
