import os
import subprocess
import tarfile
import urllib2

from makegyp.core import archive


class Formula(object):
    url = None
    sha1 = None

    def __init__(self):
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
        self.tmp_dir = os.path.join(self.deps_dir, '.tmp')
        try:
            os.mkdir(self.tmp_dir)
        except OSError as error:
            # Ignores error if the deps directory already exists.
            if not error.errno == 17:
                raise error

    def configure(self):
        return list()

    def download(self):
        filename = os.path.basename(self.url)
        package_name, ext = archive.splitext(filename)

        self.tmp_package_path = os.path.join(self.tmp_dir, package_name)
        if os.path.isdir(self.tmp_package_path):
            print 'Use cached package at \'%s\'' % self.tmp_package_path
            return

        file_path = os.path.join(self.tmp_dir, filename)
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

    def install(self):
        print 'Installing %s...' % self.__class__.__name__
        self.download()
        # configure_args = self.configure()
        #
        # try:
        #     output = subprocess.check_output(configure_args)
        # except subprocess.CalledProcessError as e:
        #     # print 'Error:', e.output
        #     return
        #
        # print 'OUTPUT:', output

    def make(self):
        return list()
