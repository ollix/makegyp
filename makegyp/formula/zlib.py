from makegyp import formula
from makegyp.core import parser


class Zlib(formula.Formula):
    parser = parser.GccParser()
    url = 'http://zlib.net/zlib-1.2.8.tar.gz'
    sha256 = '36658cb768a54c1d4dec43c3116c27ed893e88b02ecfcb44f2166f9c0b7f2a0d'

    def configure(self):
        return ['./configure', '--static']

    def make(self):
        return ['make']
