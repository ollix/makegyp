import os
import tarfile


tarfile_exts = ('.tar', '.tar.gz')
all_archive_exts = (tarfile_exts,)


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

def splitext(name):
    for archive_exts in all_archive_exts:
        if name.endswith(archive_exts):
            for archive_ext in archive_exts:
                package_name, ext = name.rsplit(archive_ext)
                if not ext:
                    return (package_name, archive_ext)
    return (name, "")
