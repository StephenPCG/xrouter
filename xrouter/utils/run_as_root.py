import os
import sys


def run_as_root():
    """
    Ensures the program runs with root privileges by re-executing with sudo if needed.

    Checks the current user ID and if not running as root (uid 0), re-executes the
    program using sudo to gain root privileges.
    """
    uid = os.getuid()

    if uid != 0:
        os.execvp("sudo", ["sudo"] + sys.argv)
