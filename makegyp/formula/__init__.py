import ftplib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib2
import urlparse

from makegyp.core import archive
from makegyp.core import gyp
from makegyp.core import parser


kConfigRootDirectoryName = "gyp_config"


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

        # Determines the root path to keep generated config files:
        self.config_root = os.path.join(self.tmp_package_path,
                                        kConfigRootDirectoryName)

    def __configure(self):
        output = self.__process('makegyp_configure_log', self.configure())

        # Determines the directory to keep config files:
        config_dir = os.path.join(self.config_root, gyp.get_os(),
                                  gyp.get_arch())

        # Copies each generated config file:
        for config in self.parser.parse_configure(output):
            src = os.path.join(self.tmp_package_path, config)
            dest = os.path.join(config_dir, config)
            # make sure the directory existed
            try:
                os.makedirs(os.path.dirname(dest))
            except OSError as error:
                if error.errno != 17:
                    raise error

            shutil.copyfile(src, dest)
            print 'Generated config file: %s' % dest

    def __download(self):
        if os.path.isdir(self.tmp_package_path):
            print 'Use cached package at \'%s\'' % self.tmp_package_path
            return

        filename = os.path.basename(self.url)
        file_path = os.path.join(self.tmp_dir, filename)
        if not os.path.isfile(file_path):
            print 'Downloading %s' % self.url

            url_info = urlparse.urlparse(self.url)
            local_package = open(file_path, 'wb')
            failed = False

            if url_info.scheme == 'http':
                package = urllib2.urlopen(self.url)
                if package.getcode() == 200:
                    local_package.write(package.read())
                else:
                    print 'Failed to download \'%s\' (error code: %d)' % \
                          (filename, package.getcode())
                    failed = True
            elif url_info.scheme == 'ftp':
                ftp = ftplib.FTP(url_info.netloc)
                ftp.login()
                ftp.retrbinary('RETR %s' % url_info.path, local_package.write)
                ftp.quit()
            else:
                print 'URL is not supported: %s' % self.url
                failed = True

            local_package.close()
            if failed:
                exit(1)

        # Extracts the archive:
        print 'Extracting archive \'%s\'' % file_path
        archive.extract_archive(file_path)

    def __process(self, log_name, args):
        """Process the args and preserve the output.

        Returns the output of the processed arguments.
        """
        log_file_path = os.path.join(self.tmp_package_path, log_name)
        identifier = "# %s\n" % ' '.join(args)

        # Checks if the log can be reused:
        needs_to_process = True
        if os.path.isfile(log_file_path):
            log_file = open(log_file_path, 'r')
            if log_file.readline() == identifier:
                # It's ok to reuse the log
                needs_to_process = False
                output = log_file.read()
            log_file.close()

        if needs_to_process:
            try:
                output = subprocess.check_output(args)
            except subprocess.CalledProcessError as e:
                print 'Failed to process the formula: %s' % e.output
                esxit(1)

            # Preserves the output for debug and reuse:
            log_file = open(log_file_path, 'w')
            log_file.write(identifier)
            log_file.write(output)
            log_file.close()

        return output

    def __reset_gyp(self):
        self.gyp.clear()

        # Initializes target_defaults:
        self.gyp['target_defaults'] = dict()
        self.gyp['target_defaults']['default_configuration'] = 'Debug'
        self.gyp['target_defaults']['configurations'] = {
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
        self.gyp['target_defaults']['msvs_settings'] = {
            'VCLinkerTool': {'GenerateDebugInformation': 'true'},
        }
        self.gyp['variables'] = {
            'target_arch%': gyp.get_arch(),
        }
        self.gyp['target_defaults']['include_dirs'] = [
            # platform and arch-specific headers
            '%s/<(OS)/<(target_arch)' % kConfigRootDirectoryName
        ]

        # Initializes targets
        self.gyp['targets'] = list()

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
