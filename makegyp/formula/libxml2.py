from makegyp import formula
from makegyp.core import parser


class Libxml2(formula.Formula):
    parser = parser.MakeParser()
    url = 'ftp://xmlsoft.org/libxml2/libxml2-2.9.1.tar.gz'
    sha256 = 'fd3c64cb66f2c4ea27e934d275904d92cec494a8e8405613780cbc8a71680fdb'

    def configure(self):
        return ['./configure']

    def make(self):
        return ['make']
