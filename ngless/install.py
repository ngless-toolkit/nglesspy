import sys
from os import path, chmod
import requests

NGLESS_DOWNLOAD_URL = 'http://ngless.embl.de/releases/ngless-0.8.1-Linux64'

def _http_download_file(url, ofile):
    '''Download from `url` to `ofile`'''
    from contextlib import closing
    with closing(requests.get(url, stream=True)) as ifile, \
                open(ofile, 'wb') as ofile:
        for chunk in ifile.iter_content(8192):
            ofile.write(chunk)

def _find_target(mode, target):
    if target is not None:
        return target
    if mode == 'user':
        return path.expanduser('~/.local/bin/ngless')
    if mode == 'root':
        return '/usr/local/bin/ngless'
    raise ValueError("Could not determine installation target")

def install_ngless(mode='user', target=None, force=False, verbose=True):
    '''Install ngless

    By default, this function **will not** overwrite existing files (set the
    `force` argument for that).


    Arguments
    ---------
    mode : str, optional
        Whether to install in 'user' mode or 'root' mode
    target : str, optional
        Alternatively, specify the path onto which to install NGLess
    force : bool, optional
        Whether to install even if file already exists (default: False)
    verbose : bool, optional
        If True (default), print information messages

    Returns
    -------
    installed : bool
        whether a file was indeed installed
    '''
    target_path = _find_target(mode, target)
    if path.exists(target_path) and not force:
        return False
    else:
        if not sys.platform.startswith('linux'):
            raise NotImplementedError("""
install_ngless is only implemented on Linux (detected platform: {}).

Please see the ngless webpage: http://ngless.embl.de for more information on how to install NGLess on your system.""".format(sys.platform))
        if verbose:
            print("Downloading file to {}".format(target_path))
        _http_download_file(NGLESS_DOWNLOAD_URL, target_path)
        chmod(target_path, 0o555)        
        if verbose:
            print("Download complete.")
        return True

