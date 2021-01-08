# Copyright 2020 The SIESTA group
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
    git      = "https://gitlab.com/siesta-project/siesta.git"

    maintainers = ['vdikan']

    # version('psml',  branch='psml-support')

    version('4.1-b4', sha256='19fa19a23adefb9741a436c6b5dbbdc0f57fb66876883f8f9f6695dfe7574fe3',
            url='https://launchpad.net/siesta/4.1/4.1-b4/+download/siesta-4.1-b4.tar.gz')

    variant('mpi', default=True, description='Build parallel version with MPI.')
    # variant('psml', default=True,
    #         description='Build with support for pseudopotentials in PSML format.')
    variant('utils', default=True, description='Build the utilities suit bundled with SIESTA (./Util dir).')

    # conflicts('-psml', when='@psml', msg='Experimental PSML branch needs `+psml`.')
    # conflicts('-mpi', when='@psml',  msg='Experimental PSML branch needs MPI (bug?).')
    # conflicts('-gridxc', when='+psml', msg='PSML requires LibGridXC.')

    depends_on('mpi', when='+mpi')
    depends_on('blas')
    depends_on('lapack')
    depends_on('scalapack', when='+mpi') # NOTE: cannot ld-link without scalapack when +mpi
    depends_on('netcdf-c')
    depends_on('netcdf-fortran') # TODO: CDF4
    depends_on('libxc@3.0.0') # NOTE: hard-wired libxc version, Siesta does not link against newer ones yet

    depends_on('libgridxc +libxc ~mpi', when='~mpi')
    depends_on('libgridxc +libxc +mpi', when='+mpi')

    # depends_on('xmlf90', when='+psml')
    # depends_on('libpsml', when='+psml')

    phases = ['edit', 'build', 'install']

    @property
    def final_fflags_string(self):
        return ' '.join(self.spec.compiler_flags['fflags'] + [
            self.compiler.fc_pic_flag,
        ])


    @property
    def final_fppflags_string(self):
        fppflags = ['-DGRID_DP', '-DCDF']
        if '+mpi' in self.spec:
            fppflags.append('-DMPI')

        return ' '.join(fppflags)


    @property
    def final_incflags_string(self):
        return self.spec['netcdf-fortran'].headers.cpp_flags


    @property
    def archmake_lp_content(self):
        "Archmake content list for the `stable` version hosted on launchpad."
        spec = self.spec
        conf = ['.SUFFIXES: .f .F .o .c .a .f90 .F90']

        conf.append('SIESTA_ARCH = {0}'.format('_'.join([spec.target.name, spec.platform, spec.os])))

        conf.append('CC = {0}'.format(env['CC']))
        conf.append('FPP = {0} -E -P -x -c'.format(env['FC']))
        if '+mpi' in spec:
            conf.append('FC = {0}'.format(env['MPIF90']))
        else:
            conf.append('FC = {0}'.format(env['FC']))

        conf.append('FFLAGS = {0}'.format(self.final_fflags_string))

        conf.append('FC_SERIAL = {0}'.format(env['FC']))

        conf += ['AR = ar', 'RANLIB = ranlib', 'SYS = nag']
        conf += ['SP_KIND = 4', 'DP_KIND = 8', 'KINDS = $(SP_KIND) $(DP_KIND)']

        conf.append('BLAS_LIBS = {0}'.format(self.spec['blas'].libs.ld_flags))
        conf.append('LAPACK_LIBS = {0}'.format(self.spec['lapack'].libs.ld_flags))
        if '+mpi' in spec:
            conf.append('SCALAPACK_LIBS = {0}'.format(self.spec['scalapack'].libs.ld_flags))

        conf.append('GRIDXC_ROOT = {0}'.format(self.spec['libgridxc'].prefix))
        conf.append('LIBXC_ROOT =  {0}'.format(self.spec['libxc'].prefix))

        if self.spec['libgridxc'].satisfies('@:0.8'):
            conf.append('include {0}/gridxc.mk'.format(self.spec['libgridxc'].prefix))
        else:           # FIXME: proper check for versions higher than 9.0
            conf.append('include {0}/share/org.siesta-project/gridxc_dp.mk'.format(
                self.spec['libgridxc'].prefix))

        conf.append('FPPFLAGS = $(DEFS_PREFIX)-DFC_HAVE_ABORT')
        conf.append('FPPFLAGS+= {0}'.format(self.final_fppflags_string))

        conf.append('INCFLAGS+= {0}'.format(self.final_incflags_string))
        conf.append('NETCDF_LIBS = {0} {1}'.format(
            self.spec['netcdf-fortran'].libs.ld_flags,
            self.spec['hdf5'].libs.ld_flags,
        ))

        conf.append('LIBS = $(NETCDF_LIBS) -lpthread $(SCALAPACK_LIBS) $(LAPACK_LIBS) $(BLAS_LIBS)')

        if '+mpi' in spec:
            conf.append('MPI_INTERFACE=libmpi_f90.a')
            conf.append('MPI_INCLUDE=.')

        conf += ['', 'FFLAGS_DEBUG = -g -O1', '',
                 'atom.o: atom.F',
                 '\t$(FC) -c $(FFLAGS_DEBUG) $(INCFLAGS) $(FPPFLAGS) $(FPPFLAGS_fixed_F) $<',
                 '',
                 '.c.o:',
                 '\t$(CC) -c $(CFLAGS) $(INCFLAGS) $(CPPFLAGS) $<',
                 '.F.o:',
                 '\t$(FC) -c $(FFLAGS) $(INCFLAGS) $(FPPFLAGS) $(FPPFLAGS_fixed_F)  $<',
                 '.F90.o:',
                 '\t$(FC) -c $(FFLAGS) $(INCFLAGS) $(FPPFLAGS) $(FPPFLAGS_free_F90) $<',
                 '.f.o:',
                 '\t$(FC) -c $(FFLAGS) $(INCFLAGS) $(FCFLAGS_fixed_f)  $<',
                 '.f90.o:',
                 '\t$(FC) -c $(FFLAGS) $(INCFLAGS) $(FCFLAGS_free_f90)  $<',]

        return conf


    def edit(self, spec, prefix):
        sh = which('sh')
        with working_dir('Obj'):
            sh('../Src/obj_setup.sh')
            with open('arch.make', 'w') as archmake:
                for line in self.archmake_lp_content:
                    archmake.write('{0}\n'.format(line))


    def build(self, spec, prefix):
        with working_dir('Obj'):
            make()

        if '+utils' in self.spec:
            with working_dir('Util'):
                sh = which('sh')
                sh('build_all.sh')


    def install(self, spec, prefix):
        mkdir(prefix.bin)
        with working_dir('Obj'):
            install('siesta', prefix.bin)

        if '+utils' in self.spec:
            for root, _, files in os.walk('Util'):
                for fname in files:
                    fname = join_path(root, fname)
                    if os.access(fname, os.X_OK):
                        install(fname, prefix.bin)
