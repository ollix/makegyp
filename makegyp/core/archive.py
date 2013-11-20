import os
import tarfile


tarfile_exts = ('.tar', '.tar.gz')
all_archive_exts = (tarfile_exts,)


def extract_archive(path):
    ext = splitext(path)[1]
    if ext in tarfile_exts:
        # Makes sure the file is a valid tar archive.
        if not tarfile.is_tarfile(path):
            print 'Invalid Tar archive: %s' % path
            exit(1)

        archive = tarfile.open(path)
        archive.extractall(path=os.path.dirname(path))

def splitext(name):
    for archive_exts in all_archive_exts:
        if name.endswith(archive_exts):
            for archive_ext in archive_exts:
                package_name, ext = name.rsplit(archive_ext)
                if not ext:
                    return (package_name, archive_ext)
    return (name, "")
