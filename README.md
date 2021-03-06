makegyp
=======

*makegyp* tries to add existing C or C++ library as modules with GYP support.
This project is still at early stage and could be constantly changed.

The idea behind makegyp is inspired by [Homebrew](http://brew.sh) and
[npm](https://npmjs.org). Like Homebrew, *formula* is defined explicitly
for installing a library. And like npm, C or C++ libraries will be installed
as modules under a specific directory.

Also, thanks to Nathan Rajlich for writing this
[article](http://n8.io/converting-a-c-library-to-gyp/). *makegyp* pretty much
does the same thing but programatically.

Why makegyp?
-------------
I was trying to find a better way to develop my C++ projects. I chose Google's
[GYP](https://code.google.com/p/gyp/) build system as my weapon to build
my products. But if I want to easily use existing C or C++ libraries as
dependencies, I need to convert them from other build system to GYP before I
can use. It's really cumbersome to do such work manually and repeatly. So I
created this project trying to automate that work.

How does it work?
-----------------
Each C or C++ library will be supported by implementing an inherited Formula
class. When installing, *makegyp* will try to download and build the library by
a predefined formula, then inspect the building process and finally
generate necessary config files and  a GYP script for that library.
The installed module is just a normal source code library with GYP support so
you can easily use them as dependencies of your GYP projects.

Try it!
-------
*makegyp* is written in Python, so you can install it by [pip](http://www.pip-installer.org/en/latest/) like this:

    pip install git+git://github.com/olliwang/makegyp.git

Now create a new directory and switch to it. You can simply install the [LAME](http://lame.sourceforge.net) library one command:

    $mkgyp install lame

    Created 'gyp_deps' directory.
    Installing lame...
    Use cached package at '/var/folders/gf/dx4d3hdj6yg302w7qkyz8zt40000gn/T/makegyp/lame-3.99.5'
    Configuring...
    Generated config file: /var/folders/gf/dx4d3hdj6yg302w7qkyz8zt40000gn/T/makegyp/lame-3.99.5/gyp_config/mac/x64/config.h
    Making...
    Generating gyp file...
    Copying library source code to '/Users/olliwang/workspace/pip_makegyp/gyp_deps/lame-3.99.5'
    Copying config files to '/Users/olliwang/workspace/pip_makegyp/gyp_deps/lame-3.99.5/gyp_config'
    Copying gyp file to '/Users/olliwang/workspace/pip_makegyp/gyp_deps/lame-3.99.5/lame.gyp'
    Installed 'lame' to '/Users/olliwang/workspace/pip_makegyp/gyp_deps/lame-3.99.5'
    - library::gyp_deps/lame-3.99.5/lame.gyp:libmpgdecoder
    - library::gyp_deps/lame-3.99.5/lame.gyp:liblamevectorroutines
    - library::gyp_deps/lame-3.99.5/lame.gyp:libmp3lame

That's it. Now the *LAME* library should be installed as a module in the auto
generated *gyp_deps* directory. You can add *gyp_deps/lame/lame.gyp:libmp3lame*
to the target's *dependencies* field in your GYP file and write a simple
program to test it.

    #include <stdio.h>
    #include "lame.h"

    int main(int argc, char **argv) {
        printf("get_lame_version(): %s\n", get_lame_version());
        return 0;
    }

Write a GYP file for your test problem like this:

    {
        "target_defaults": {
            "default_configuration": "Debug",
            "configurations": {
                "Debug": {},
                "Release": {},
            },
        },
        'targets': [
            {
                'target_name': 'test',
                'type': 'executable',
                'sources': [
                    'main.c',
                ],
                'dependencies': [
                    'gyp_deps/lame/lame.gyp:libmp3lame',
                ],
            },
        ],
    }

At this point, you can build your test program:

    $gyp --depth=. -f ninja test.gyp
    $ninja -C out/Debug/

And run the test program:

    $ ./out/Debug/test
    get_lame_version(): 3.99.5

It works!

What's Next?
------------
I'm going to support more libraries for my needs and the parsers will be
improved as well to be able to support more libraries. If you can't find the
library you need in the supported list below. You can also write formula for
your needs. You may want to check the "tests" directory to get the idea how
to use makegyp to install all dependent library at once through the
gyp_deps.txt file. If you have such file, all you have to do is run
`mkgyp install` in the same directory.

Current working formulas
-------------------------
- [boost](http://www.boost.org)
- [faad2](http://www.audiocoding.com/faad2.html)
- [gtest](https://code.google.com/p/googletest/)
- [lame](http://lame.sourceforge.net)
- [libffi](https://sourceware.org/libffi/)
- [libogg](http://xiph.org/ogg/)
- [libvorbis](http://xiph.org/vorbis/)
- [libpng](http://www.libpng.org/pub/png/libpng.html)
- [mpg123](http://www.mpg123.de)
- [openssl](http://www.openssl.org) (32-bit only)
- [sqlite](http://www.sqlite.org)
- [yamlcpp](https://code.google.com/p/yaml-cpp/)
- [zlib](http://www.zlib.net)
