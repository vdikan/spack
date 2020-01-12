# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from __future__ import print_function
import re
import argparse
import errno
import sys


# NOTE: The only reason we subclass argparse.HelpFormatter is to get access
# to self._expand_help(), ArgparseWriter is not intended to be used as a
# formatter_class.
class ArgparseWriter(argparse.HelpFormatter):
    """Analyzes an argparse ArgumentParser for easy generation of help."""

    def __init__(self, prog, out=sys.stdout, aliases=False):
        """Initializes a new ArgparseWriter instance.

        Parameters:
            prog (str): the program name
            out (file object): the file to write to
            aliases (bool): whether or not to include subparsers for aliases
        """
        super(ArgparseWriter, self).__init__(prog)
        self.level = 0
        self.prog = prog
        self.out = out
        self.aliases = aliases

    def parse(self, parser, prog):
        """Parses the parser object and returns the relavent components.

        Parameters:
            parser (argparse.ArgumentParser): the parser
            prog (str): the command name

        Returns:
            str: the command name
            str: the command description
            str: the command usage
            list: list of positional arguments
            list: list of optional arguments
            list: list of subcommand parsers
        """
        self.parser = parser

        split_prog = parser.prog.split(' ')
        split_prog[-1] = prog
        prog = ' '.join(split_prog)
        description = parser.description

        fmt = parser._get_formatter()
        actions = parser._actions
        groups = parser._mutually_exclusive_groups
        usage = fmt._format_usage(None, actions, groups, '').strip()

        # Go through actions and split them into optionals, positionals,
        # and subcommands
        optionals = []
        positionals = []
        subcommands = []
        for action in actions:
            if action.option_strings:
                flags = action.option_strings
                dest_flags = fmt._format_action_invocation(action)
                help = self._expand_help(action) if action.help else ''
                help = help.replace('\n', ' ')
                optionals.append((flags, dest_flags, help))
            elif isinstance(action, argparse._SubParsersAction):
                for subaction in action._choices_actions:
                    subparser = action._name_parser_map[subaction.dest]
                    subcommands.append((subparser, subaction.dest))

                    # Look for aliases of the form 'name (alias, ...)'
                    if self.aliases:
                        match = re.match(r'(.*) \((.*)\)', subaction.metavar)
                        if match:
                            aliases = match.group(2).split(', ')
                            for alias in aliases:
                                subparser = action._name_parser_map[alias]
                                subcommands.append((subparser, alias))
            else:
                args = fmt._format_action_invocation(action)
                help = self._expand_help(action) if action.help else ''
                help = help.replace('\n', ' ')
                positionals.append((args, help))

        return prog, description, usage, positionals, optionals, subcommands

    def format(self, prog, description, usage,
               positionals, optionals, subcommands):
        """Returns the string representation of a single node in the
        parser tree.

        Override this in subclasses to define how each subcommand
        should be displayed.

        Parameters:
            prog (str): the command name
            description (str): the command description
            usage (str): the command usage
            positionals (list): list of positional arguments
            optionals (list): list of optional arguments
            subcommands (list): list of subcommand parsers

        Returns:
            str: the string representation of this subcommand
        """
        raise NotImplementedError

    def _write(self, parser, prog, level=0):
        """Recursively writes a parser.

        Parameters:
            parser (argparse.ArgumentParser): the parser
            prog (str): the command name
            level (int): the current level
        """
        self.level = level

        args = self.parse(parser, prog)
        self.out.write(self.format(*args))

        subcommands = args[-1]
        for subparser, prog in subcommands:
            self._write(subparser, prog, level=level + 1)

    def write(self, parser):
        """Write out details about an ArgumentParser.

        Args:
            parser (argparse.ArgumentParser): the parser
        """
        try:
            self._write(parser, self.prog)
        except IOError as e:
            # Swallow pipe errors
            # Raises IOError in Python 2 and BrokenPipeError in Python 3
            if e.errno != errno.EPIPE:
                raise


_rst_levels = ['=', '-', '^', '~', ':', '`']


class ArgparseRstWriter(ArgparseWriter):
    """Write argparse output as rst sections."""

    def __init__(self, prog, out=sys.stdout, rst_levels=_rst_levels):
        """Create a new ArgparseRstWriter.

        Parameters:
            prog (str): program name
            out (file object): file to write to
            rst_levels (list of str): list of characters
                for rst section headings
        """
        super(ArgparseRstWriter, self).__init__(prog, out)
        self.rst_levels = rst_levels

    def format(self, prog, description, usage,
               positionals, optionals, subcommands):
        string = self.begin_command(prog)

        if description:
            string += self.description(description)

        string += self.usage(usage)

        if positionals:
            string += self.begin_positionals()
            for args, help in positionals:
                string += self.positional(args, help)
            string += self.end_positionals()

        if optionals:
            string += self.begin_optionals()
            for flags, dest_flags, help in optionals:
                string += self.optional(dest_flags, help)
            string += self.end_optionals()

        if subcommands:
            string += self.begin_subcommands(subcommands)

        return string

    def begin_command(self, prog):
        return """
----

.. _{0}:

{1}
{2}

""".format(prog.replace(' ', '-'), prog,
           self.rst_levels[self.level] * len(prog))

    def description(self, description):
        return description + '\n\n'

    def usage(self, usage):
        return """\
.. code-block:: console

    {0}

""".format(usage)

    def begin_positionals(self):
        return '\n**Positional arguments**\n\n'

    def positional(self, name, help):
        return """\
{0}
  {1}

""".format(name, help)

    def end_positionals(self):
        return ''

    def begin_optionals(self):
        return '\n**Optional arguments**\n\n'

    def optional(self, opts, help):
        return """\
``{0}``
  {1}

""".format(opts, help)

    def end_optionals(self):
        return ''

    def begin_subcommands(self, subcommands):
        string = """
**Subcommands**

.. hlist::
   :columns: 4

"""

        for cmd, _ in subcommands:
            prog = cmd.prog
            string += '   * :ref:`{0} <{1}>`\n'.format(
                prog, prog.replace(' ', '-'))

        return string + '\n'


class ArgparseCompletionWriter(ArgparseWriter):
    """Write argparse output as shell programmable tab completion functions."""

    def __init__(self, prog, out=sys.stdout, aliases=True):
        """Initializes a new ArgparseWriter instance.

        Parameters:
            prog (str): the program name
            out (file object): the file to write to
            aliases (bool): whether or not to include subparsers for aliases
        """
        super(ArgparseCompletionWriter, self).__init__(prog, out, aliases)

    def format(self, prog, description, usage,
               positionals, optionals, subcommands):
        """Returns the string representation of a single node in the
        parser tree.

        Override this in subclasses to define how each subcommand
        should be displayed.

        Parameters:
            prog (str): the command name
            description (str): the command description
            usage (str): the command usage
            positionals (list): list of positional arguments
            optionals (list): list of optional arguments
            subcommands (list): list of subcommand parsers

        Returns:
            str: the string representation of this subcommand
        """

        assert optionals  # we should always at least have -h, --help
        assert not (positionals and subcommands)  # one or the other, not both

        # We only care about the arguments/flags, not the help messages
        if positionals:
            positionals, _ = zip(*positionals)
        optionals, _, _ = zip(*optionals)
        if subcommands:
            _, subcommands = zip(*subcommands)

        # Flatten lists of lists
        optionals = [x for xx in optionals for x in xx]

        return self.start_function(prog) + \
            self.body(positionals, optionals, subcommands) + \
            self.end_function(prog)

    def start_function(self, prog):
        """Returns the syntax needed to begin a function definition.

        Parameters:
            prog (str): the command name

        Returns:
            str: the function definition beginning
        """
        name = prog.replace('-', '_').replace(' ', '_')
        return '_{0} () {{'.format(name)

    def end_function(self, prog=None):
        """Returns the syntax needed to end a function definition.

        Parameters:
            prog (str, optional): the command name

        Returns:
            str: the function definition ending
        """
        return '}\n\n'

    def body(self, positionals, optionals, subcommands):
        """Returns the body of the function.

        Parameters:
            positionals (list): list of positional arguments
            optionals (list): list of optional arguments
            subcommands (list): list of subcommand parsers

        Returns:
            str: the function body
        """
        return ''

    def positionals(self, positionals):
        """Returns the syntax for reporting positional arguments.

        Parameters:
            positionals (list): list of positional arguments

        Returns:
            str: the syntax for positional arguments
        """
        return ''

    def optionals(self, optionals):
        """Returns the syntax for reporting optional flags.

        Parameters:
            optionals (list): list of optional arguments

        Returns:
            str: the syntax for optional flags
        """
        return ''

    def subcommands(self, subcommands):
        """Returns the syntax for reporting subcommands.

        Parameters:
            subcommands (list): list of subcommand parsers

        Returns:
            str: the syntax for subcommand parsers
        """
        return ''
