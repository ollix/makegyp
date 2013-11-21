import platform


def get_arch():
    """Returns the arch type.

    An empty string is returned if the value cannot be determined.
    """
    machine = platform.machine()
    if machine == 'i386':
        return 'ia32'
    elif machine == 'x86_64':
        return 'x64'
    else:
        return ''

def get_os():
    system = platform.system()
    if system == 'Windows':
        return 'win'
    elif system == 'Darwin':
        return 'mac'
    else:
        return system.lower()
