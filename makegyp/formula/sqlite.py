from makegyp import formula
from makegyp.core import parser


class Sqlite(formula.Formula):
    parser = parser.GccParser()
    url = 'http://www.sqlite.org/2013/sqlite-autoconf-3080200.tar.gz'
    sha256 = 'a0851d06092c8208e4dd947f569f40db476b472b22e3e10e2f52f3c5e94fef92'

    def configure(self):
        return './configure'

    def make(self):
         return 'make'
