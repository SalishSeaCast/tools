"""Marlin command plug-ins for SVN-ish commands.

Copyright 2015-2016 The Salish Sea MEOPAR Contributors
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
import logging
import tempfile
import sys

import arrow
import cliff.command
import pysvn

from salishsea_tools import hg_commands


__all__ = [
    'SVNIncoming', 'SVNUpdate',
    'get_working_copy_info', 'get_working_copy_rev', 'get_upstream_url',
    'get_upstream_logs', 'apply_update',
]


HEAD = pysvn.Revision(pysvn.opt_revision_kind.head)


class SVNIncoming(cliff.command.Command):
    """Display SVN log of revisions that have not yet been brought in
    from the upstream repo.
    """
    def get_parser(self, prog_name):
        parser = super(SVNIncoming, self).get_parser(prog_name)
        parser.add_argument(
            '-l', '--limit',
            type=int,
            default=1,
            help='maximum number of log messages to show; defaults to 1',
        )
        return parser

    def take_action(self, parsed_args):
        svn_logs = get_upstream_logs(limit=parsed_args.limit)
        for chunk in self._format(svn_logs):
            sys.stdout.write(chunk)

    def _format(self, svn_logs):
        for svn_log in svn_logs:
            timestamp = arrow.get(svn_log.date)
            chunk = (
                'r{0.revision.number} {1} UTC\n'
                '  {0.message}'
                '\n'
                .format(svn_log, timestamp.format('YYYY-MM-DD HH:mm:ss'))
            )
            yield chunk


class SVNUpdate(cliff.command.Command):
    """Apply SVN updates from upstream repo & commit them to Mercurial
    one at a time.
    """
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SVNUpdate, self).get_parser(prog_name)
        parser.add_argument(
            '--to-rev',
            type=int,
            help='SVN revision number to update repo to',
        )
        return parser

    def take_action(self, parsed_args):
        end_rev = parsed_args.to_rev
        limit = 1 if end_rev is None else 0
        svn_logs = get_upstream_logs(limit)
        end_rev = svn_logs[0].revision.number if end_rev is None else end_rev
        for svn_log in svn_logs:
            if svn_log.revision.number > end_rev:
                break
            apply_update(svn_log.revision.number)
            hg_commit_msg = (
                'Update to svn r{0.revision.number}.'
                '\n\n'
                '{0.message}'
                .format(svn_log)
            )
            with tempfile.NamedTemporaryFile() as msg_file:
                msg_file.write(hg_commit_msg)
                msg_file.flush()
                hg_commands.commit(logfile=msg_file.name)
            self.log.info(hg_commit_msg + '\n')


def get_working_copy_info(path='.'):
    client = pysvn.Client()
    info = client.info(path)
    return info


def get_working_copy_rev(path='.'):
    info = get_working_copy_info()
    return info.revision.number


def get_upstream_url(path='.'):
    info = get_working_copy_info()
    return info.url


def get_upstream_logs(limit=0):
    limit = limit + 1 if limit != 0 else 0
    url = get_upstream_url()
    tip_rev = pysvn.Revision(
        pysvn.opt_revision_kind.number, get_working_copy_rev())
    client = pysvn.Client()
    svn_logs = client.log(
        url,
        revision_start=tip_rev,
        revision_end=HEAD,
        limit=limit,
    )
    return svn_logs[1:]


def apply_update(revision, path='.'):
    client = pysvn.Client()
    rev = pysvn.Revision(pysvn.opt_revision_kind.number, revision)
    tip_rev = client.update(path, revision=rev)
    return tip_rev
