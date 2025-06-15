import socket
import time

single_instance_lock = None


def single_instance(name=__file__):
    """
    Ensures only one instance of a program is running by using a Unix domain socket as a lock.

    This function creates a Unix domain socket with a name derived from the provided parameter.
    If another instance is already running (socket address in use), it will wait and retry.
    Once successful, it acts as a lock preventing other instances from starting.

    Args:
        name: A unique identifier for the lock, defaults to the current file path

    Returns:
        None when lock is acquired. Blocks while waiting for lock.
    """
    global single_instance_lock
    if single_instance_lock is not None:
        return

    while True:
        try:
            single_instance_lock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            single_instance_lock.bind("\0%s" % name)
            return
        except OSError as e:
            if e.errno == 98:  # 98: Address already in use
                time.sleep(0.1)
            else:
                raise e
