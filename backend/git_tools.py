import subprocess


def get_git_revision_short_hash() -> str:
    """
    Get the local git repository's commit version, or "not running in git" if it doesn't exist
    :return: the commit version
    """
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "not running in git"
