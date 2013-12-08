import os
import tarfile
import zipfile


tarfile_exts = ('.tar', '.tar.bz2', '.tar.gz')
zip_exts = ('.zip',)
all_archive_exts = (tarfile_exts, zip_exts)


def extract_archive(src, dest=None):
    if dest is None:
        dest = os.path.dirname(src)

    ext = splitext(src)[1]
    if ext in tarfile_exts:
        # Makes sure the file is a valid tar archive.
        if not tarfile.is_tarfile(src):
            print 'Invalid Tar archive: %s' % src
            exit(1)

        archive = tarfile.open(src)
        archive.extractall(path=dest)
    elif ext in zip_exts:
        if not zipfile.is_zipfile(src):
            print 'Invalid Zip archive: %s' % src
            exit(1)

        archive = zipfile.ZipFile(src)
        archive.extractall(path=dest)
        archive.close()
    else:
        print "Archive format is not supported: %r" % ext
        exit(1)

def splitext(name):
    for archive_exts in all_archive_exts:
        if name.endswith(archive_exts):
            for archive_ext in archive_exts:
                package_name, ext = name.rsplit(archive_ext)
                if not ext:
                    return (package_name, archive_ext)
    return (name, "")
