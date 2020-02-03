# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack import *
import os


class Siesta(MakefilePackage):
    """SIESTA performs electronic structure calculations and ab initio molecular
       dynamics simulations of molecules and solids."""

    homepage = "https://departments.icmab.es/leem/siesta/"

    version('4.1', sha256='19fa19a23adefb9741a436c6b5dbbdc0f57fb66876883f8f9f6695dfe7574fe3',
            url='https://launchpad.net/siesta/4.1/4.1-b4/+download/siesta-4.1-b4.tar.gz')
    # version('4.0.1', sha256='bfb9e4335ae1d1639a749ce7e679e739fdead5ee5766b5356ea1d259a6b1e6d1', url='https://launchpad.net/siesta/4.0/4.0.1/+download/siesta-4.0.1.tar.gz')
    # version('3.2-pl-5', sha256='e438bb007608e54c650e14de7fa0b5c72562abb09cbd92dcfb5275becd929a23', url='http://departments.icmab.es/leem/siesta/CodeAccess/Code/siesta-3.2-pl-5.tgz')

    patch('gfortran.make.patch', when='%gcc')
    patch('intel.make.patch', when='%intel')

    depends_on('mpi')
    # depends_on('blas')
    # depends_on('lapack')
    # depends_on('scalapack')
    depends_on('netcdf-c')
    depends_on('netcdf-fortran')

    # phases = ['edit', 'build', 'install']
    phases = ['edit', 'build']

    def edit(self, spec, prefix):
        sh = which('sh')
        with working_dir('Obj'):
            sh('../Src/obj_setup.sh')
            if spec.satisfies('%gcc'):
                copy('gfortran.make', 'arch.make')
            elif spec.satisfies('%intel'):
                copy('intel.make', 'arch.make')
            else:
                tty.error("Known compilers are: gcc, intel.")

            archmake = FileFilter('arch.make')
            archmake.filter('SIESTA_ARCH = .*', 'SIESTA_ARCH = ' +
                            '_'.join([spec.target.name,
                                      spec.platform, spec.os]))

            fflags = '-O2'      # TODO: find alteration of compiler flags
            fflags += ' ' + self.compiler.pic_flag
            archmake.filter('FFLAGS = .*', 'FFLAGS = ' + fflags)

            fppflags = '-DGRID_DP -DCDF'
            if '+mpi' in self.spec:
                fppflags = '-DMPI {0}'.format(fppflags)

            archmake.filter('FPPFLAGS\+=', 'FPPFLAGS+= {0}'.format(fppflags))


    def build(self, spec, prefix):
        with working_dir('Obj'):
            make()
        # with working_dir('Util'):
        #     sh = which('sh')
        #     sh('build_all.sh')


    # def install(self, spec, prefix):
        # mkdir(prefix.bin)
        # with working_dir('Obj'):
        #     install('siesta', prefix.bin)
        # with working_dir('Obj_trans'):
        #     install('transiesta', prefix.bin)
        # for root, _, files in os.walk('Util'):
        #     for fname in files:
        #         fname = join_path(root, fname)
        #         if os.access(fname, os.X_OK):
        #             install(fname, prefix.bin)
