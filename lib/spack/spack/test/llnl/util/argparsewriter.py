# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

"""Tests for ``llnl/util/argparsewriter.py``

These tests are fairly minimal, and ArgparseWriter is more extensively
tested in ``cmd/commands.py``.
"""

import pytest

import llnl.util.argparsewriter as aw


def test_format_not_overridden():
    writer = aw.ArgparseWriter('spack')

    with pytest.raises(NotImplementedError):
        writer.write()
