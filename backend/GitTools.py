import subprocess

REMOTE_BRANCH = "master"


def perform_remote_update() -> None:
    """
    Update data for the remote
    :return: nothing
    """
    subprocess.check_output(['git', 'remote', 'update'])


def get_git_revision_short_hash() -> str:
    """
    Get the local git repository's commit version, or "not running in git" if it doesn't exist
    :return: the commit version
    """
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except subprocess.CalledProcessError:  # The error thrown when outside a git repo
        return "not running in git"


def get_stable_version_local() -> str:
    """
    Get the newest stable version tag from local
    :return:
    """
    return (subprocess.check_output(['git', 'describe', '--abbrev=0', '--tags', f'HEAD'])
            .decode('ascii').strip())


def get_stable_version_remote() -> str:
    """
    Get the newest stable version tag from the remote.
    :return: the version
    """
    return (subprocess.check_output(['git', 'describe', '--abbrev=0', '--tags', f'origin/{REMOTE_BRANCH}'])
            .decode('ascii').strip())


def get_hash_of_version(v: str) -> str:
    """
    Turn the version into its commit hash
    :param v: the version tag
    :return: the hash
    """
    return subprocess.check_output(['git', 'show-ref', '--tags', v]).decode('ascii').strip().split()[0]


def get_remote_short_hash() -> str:
    """
    Get the remote git repository's commit hash, or "not running in git" if it doesn't exist
    :return: the commit hash
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
        perform_remote_update()  # Update our version of the remote
        if stream == "dev":  # Our version is not a stable release, so attempt to blindly update to latest version
            our_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
            latest_hash = (subprocess.check_output(['git', 'rev-parse', f'origin/{REMOTE_BRANCH}'])
                           .decode('ascii').strip())
            if our_hash != latest_hash:
                our_hash_time = subprocess.check_output(['git', 'show', '-s', '--format=%ct', "HEAD"])
                latest_hash_time = subprocess.check_output(['git', 'show', '-s', '--format=%ct',
                                                            f"origin/{REMOTE_BRANCH}"])
                if int(latest_hash_time) > int(our_hash_time):
                    return True, latest_hash, our_hash, int(our_hash_time), int(latest_hash_time)  # Update is available
                else:
                    return False, "", "", 0, 0  # it isn't
            else:
                return False, "", "", 0, 0  # same hash
        else:  # "stable" stream by default
            local_version = get_stable_version_local()
            global_version = get_stable_version_remote()
            hash_local = get_hash_of_version(local_version)
            hash_global = get_hash_of_version(global_version)
            our_hash_time = subprocess.check_output(['git', 'show', '-s', '--format=%ct', "HEAD"])
            global_hash_time = subprocess.check_output(['git', 'show', '-s', '--format=%ct', hash_global,
                                                        "--", f"origin/{REMOTE_BRANCH}"])
            if hash_global != hash_local:
                return True, hash_global, hash_local, int(our_hash_time), int(global_hash_time)
            else:
                return False, '', '', 0, 0
    except subprocess.CalledProcessError:
        return False, "", "", 0, 0


def update_to(git_hash: str) -> (bool, str):
    """
    Update to this hash from remote
    :param git_hash: the hash to update to
    :return: whether it succeeded
    """
    try:
        subprocess.check_output(['git', 'fetch', 'origin', git_hash]).decode('ascii').strip()
        subprocess.check_output(['git', 'checkout', git_hash]).decode('ascii').strip()
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, str(e)
