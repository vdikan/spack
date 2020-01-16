# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class AtomDft(MakefilePackage):
    """ATOM is a program for DFT calculations in atoms and pseudopotential
       generation."""

    homepage = "https://departments.icmab.es/leem/siesta/Pseudopotentials/"
    url      = "https://departments.icmab.es/leem/SIESTA_MATERIAL/Pseudos/Code/atom-4.2.7-100.tgz"

    maintainers = ['vdikan']

    version('4.2.7', sha256='266a4119e64ca398444df7bc2f5004513891f2189cba33595a1742c64f8f3edc',
            url="https://departments.icmab.es/leem/SIESTA_MATERIAL/Pseudos/Code/atom-4.2.7-100.tgz")

    depends_on('libgridxc')
    depends_on('xmlf90')

    def edit(self, spec, prefix):
        copy('arch.make.sample', 'arch.make')

    # TODO: Refactor this
    @property
    def build_targets(self):
        if '+libxc' in self.spec['libgridxc']:
            return ['XMLF90_ROOT=%s' % self.spec['xmlf90'].prefix,
                    'LIBXC_ROOT=%s' % self.spec['libxc'].prefix,
                    'GRIDXC_ROOT=%s' % self.spec['libgridxc'].prefix,
                    'FC=fc']

        return ['XMLF90_ROOT=%s' % self.spec['xmlf90'].prefix,
                'GRIDXC_ROOT=%s' % self.spec['libgridxc'].prefix,
                'FC=fc']


    def install(self, spec, prefix):
        mkdir(prefix.bin)
        install('atm', prefix.bin)
