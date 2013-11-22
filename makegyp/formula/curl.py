from makegyp import formula
from makegyp.core import parser


class Curl(formula.Formula):
    parser = parser.LibtoolParser()
    url = 'http://curl.haxx.se/download/curl-7.33.0.tar.gz'
    sha1 = ''

    def configure(self):
        return ['./configure', '--enable-static', '--enable-shared=no',
                '--with-pic']

    def make(self):
        return ['make']
