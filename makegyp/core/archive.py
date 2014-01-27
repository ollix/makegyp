import contextlib
import os
import tarfile
import zipfile

import lzma


lzma_exts = ('.tar.xz',)
tarfile_exts = ('.tar', '.tar.bz2', '.tar.gz')
zip_exts = ('.zip',)
all_archive_exts = (lzma_exts, tarfile_exts, zip_exts)


def extract_archive(src, dest=None):
    if dest is None:
        dest = os.path.dirname(src)

    ext = splitext(src)[1]
    if ext in lzma_exts:
        with contextlib.closing(lzma.LZMAFile(src)) as xz:
            with tarfile.open(fileobj=xz) as archive:
                archive.extractall(path=dest)
    elif ext in tarfile_exts:
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
        if not name.endswith(archive_exts):
            continue

        for archive_ext in archive_exts:
            if not name.endswith(archive_ext):
                continue

            package_name, ext = name.rsplit(archive_ext)
            if not ext:
                return (package_name, archive_ext)

    return (name, "")
