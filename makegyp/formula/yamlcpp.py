from makegyp import formula
from makegyp.core import parser


class Yamlcpp(formula.Formula):
    parser = parser.CmakeParser()
    url = 'https://yaml-cpp.googlecode.com/files/yaml-cpp-0.5.1.tar.gz'
    sha256 = '3e7c9052b43d987d41819a203d97fc45de4eed3ec67e0fdb14265c3d11046f06'

    def configure(self):
        return 'cmake . -G "Unix Makefiles"'

    def make(self):
         return 'make'
