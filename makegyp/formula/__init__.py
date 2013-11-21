import json
import os
import subprocess
import tarfile
import tempfile
import urllib2

from makegyp.core import archive
from makegyp.core import parser


class Formula(object):
    parser = parser.Parser()
    url = None
    sha1 = None

    def __init__(self):
        self.gyp = dict()

        # Creates the deps directory for keeping installed libraries:
        self.deps_dir = os.path.join(os.path.curdir, 'gyp_deps')
        self.deps_dir = os.path.abspath(self.deps_dir)
        try:
            os.mkdir(self.deps_dir)
        except OSError as error:
            # Ignores error if the deps directory already exists.
            if not error.errno == 17:
                raise error
        else:
            print "Created 'gyp_deps' directory."

        # Creates the temporary directory:
        self.tmp_dir = os.path.join(tempfile.gettempdir(), 'makegyp')
        try:
            os.mkdir(self.tmp_dir)
        except OSError as error:
            # Ignores error if the deps directory already exists.
            if not error.errno == 17:
                raise error

        # Determines the path to temporary package:
        filename = os.path.basename(self.url)
        self.package_name, ext = archive.splitext(filename)
        self.tmp_package_path = os.path.join(self.tmp_dir, self.package_name)

    def __configure(self):
        output = self.__process(self.configure())
        log_file_path = os.path.join(self.tmp_package_path,
                                     'makegyp_configure_log')
        log_file = open(log_file_path, 'w')
        log_file.write(output)
        log_file.close()

        self.parser.parse_configure(output)

    def __download(self):
        if os.path.isdir(self.tmp_package_path):
            print 'Use cached package at \'%s\'' % self.tmp_package_path
            return

        file_path = os.path.join(self.tmp_dir, os.path.basename(self.url))
        if not os.path.isfile(file_path):
            print 'Downloading %s' % self.url
            package = urllib2.urlopen(self.url)
            if package.getcode() != 200:
                print 'Failed to download \'%s\' (error code: %d)' % \
                      (filename, package.getcode())
                exit(1)

            local_package = open(file_path, 'wb')
            local_package.write(package.read())
            local_package.close()

        # Extracts the archive:
        print 'Extracting archive \'%s\'' % file_path
        archive.extract_archive(file_path)

    def __process(self, args):
        try:
            output = subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            print 'Failed to process the formula: %s' % e.output
            esxit(1)
        else:
            return output

    def __reset_gyp(self):
        gyp = self.gyp

        gyp.clear()

        # Initializes target_defaults:
        gyp['target_defaults'] = dict()
        gyp['target_defaults']['default_configuration'] = 'Debug'
        gyp['target_defaults']['configurations'] = {
            'Debug': {
                'defines': ['DEBUG', '_DEBUG'],
                'msvs_settings': {
                    'VCCLCompilerTool': {
                        'RuntimeLibrary': 1,  # static debug
                    },
                },
            },
            'Release': {
                'defines': ['NDEBUG'],
                'msvs_settings': {
                    'VCCLCompilerTool': {
                        'RuntimeLibrary': 0,  # static release
                    },
                },
            },
        }
        gyp['target_defaults']['msvs_settings'] = {
            'VCLinkerTool': {'GenerateDebugInformation': 'true'},
        }

        # Initializes targets
        gyp['targets'] = list()

    def configure(self):
        return list()

    def install(self):
        self.__reset_gyp()
        print 'Installing %s...' % self.__class__.__name__
        self.__download()
        os.chdir(self.tmp_package_path)
        print 'Configuring...'
        self.__configure()

        # Generates the GYP file:
        gyp_filename = "%s.gyp" % self.__class__.__name__.lower()
        gyp_file = open(os.path.join(self.tmp_package_path, gyp_filename), "w")
        json.dump(self.gyp, gyp_file, sort_keys=True, indent=4)
        gyp_file.close()

    def make(self):
        return list()
