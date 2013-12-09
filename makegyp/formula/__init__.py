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
from makegyp.core import utils


kConfigRootDirectoryName = "gyp_config"


class Formula(object):
    name = None
    parser = None
    url = None
    sha256 = None
    dependencies = list()

    def __init__(self, install_dir):
        self.gyp = collections.OrderedDict()

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

        # Determines the path to keep output files that will be copied to
        # install path:
        self.tmp_output_path = os.path.join(self.tmp_dir, 'output')
        self.tmp_raw_package_output_path = os.path.join(self.tmp_output_path,
                                                        self.package_name)
        self.tmp_package_output_path = os.path.join(self.tmp_output_path,
                                                    self.name)

        # Determines the install path:
        self.install_dir = os.path.abspath(install_dir)
        self.install_path = os.path.join(self.install_dir, self.name)

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
        # Adds target dependencies:
        if self.dependencies:
            dependencies = dict()
            for target in targets:
                for library in target.libraries:
                    if library in dependencies:
                        continue

                    # Finds matched dependency:
                    for dependency in self.dependencies:
                        dependency_dir = os.path.join(self.install_dir,
                                                      dependency)
                        if not os.path.isdir(dependency_dir):
                            continue

                        gyp_file_path = os.path.join(dependency_dir,
                                                     '%s.gyp' % dependency)
                        if not os.path.isfile(gyp_file_path):
                            continue

                        gyp_file = file(gyp_file_path, 'r')
                        gyp_file.readline()  # skips comment
                        dependency_gyp = json.loads(gyp_file.read())
                        gyp_file.close()

                        target_names = [t['target_name'] \
                            for t in dependency_gyp['targets']]

                        library_target_name = 'lib%s' % library
                        if library_target_name in target_names:
                            dependency = '../%s/%s.gyp:%s' % \
                                (dependency, dependency, library_target_name)
                            dependencies[library] = dependency
                            break
                    else:
                        dependencies[library] = None

                for library in dependencies:
                    dependency = dependencies[library]
                    if library in target.libraries and dependency is not None:
                        target.libraries.remove(library)
                        target.dependencies.add(dependency)

        # Removes include_dirs pointing to dependencies:
        for target in targets:
            to_removed_include_dirs = set()
            for include_dir in target.include_dirs:
                if not os.path.isabs(include_dir):
                    continue

                # Makes sure the path is for dependency:
                relpath = os.path.relpath(include_dir, self.install_dir)
                if not relpath.startswith('..'):
                    to_removed_include_dirs.add(include_dir)

            target.include_dirs = target.include_dirs.difference(
                to_removed_include_dirs)

        # Extracts target defaults:
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
        output = self.__process('makegyp_configure_log', self.configure_args)

        # Determines the directory to keep config files:
        config_dir = os.path.join(self.config_root, gyp.get_os(),
                                  gyp.get_arch())
        # make sure the directory existed
        try:
            os.makedirs(config_dir)
        except OSError as error:
            if error.errno != 17:
                raise error

        # Copies each generated config file:
        for config in self.parser.get_config_files(output):
            src = os.path.join(self.tmp_package_path, config)
            dest = os.path.join(config_dir, os.path.basename(config))

            try:
                shutil.copyfile(src, dest)
            except IOError as error:
                if error.errno == 2:
                    print 'Failed to copy config file: %r' % config
                    exit(1)
                else:
                    raise error
            print 'Generated config file: %s' % dest

    def __process(self, log_name, args, pre_process_func=None):
        """Process the args and preserve the output.

        Returns the output of the processed arguments.
        """
        log_file_path = os.path.join(self.tmp_package_path, log_name)

        if not hasattr(self, 'identifier'):
            self.identifier = hashlib.sha256(self.configure_args).hexdigest()
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
            if pre_process_func is not None:
                pre_process_func()

            try:
                output = subprocess.check_output(args, shell=True)
            except subprocess.CalledProcessError as e:
                print 'Failed to process the formula: %s' % args
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
        self.gyp['target_defaults']['conditions'] = [
            ["OS=='mac'", {
                'conditions': [
                    ["target_arch=='ia32'",
                     {'xcode_settings': {'ARCHS': ['i386']}}],
                    ["target_arch=='x64'",
                     {'xcode_settings': {'ARCHS': ['x86_64']}}],
                ]
            }],
        ]

        # Initializes targets
        self.gyp['targets'] = list()

    def configure(self):
        return list()

    def install(self):
        # Remembers the current directory:
        curdir = os.path.abspath(os.path.curdir)

        print 'Installing %s...' % self.name
        self.__reset_gyp()
        self.__download()
        os.chdir(self.tmp_package_path)
        print 'Configuring...'
        self.configure_args = self.configure()
        self.__generate_config_files()
        print 'Making...'
        # Tries to clean built files before actually do make:
        def clean_make():
            try:
                subprocess.check_output('make clean', stderr=subprocess.STDOUT,
                                        shell=True)
            except subprocess.CalledProcessError:
                pass
        output = self.__process('makegyp_make_log', self.make(),
                                pre_process_func=clean_make)

        print 'Generating gyp file...'
        targets = self.parser.get_targets(output)
        self.__add_targets_to_gyp(targets)

        # Changes back to the original directory:
        os.chdir(curdir)

        # Generates the GYP file:
        gyp_filename = "%s.gyp" % self.name
        gyp_file_path = os.path.join(self.tmp_package_path, gyp_filename)
        gyp_file = open(gyp_file_path, "w")
        gyp_file.write('# makegyp: %s\n' % self.package_name)
        json.dump(self.gyp, gyp_file, indent=4)
        gyp_file.close()

        # Copies library source code along generated files to destination:
        shutil.rmtree(self.tmp_package_output_path, True)
        archive_path = os.path.join(self.tmp_dir, os.path.basename(self.url))
        print 'Copying library source code to %r' % self.install_path
        try:
            os.mkdir(self.tmp_output_path)
        except OSError as error:
            # Ignores error if the deps directory already exists.
            if not error.errno == 17:
                raise error
        archive.extract_archive(archive_path, self.tmp_output_path)
        os.rename(self.tmp_raw_package_output_path,
                  self.tmp_package_output_path)

        # Copies config files:
        config_dest = os.path.join(self.tmp_package_output_path,
                                   kConfigRootDirectoryName)
        print 'Copying config files to %r' % config_dest
        shutil.copytree(self.config_root, config_dest)

        # Copies gyp file:
        gyp_dest = os.path.join(self.tmp_package_output_path, gyp_filename)
        print 'Copying gyp file to %r' % gyp_dest
        shutil.copyfile(gyp_file_path, gyp_dest)

        # Post-precoesses the installed library:
        print 'Post-processing the library...'
        self.post_process(self.tmp_package_output_path)

        shutil.rmtree(self.install_path, True)
        shutil.copytree(self.tmp_package_output_path, self.install_path)

        print 'Installed %r to %r' % (self.name, self.install_path)
        target_prefix = os.path.join(os.path.relpath(self.install_dir),
                                     self.name, gyp_filename)
        for target in targets:
            print '- %s::%s:%s' % (target.type, target_prefix, target.name)

    def make(self):
        return list()

    def post_process(self, package_root):
        """This method will be called after the library installed."""
        pass
