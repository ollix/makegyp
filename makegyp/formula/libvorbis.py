import os

from makegyp import formula
from makegyp.core import parser
from makegyp.core import utils


class Libvorbis(formula.Formula):
    parser = parser.GccParser()
    url = 'http://downloads.xiph.org/releases/vorbis/libvorbis-1.3.3.tar.gz'
    sha256 = '6d747efe7ac4ad249bf711527882cef79fb61d9194c45b5ca5498aa60f290762'
    dependencies = ['libogg']

    def configure(self):
        variables = dict()
        ogg_library_path = utils.build_target(self.install_dir, 'libogg')
        variables['ogg_libraries'] = os.path.dirname(ogg_library_path)
        variables['ogg_includes'] = os.path.join(self.install_dir,
                                                 'libogg', 'include')

        return './configure --enable-static --disable-shared --with-pic ' \
               '--with-ogg-libraries=%(ogg_libraries)s ' \
               '--with-ogg-includes=%(ogg_includes)s' % variables

    def make(self):
         return 'make'
