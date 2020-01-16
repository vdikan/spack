# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class Libgridxc(Package):
    """A library to compute the exchange and correlation energy and potential
       in spherical (i.e. an atom) or periodic systems."""

    homepage = "https://siesta-project.github.io/gridxc-docs"
    url      = "https://launchpad.net/libgridxc/trunk/0.8/+download/libgridxc-0.8.5.tgz"

    def url_for_version(self, version):
        url = "https://launchpad.net/libgridxc/trunk/{0}/+download/libgridxc-{1}.tgz"
        return url.format(version.up_to(2), version)

    maintainers = ['vdikan']

    version('0.8.5', sha256='66192e2d3379677d6687510915d7b24ffefeec96899b0bbf2adeec63a1d83c26')
    # 0.7.6 has problems with finding libxc.mk
    # version('0.7.6', sha256='ecf88ea68b9dbbdae3e86c8d598aee63b134f2f2d0e879fdedc06544b8267b91')

    variant('mpi', default=True, description='Builds an MPI-parallelized version of the library')
    variant('libxc', default=True, description='Builds with libXC support. Recommended.')

    depends_on('mpi', when='+mpi')
    depends_on('libxc', when='+libxc')

    def make_args(self):
        args = ['PREFIX=%s' % self.prefix]

        if '+mpi' in self.spec:
            args.append('WITH_MPI=1')

        if '+libxc' in self.spec:
            args.append('WITH_LIBXC=1')

        return args

    phases = ['configure', 'install']


    def line_prepender(self, filename, line):
        with open(filename, 'r+') as f:
            content = f.read()
            f.seek(0, 0)
            f.write(line.rstrip('\r\n') + '\n' + content)


    def configure(self, spec, prefix):
        sh = which('sh')
        with working_dir('build', create=True):
            sh('../src/config.sh')
            copy('../extra/fortran.mk', 'fortran.mk')

            if '+libxc' in self.spec:
                self.line_prepender('fortran.mk',
                                    'LIBXC_ROOT=%s' % spec['libxc'].prefix)


    def install(self, spec, prefix):
        mymake=Executable('make')
        with working_dir('build'):
            mymake(*self.make_args())
