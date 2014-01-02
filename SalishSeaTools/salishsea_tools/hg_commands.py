"""A library of Python functions for working with Mercurial
via its command line interface.
This is a utility library that is used by other Python packages
and modules developed for the Salish Sea MEOPAR project.
"""
from __future__ import absolute_import
"""
Copyright 2013-2014 The Salish Sea MEOPAR contributors
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
    'default_url',
    'heads',
]


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
        return subprocess.check_output(cmd).strip()
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
    return subprocess.check_output(cmd)
