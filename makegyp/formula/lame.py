from makegyp import formula
from makegyp.core import parser


class Lame(formula.Formula):
    parser = parser.LibtoolParser()
    url = 'http://downloads.sourceforge.net/project/lame/lame/3.99/lame-3.99.5.tar.gz'
    sha256 = '24346b4158e4af3bd9f2e194bb23eb473c75fb7377011523353196b19b9a23ff'

    def configure(self):
        return ['./configure', '--enable-static', '--disable-shared',
                '--with-pic', '--disable-rpath', '--disable-frontend',
                '--disable-gtktest']

    def make(self):
        return ['make']
