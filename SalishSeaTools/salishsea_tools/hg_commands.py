"""A library of Python functions for working with Mercurial
via its command line interface.
This is a utility library that is used by other Python packages
and modules developed for the Salish Sea MEOPAR project.
"""
from __future__ import absolute_import
"""
Copyright 2013-2016 The Salish Sea MEOPAR contributors
and The University of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import subprocess


__all__ = [
    'commit',
    'default_url',
    'heads',
    'parents',
]


def commit(logfile):
    """Commit all changes in the repo with the contents of logfile
    as the commit message.

    :arg logfile: Name of the file containing the commit message.
    :type logfile: str
    """
    cmd = ['hg', 'commit', '--logfile', logfile]
    subprocess.check_call(cmd)


def default_url(repo=None):
    """Return the result of the :command:`hg paths default` command.

    If repo is given the :command:`hg -R repo paths default` command
    is run. The repo argument must be the root directory of a Mercurial
    repository.

    If the :program:`hg` command fails :py:obj:`None` is returned.

    :arg repo: Repository root directory.
    :type repo: str

    :returns: Output of the command or :py:obj:`None`.
    """
    cmd = ['hg']
    if repo is not None:
        cmd.extend(['-R', repo])
    cmd.extend(['paths', 'default'])
    try:
        return subprocess.check_output(
            cmd, universal_newlines=True).strip()
    except subprocess.CalledProcessError:
        return None


def heads(repo, revs=['.']):
    """Return the result of the :command:`hg -R repo heads revs` command.

    :arg repo: Repository root directory.
    :type repo: str

    :arg revs: Revisions for which to show branch heads.
               The default :kbd:`.` causes the head(s) of the currently
               checked out branch to be returned.
    :type revs: list

    :returns: Output of the command.
    :rtype: str
    """
    cmd = ['hg', '-R', repo, 'heads'] + revs
    return subprocess.check_output(cmd, universal_newlines=True)


def parents(repo=None, rev=None, file=None, verbose=False):
    """Return the result of the :command:`hg parents` command.

    If repo is given the :command:`hg parents -R repo` command is run.
    The repo argument must be the root directory of a Mercurial repository.

    If rev is given the :command:`hg parents -r rev` command is run.
    Only one rev may be given.

    If file is given the :command:`hg parents file` command is run.
    Only one file may be given.

    If verbose is True the :command:`hg parents -v` command is run.

    Keyword argument can be used cumulatively;
    e.g. :kbd:`repo=foo, file=bar` will result in the
    :command:`hg parents -R foo bar` command being run.

    :arg repo: Repository root directory.
    :type repo: str

    :arg rev: Revision to get the parents of.
              May be either an integer or a hash string.
    :type ref: int or str

    :arg file: File path and name to get the parents of.
    :type file: str

    :arg verbose: Control verbosity of :command:`hg` command;
                  default to :kbd:`False` meaning to run the command
                  without the :kbd:`-v` flag.
    :type verbose: Boolean

    :returns: Output of the command.
    :rtype: str
    """
    cmd = ['hg', 'parents']
    if repo is not None:
        cmd.extend(['-R', repo])
    if rev is not None:
        cmd.extend(['-r', rev])
    if file is not None:
        cmd.append(file)
    if verbose:
        cmd.append('-v')
    return subprocess.check_output(cmd, universal_newlines=True)
