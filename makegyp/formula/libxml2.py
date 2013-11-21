from makegyp import formula
from makegyp.core import parser


class Libxml2(formula.Formula):
    parser = parser.MakeParser()
    url = 'ftp://xmlsoft.org/libxml2/libxml2-2.9.1.tar.gz'
    sha1 = ''

    def configure(self):
        return ['./configure']

    def make(self):
        return ['make']
