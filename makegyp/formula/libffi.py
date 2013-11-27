from makegyp import formula
from makegyp.core import parser


class Libffi(formula.Formula):
    parser = parser.GccParser()
    url = 'http://mirrors.kernel.org/sources.redhat.com/libffi/libffi-3.0.13.tar.gz'
    sha256 = '1dddde1400c3bcb7749d398071af88c3e4754058d2d4c0b3696c2f82dc5cf11c'

    def configure(self):
        return './configure --disable-shared --enable-static --disable-debug'

    def make(self):
        return 'make'
