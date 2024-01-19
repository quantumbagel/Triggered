import subprocess


def get_git_revision_short_hash() -> str:
    """
    Get the local git repository's commit version, or "not running in git" if it doesn't exist
    :return: the commit version
    """
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except subprocess.CalledProcessError:  # The error thrown when outside a git repo
        return "not running in git"


def check_for_updates(stream="stable") -> (bool, str, str, int, int):
    """
    Return a boolean describing if an update is available
    :param stream: the stream to update on (stable, dev)
    :return:
    """
    try:
        subprocess.check_output(['git', 'remote', 'update'])  # Update our version of the remote
        our_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
        latest_hash = (subprocess.check_output(['git', 'rev-parse', f'origin/{stream}'])
                       .decode('ascii').strip())
        if our_hash != latest_hash:
            our_hash_time = subprocess.check_output(['git', 'show', '-s', '--format=%ct', "HEAD"])
            latest_hash_time = subprocess.check_output(['git', 'show', '-s', '--format=%ct',
                                                        f"origin/{stream}"])
            if int(latest_hash_time) > int(our_hash_time):
                return True, latest_hash, our_hash, int(our_hash_time), int(latest_hash_time)  # Update is available
            else:
                return False, "", "", 0, 0  # it isn't
        else:
            return False, "", "", 0, 0  # same hash
    except subprocess.CalledProcessError:
        return False, "", "", 0, 0


def update(stream: str) -> (bool, str):
    """
    Update to this stream from remote
    :param stream: the stream to update to
    :return: whether it succeeded
    """
    try:
        subprocess.check_output(['git', 'checkout', stream])
        subprocess.check_output(['git', 'pull'])
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, str(e)
