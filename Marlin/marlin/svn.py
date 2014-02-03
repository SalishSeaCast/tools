"""Marlin command plug-ins for SVN-ish commands.

Copyright 2014 The Salish Sea MEOPAR Contributors
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
import sys

import arrow
import cliff.command
import pysvn


__all__ = [
    'SVNIncoming',
    'get_working_copy_info', 'get_working_copy_rev', 'get_upstream_url',
    'get_upstream_log',
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
        tip_rev = pysvn.Revision(
            pysvn.opt_revision_kind.number, get_working_copy_rev())
        svn_logs = get_upstream_log(
            revision_start=tip_rev,
            limit=parsed_args.limit + 1,
        )
        for chunk in self._format(svn_logs[1:]):
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

def get_upstream_log(revision_start, revision_end=HEAD, limit=0):
    url = get_upstream_url()
    client = pysvn.Client()
    svn_logs = client.log(
        url,
        revision_start=revision_start,
        revision_end=revision_end,
        limit=limit,
    )
    return svn_logs
