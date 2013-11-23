from makegyp import formula
from makegyp.core import parser


class Curl(formula.Formula):
    parser = parser.LibtoolParser()
    url = 'http://curl.haxx.se/download/curl-7.33.0.tar.gz'
    sha256 = '7450a9c72bd27dd89dc6996aeadaf354fa49bc3c05998d8507e4ab29d4a95172'

    def configure(self):
        return ['./configure', '--enable-static', '--enable-shared=no',
                '--with-pic']

    def make(self):
        return ['make']
