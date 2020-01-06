# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from __future__ import print_function

import sys
import re

from llnl.util.argparsewriter import ArgparseWriter

import spack.main


description = "generate shell code for tab completion"
section = "developer"
level = "long"


class StackEntry():
    def __init__(self):
        self.optionals = []
        self.subcommands = []


class SpackBashCompletionWriter(ArgparseWriter):
    def __init__(self, out=sys.stdout):
        super(SpackBashCompletionWriter, self).__init__(out)
        self.stack = []

    def begin_command(self, name):
        self.stack.append(StackEntry())

    def optional(self, opts, help):
        cmd = self.stack[-1]

        # get rid of choice lists like {true false}
        opts = re.sub(r'\{[^}]*\}', '', opts).strip()

        # get rid of metavars (which do not start with `-`)
        opts = [opt for opt in re.split(r',?\s+', opts) if opt.startswith('-')]
        cmd.optionals.extend(opts)

    def begin_subcommands(self, subcommands):
        cmd = self.stack[-1]
        for full_cmd in subcommands:
            parts = re.split(r'\s+', full_cmd.prog)
            cmd.subcommands.append(parts[-1])

    def end_command(self, name):
        cmd = self.stack.pop()
        print("function _%s {" % name.replace(" ", "_"))
        print("    if $list_options")
        print("    then")
        print('        compgen -W "%s" -- "$cur"' % " ".join(cmd.optionals))
        if cmd.subcommands:
            print("    else")
            print('        compgen -W "%s" -- "$cur"' % " ".join(cmd.subcommands))
        print("    fi")
        print("}\n")


def completion(parser, args):
    parser = spack.main.make_argument_parser()
    spack.main.add_all_commands(parser)

    writer = SpackBashCompletionWriter()
    writer.write(parser)
