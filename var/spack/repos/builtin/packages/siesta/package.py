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

    # TODO: add older versions as well as those new from git that use LibXC & PSML
    version('4.1', sha256='19fa19a23adefb9741a436c6b5dbbdc0f57fb66876883f8f9f6695dfe7574fe3',
            url='https://launchpad.net/siesta/4.1/4.1-b4/+download/siesta-4.1-b4.tar.gz')
    # version('4.0.1', sha256='bfb9e4335ae1d1639a749ce7e679e739fdead5ee5766b5356ea1d259a6b1e6d1', url='https://launchpad.net/siesta/4.0/4.0.1/+download/siesta-4.0.1.tar.gz')
    # version('3.2-pl-5', sha256='e438bb007608e54c650e14de7fa0b5c72562abb09cbd92dcfb5275becd929a23', url='http://departments.icmab.es/leem/siesta/CodeAccess/Code/siesta-3.2-pl-5.tgz')

    variant('mpi', default=True, description='Build parallel version with MPI.')
    variant('psml', default=True,
            description='Build with support for pseudopotentials in PSML format.')
    variant('gridxc', default=True,
            description='Build SIESTA that uses XC energies and potrntials from LibGridXC.')
    variant('libxc', default=False,
            description='Build SIESTA that uses XC-functionals via LibXC.')

    patch('gfortran.make.patch', when='%gcc')
    patch('intel.make.patch', when='%intel')

    depends_on('mpi', when='+mpi')
    depends_on('blas')
    depends_on('lapack')
    depends_on('scalapack', when='+mpi') # NOTE: cannot ld-link without scalapack when +mpi
    depends_on('netcdf-c')
    depends_on('netcdf-fortran')
    depends_on('xmlf90', when='+psml')
    depends_on('libpsml', when='+psml')

    # TODO: use external XC-deps for those versions that deserve them
    depends_on('libgridxc ~libxc', when='+gridxc~libxc')
    depends_on('libgridxc +libxc', when='+libxc')

    conflicts('+libxc', when='~gridxc', msg='Need GridXC built with LibXC to utilize `+libxc`.')

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

            include_section_tag = '# Include_section:'
            include_mks = [include_section_tag]
            if '+psml' in self.spec:
                include_mks.append(
                    'include {0}/share/org.siesta-project/xmlf90.mk'.format(
                        self.spec['xmlf90'].prefix))
                include_mks.append(
                    'include {0}/share/org.siesta-project/psml.mk'.format(
                        self.spec['libpsml'].prefix))

            if '+gridxc' in self.spec:
                include_mks.append('GRIDXC_ROOT = {0}'.format(self.spec['libgridxc'].prefix))

                # NOTE: For the "flat" dependencies we have in Siesta it's okay
                # to link LibXC with dependant GridXC here... but that's in general
                # bad practice that does not fit the Spack's ideology.
                # At least `gridxc_dp.mk` should be patched to bear the info about LibXC it
                # was built with, as happens now with PSML and Xmlf90,
                # for the sake of transferability and Great Justice!
                if '+libxc' in self.spec:
                    include_mks.append(
                        'LIBXC_ROOT =  {0}'.format(self.spec['libxc'].prefix))

                if self.spec['libgridxc'].satisfies('@:0.8'):
                    include_mks.append(
                        'include {0}/gridxc.mk'.format(self.spec['libgridxc'].prefix))
                else:           # FIXME: proper check for versions higher than 9.0
                    include_mks.append(
                        'include {0}/share/org.siesta-project/gridxc_dp.mk'.format(
                            self.spec['libgridxc'].prefix))

            archmake.filter('^' + include_section_tag, '\n'.join(include_mks))

            incflags_plus = self.spec['netcdf-fortran'].headers.cpp_flags
            archmake.filter('^NETCDF_LIBS\s=.*',
                            'NETCDF_LIBS = {0}'.format(
                                self.spec['netcdf-fortran'].libs.ld_flags
                            ))

            if '~mpi' in self.spec:
                archmake.filter('^MPI_INTERFACE=.*',
                                'MPI_INTERFACE=  # None: ordered serial version.')
                archmake.filter('^MPI_INCLUDE=\.', '')

            fflags = '-O2'      # TODO: find alteration of compiler flags
            fflags += ' ' + self.compiler.pic_flag
            archmake.filter('^FFLAGS = .*', 'FFLAGS = ' + fflags)

            fppflags = '-DGRID_DP -DCDF'
            if '+mpi' in self.spec:
                fppflags = '-DMPI {0}'.format(fppflags)

            archmake.filter('^FPPFLAGS\+=', 'FPPFLAGS+= {0}'.format(fppflags))

            archmake.filter('^INCFLAGS\+=', 'INCFLAGS+= {0}'.format(incflags_plus))


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
