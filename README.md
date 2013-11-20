makegyp
=======

makegyp tries to add existing C or C++ library as modules with GYP support.
This project is still at early stage and could be constantly changed. It's also
not functional yet.

The idea behind makegyp is inspired by [Homebrew](http://brew.sh) and
[npm](https://npmjs.org). Like Homebrew, *formula* is defined explicitly
for installing a library. And like npm, C or C++ libraries will be installed
as modules under a specific directory.

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
class. When installing, makegyp will try to download and build the library by
a predefined formula, analyze the output of the building process, and finally
generate necessary config and GYP files for that library. The installed module
is just a normal source code library with GYP support so you can easily use
them as dependencies in your GYP projects.
