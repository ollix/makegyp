import collections
import ftplib
import hashlib
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
    name = None
    parser = None
    url = None
    sha256 = None

    def __init__(self):
        self.gyp = collections.OrderedDict()

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

        # Guesses the library name:
        if not self.name:
            self.name = self.__class__.__name__.lower()

        # Determines the install path:
        self.install_path = os.path.join(self.deps_dir, self.package_name)

    def __add_direct_dependent_settings_to_target(self, target):
        # Retrieves default include dirs as a set:
        try:
            default_include_dirs = self.gyp['target_defaults']['include_dirs']
        except KeyError:
            default_include_dirs = set()
        else:
            default_include_dirs = set(default_include_dirs)
        # Retrieves target include dirs as as set:
        try:
            target_include_dirs = target['include_dirs']
        except KeyError:
            target_include_dirs = set()
        else:
            target_include_dirs = set(target_include_dirs)
        # Merges two sets of include dirs and adds to direct_dependent_settings:
        include_dirs = sorted(default_include_dirs.union(target_include_dirs))
        target['direct_dependent_settings'] = {'include_dirs': include_dirs}

    def __add_targets_to_gyp(self, targets):
        target_gyp_dicts = [target.gyp_dict() for target in targets]

        target_defaults = self.gyp['target_defaults']
        for keyword in gyp.Target.target_default_keywords:
            # Finds common values for the target default keyword:
            common_values = None
            for target in target_gyp_dicts:
                # Retrieves current values from the target:
                try:
                    values = target[keyword]
                except KeyError:
                    values = set()
                else:
                    values = set(values)

                # Updates common values:
                if common_values is None:
                    common_values = values
                else:
                    common_values = common_values.intersection(values)

                # Stops searching if there is not common values:
                if not common_values:
                    break

            # If there are common values, merge them to top-level target
            # defaults and remove them from each target:
            if common_values:
                # Merges common values into target defaults:
                try:
                    values = target_defaults[keyword]
                except KeyError:
                    values = set()
                else:
                    values = set(values)
                target_defaults[keyword] = sorted(values.union(common_values))

                # Removes common values from each target:
                for target in target_gyp_dicts:
                    try:
                        values = target[keyword]
                    except KeyError:
                        pass
                    else:
                        new_values = set(values).difference(common_values)
                        if new_values:
                            target[keyword] = sorted(new_values)
                        else:
                            target.pop(keyword)

        for target in target_gyp_dicts:
            # Adds direct_dependent_settings to target:
            self.__add_direct_dependent_settings_to_target(target)

            self.gyp['targets'].append(target)

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

            if url_info.scheme in ('http', 'https'):
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

        # Checks checksum:
        local_package = open(file_path, 'rb')
        if hashlib.sha256(local_package.read()).hexdigest() != self.sha256:
            print 'SHA256 checksum not matched: %s %s' % \
                (self.sha256, file_path)
            exit(1)

        # Extracts the archive:
        print 'Extracting archive \'%s\'' % file_path
        archive.extract_archive(file_path)

    def __generate_config_files(self):
        output = self.__process('makegyp_configure_log', self.configure())

        # Determines the directory to keep config files:
        config_dir = os.path.join(self.config_root, gyp.get_os(),
                                  gyp.get_arch())

        # Copies each generated config file:
        for config in self.parser.get_config_files(output):
            src = os.path.join(self.tmp_package_path, config)
            dest = os.path.join(config_dir, os.path.basename(config))
            # make sure the directory existed
            try:
                os.makedirs(os.path.dirname(dest))
            except OSError as error:
                if error.errno != 17:
                    raise error

            shutil.copyfile(src, dest)
            print 'Generated config file: %s' % dest

    def __process(self, log_name, args):
        """Process the args and preserve the output.

        Returns the output of the processed arguments.
        """
        log_file_path = os.path.join(self.tmp_package_path, log_name)

        if not hasattr(self, 'identifier'):
            configure_args = ' '.join(self.configure())
            self.identifier = hashlib.sha256(configure_args).hexdigest()
            self.identifier = '# %s\n' % self.identifier

        args_string = args
        if isinstance(args, list):
            args_string = ' '.join(args)
        args_str = '# %s\n' % args_string

        # Checks if the log can be reused:
        needs_to_process = True
        if os.path.isfile(log_file_path):
            log_file = open(log_file_path, 'r')
            if log_file.readline() == self.identifier and \
               log_file.readline() == args_str:
                # It's ok to reuse the log
                needs_to_process = False
                output = log_file.read()
            log_file.close()

        if needs_to_process:
            try:
                output = subprocess.check_output(args, shell=True)
            except subprocess.CalledProcessError as e:
                print 'Failed to process the formula: %s' % e.output
                exit(1)

            # Preserves the output for debug and reuse:
            log_file = open(log_file_path, 'w')
            log_file.write(self.identifier)
            log_file.write(args_str)
            log_file.write(output)
            log_file.close()

        return output

    def __reset_gyp(self):
        self.gyp.clear()

        # Initializes target_defaults:
        self.gyp['variables'] = {
            'target_arch%': gyp.get_arch(),
        }
        self.gyp['target_defaults'] = collections.OrderedDict()
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
        self.gyp['target_defaults']['include_dirs'] = [
            # platform and arch-specific headers
            '%s/<(OS)/<(target_arch)' % kConfigRootDirectoryName
        ]

        # Initializes targets
        self.gyp['targets'] = list()

    def configure(self):
        return list()

    def install(self):
        print 'Installing %s...' % self.name
        self.__reset_gyp()
        self.__download()
        os.chdir(self.tmp_package_path)
        print 'Configuring...'
        self.__generate_config_files()
        print 'Making...'
        # Tries to clean built files before actually do make:
        try:
            subprocess.check_output('make clean', stderr=subprocess.STDOUT,
                                    shell=True)
        except subprocess.CalledProcessError:
            pass
        output = self.__process('makegyp_make_log', self.make())
        print 'Generating gyp file...'
        targets = self.parser.get_targets(output)
        self.__add_targets_to_gyp(targets)

        # Generates the GYP file:
        gyp_filename = "%s.gyp" % self.name
        gyp_file_path = os.path.join(self.tmp_package_path, gyp_filename)
        gyp_file = open(gyp_file_path, "w")
        json.dump(self.gyp, gyp_file, indent=4)
        gyp_file.close()

        # Copies library source code along generated files to destination:
        archive_path = os.path.join(self.tmp_dir, os.path.basename(self.url))
        print 'Copying library source code to %r' % self.install_path
        archive.extract_archive(archive_path, self.deps_dir)

        # Copies config files:
        config_dest = os.path.join(self.install_path, kConfigRootDirectoryName)
        print 'Copying config files to %r' % config_dest
        try:
            shutil.rmtree(config_dest)
        except OSError as error:
            if error.errno == 2:
                pass  # don't care if the directory not exists
        shutil.copytree(self.config_root, config_dest)

        # Copies gyp file:
        gyp_dest = os.path.join(self.install_path, gyp_filename)
        print 'Copying gyp file to %r' % gyp_dest
        shutil.copyfile(gyp_file_path, gyp_dest)

        # Post-precoesses the installed library:
        print 'Post-processing the library...'
        self.post_process()

        print 'Installed %r to %r' % (self.name, self.install_path)
        target_prefix = os.path.join('gyp_deps', self.package_name,
                                     gyp_filename)
        for target in targets:
            print '- %s::%s:%s' % (target.type, target_prefix, target.name)

    def make(self):
        return list()

    def post_process(self):
        """This method will be called after the library installed."""
        pass
