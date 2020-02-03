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

    maintainers = ['vdikan']

    version('4.1', sha256='19fa19a23adefb9741a436c6b5dbbdc0f57fb66876883f8f9f6695dfe7574fe3',
            url='https://launchpad.net/siesta/4.1/4.1-b4/+download/siesta-4.1-b4.tar.gz')
    # version('4.0.1', sha256='bfb9e4335ae1d1639a749ce7e679e739fdead5ee5766b5356ea1d259a6b1e6d1', url='https://launchpad.net/siesta/4.0/4.0.1/+download/siesta-4.0.1.tar.gz')
    # version('3.2-pl-5', sha256='e438bb007608e54c650e14de7fa0b5c72562abb09cbd92dcfb5275becd929a23', url='http://departments.icmab.es/leem/siesta/CodeAccess/Code/siesta-3.2-pl-5.tgz')

    variant('mpi', default=True, description='Build parallel version with MPI')

    patch('gfortran.make.patch', when='%gcc')
    patch('intel.make.patch', when='%intel')

    depends_on('mpi', when='+mpi')
    depends_on('blas')
    depends_on('lapack')
    depends_on('scalapack', when='+mpi')
    depends_on('netcdf-c')
    depends_on('netcdf-fortran')

    phases = ['edit', 'build', 'install']

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

            if '+mpi' in self.spec:
                if spec.satisfies('%gcc'):
                    archmake.filter('^FC = .*', 'FC = mpif90')
                elif spec.satisfies('%intel'):
                    archmake.filter('^FC = .*', 'FC = mpifort')

            archmake.filter('^BLAS_LIBS\s=',
                            'BLAS_LIBS = {0}'.format(self.spec['blas'].libs.ld_flags))
            archmake.filter('^LAPACK_LIBS\s=',
                            'LAPACK_LIBS = {0}'.format(self.spec['lapack'].libs.ld_flags))
            if '+mpi' in self.spec:
                archmake.filter('^SCALAPACK_LIBS\s=',
                                'SCALAPACK_LIBS = {0}'.format(self.spec['scalapack'].libs.ld_flags))

            archmake.filter('^COMP_LIBS\s=.*',
                            'COMP_LIBS = # Empty: BLAS and LAPACK are Spack dependencies.')

            fflags = '-O2'      # TODO: find alteration of compiler flags
            fflags += ' ' + self.compiler.pic_flag
            archmake.filter('^FFLAGS = .*', 'FFLAGS = ' + fflags)

            # fppflags = '-DGRID_DP -DCDF'
            fppflags = '-DGRID_DP'
            if '+mpi' in self.spec:
                fppflags = '-DMPI {0}'.format(fppflags)

            archmake.filter('^FPPFLAGS\+=', 'FPPFLAGS+= {0}'.format(fppflags))


    def build(self, spec, prefix):
        with working_dir('Obj'):
            make()
        # with working_dir('Util'):
        #     sh = which('sh')
        #     sh('build_all.sh')


    def install(self, spec, prefix):
        mkdir(prefix.bin)
        with working_dir('Obj'):
            install('siesta', prefix.bin)
        # with working_dir('Obj_trans'):
        #     install('transiesta', prefix.bin)
        # for root, _, files in os.walk('Util'):
        #     for fname in files:
        #         fname = join_path(root, fname)
        #         if os.access(fname, os.X_OK):
        #             install(fname, prefix.bin)
