from makegyp import formula
from makegyp.core import parser


class Libogg(formula.Formula):
    parser = parser.GccParser()
    url = 'http://downloads.xiph.org/releases/ogg/libogg-1.3.1.tar.gz'
    sha256 = '4e343f07aa5a1de8e0fa1107042d472186b3470d846b20b115b964eba5bae554'

    def configure(self):
        return './configure --enable-static --disable-shared --with-pic'

    def make(self):
         return 'make'
