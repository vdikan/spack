# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class Flook(MakefilePackage):
    """The fortran-Lua-hook library.

    It allows abstraction of input files to be pure Lua files to enable configuration of internal variables through an embedded Lua interpreter.
    """

    homepage = "https://github.com/ElectronicStructureLibrary/flook"
    url      = "https://github.com/ElectronicStructureLibrary/flook"

    maintainers = ['pfebrer']

    version('0.8.1', sha256='c0da954f1e9d1cc39b62b07285c5f2e26109fa659c1b340994b633b55141f274',
        url="https://github.com/ElectronicStructureLibrary/flook/archive/v0.8.1.zip")

    build_targets = ["liball"]

    def edit(self, spec, prefix):

        setupmake_lines = [
            f"CC = {env['CC']}",
            f"FC = {env['FC']}",
            "CFLAGS = -g",
            "FFLAGS = -g",
            ".f90.o:",
            "\t$(FC) -c $(FFLAGS) $(INC) $<",
            ".F90.o:",
            "\t$(FC) -c $(FFLAGS) $(INC) $<",
            ".c.o:",
            "\t$(CC) -c $(CFLAGS) $(INC) $<]"
        ]

        setupmake_content = "\n".join(setupmake_lines)

        with open('setup.make', 'w') as setupmake:
            setupmake.write(setupmake_content)
    
    def install(self, spec, prefix):
        mkdir(prefix.lib)
        install("*.a", prefix.lib)

        mkdir(prefix.include)
        install("*.mod", prefix.include)