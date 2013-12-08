from makegyp import formula
from makegyp.core import parser


class Mpg123(formula.Formula):
    parser = parser.GccParser()
    url = 'http://mpg123.orgis.org/download/mpg123-1.16.0.tar.bz2'
    sha256 = 'f00f72e385b522b8f05c9b1ed371abad438362620e6eb8164e2a99b79bb3f6d3'

    def configure(self):
        return './configure --enable-static --disable-shared --with-pic ' \
               '--with-cpu=generic_fpu'

    def make(self):
         return 'make'
