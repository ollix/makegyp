from makegyp import formula
from makegyp.core import parser


class Gtest(formula.Formula):
    parser = parser.CmakeParser()
    url = 'https://googletest.googlecode.com/files/gtest-1.7.0.zip'
    sha256 = '247ca18dd83f53deb1328be17e4b1be31514cedfc1e3424f672bf11fd7e0d60d'

    def configure(self):
        return 'cmake . -G "Unix Makefiles" -DBUILD_SHARED_LIBS=OFF'

    def make(self):
        return 'make'
