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

    version('4.1-b4', sha256='19fa19a23adefb9741a436c6b5dbbdc0f57fb66876883f8f9f6695dfe7574fe3',
            url='https://launchpad.net/siesta/4.1/4.1-b4/+download/siesta-4.1-b4.tar.gz')

    version('master',  branch='master')
    version('psml',  branch='psml-support')

    variant('mpi', default=True, description='Build parallel version with MPI.')
    variant('utils', default=False, description='Build the utilities suit bundled with SIESTA (./Util dir).')
    # variant('psml', default=True,
    #         description='Build with support for pseudopotentials in PSML format.')

    # conflicts('-psml', when='@psml', msg='Experimental PSML branch needs `+psml`.')
    # conflicts('-mpi', when='@psml',  msg='Experimental PSML branch needs MPI (bug?).')
    # conflicts('-gridxc', when='+psml', msg='PSML requires LibGridXC.')

    depends_on('mpi', when='+mpi')

    depends_on('blas')
    depends_on('lapack')
    depends_on('scalapack', when='+mpi') # NOTE: cannot ld-link without scalapack when +mpi

    #NOTE: how do I resolve these strictly together?
    # depends_on('netcdf-fortran ^netcdf-c+dap ^hdf5+fortran+hl')
    depends_on('hdf5 +fortran +hl')
    depends_on('netcdf-c +dap')
    depends_on('netcdf-fortran')

    depends_on('libxc@3.0.0') # NOTE: hard-wired libxc version, Siesta does not link against newer ones yet
    depends_on('libgridxc +libxc ~mpi', when='~mpi')
    depends_on('libgridxc +libxc +mpi', when='+mpi')

    depends_on('xmlf90',  when='@master,psml')
    depends_on('libpsml', when='@master,psml')

    phases = ['edit', 'build', 'install']

    @property
    def siesta_arch_string(self):
        return '_'.join([
            self.spec.target.name, self.spec.platform, self.spec.os
        ])


    @property
    def final_fflags_string(self):
        return ' '.join(self.spec.compiler_flags['fflags'] + [
            self.compiler.fc_pic_flag,
        ])


    @property
    def final_fppflags_string(self):
        fppflags = ['-DGRID_DP', '-DCDF', '-DNCDF', '-DNCDF_4']
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

        conf.append('SIESTA_ARCH = {0}'.format(self.siesta_arch_string))

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

        conf.append('BLAS_LIBS = {0}'.format(spec['blas'].libs.ld_flags))
        conf.append('LAPACK_LIBS = {0}'.format(spec['lapack'].libs.ld_flags))
        if '+mpi' in spec:
            conf.append('SCALAPACK_LIBS = {0}'.format(spec['scalapack'].libs.ld_flags))

        conf.append('COMP_LIBS = libncdf.a libfdict.a')

        conf.append('GRIDXC_ROOT = {0}'.format(spec['libgridxc'].prefix))
        conf.append('LIBXC_ROOT =  {0}'.format(spec['libxc'].prefix))

        if self.spec['libgridxc'].satisfies('@:0.8'):
            conf.append('include {0}/gridxc.mk'.format(spec['libgridxc'].prefix))
        else:           # FIXME: proper check for versions higher than 9.0
            conf.append('include {0}/share/org.siesta-project/gridxc_dp.mk'.format(
                spec['libgridxc'].prefix))

        conf.append('FPPFLAGS = $(DEFS_PREFIX)-DFC_HAVE_ABORT')
        conf.append('FPPFLAGS+= {0}'.format(self.final_fppflags_string))

        conf.append('INCFLAGS+= {0}'.format(self.final_incflags_string))

        conf.append('NETCDF_LIBS = {0}'.format(' '.join([
            spec['netcdf-fortran'].libs.ld_flags,
            spec['hdf5'].libs.ld_flags,
            '-lhdf5_fortran',
            spec['zlib'].libs.ld_flags,
        ])))

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


    def filter_archmake(self, archmake):
        spec = self.spec
        archmake.filter('^SIESTA_ARCH=Master-template',
                        'SIESTA_ARCH={0}'.format(self.siesta_arch_string))

        archmake.filter('^WITH_PSML=.*',   'WITH_PSML=1')
        archmake.filter('^WITH_GRIDXC=.*', 'WITH_GRIDXC=1')

        if '+mpi' not in spec:
            archmake.filter('^WITH_MPI=1', 'WITH_MPI=')

        archmake.filter('^WITH_NETCDF=.*', 'WITH_NETCDF=1')
        archmake.filter('^WITH_SEPARATE_NETCDF_FORTRAN=.*', 'WITH_SEPARATE_NETCDF_FORTRAN=1')
        archmake.filter('^WITH_NCDF=.*', 'WITH_NCDF=1')

        #NOTE: For now Spack recipy uses legacy installation schema for gridxc
        archmake.filter('^WITH_LEGACY_GRIDXC_INSTALL=.*', 'WITH_LEGACY_GRIDXC_INSTALL=1')

        archmake.filter('^#XMLF90_ROOT=', 'XMLF90_ROOT={0}'.format(spec['xmlf90'].prefix))
        archmake.filter('^#PSML_ROOT=', 'PSML_ROOT={0}'.format(spec['libpsml'].prefix))
        archmake.filter('^#GRIDXC_ROOT=',
                        'GRIDXC_ROOT={0}\nLIBXC_ROOT={1}'.format(
                        spec['libgridxc'].prefix, spec['libxc'].prefix
                        ))      #NOTE: older gridxc installation requires LIBXC_ROOT specified

        archmake.filter('^#NETCDF_ROOT=.*',
                        'NETCDF_ROOT={0}'.format(spec['netcdf-c'].prefix))
        archmake.filter('^#NETCDF_FORTRAN_ROOT=.*',
                        'NETCDF_FORTRAN_ROOT={0}'.format(spec['netcdf-fortran'].prefix))
        archmake.filter('^#HDF5_LIBS=.*',
                        'HDF5_LIBS={0}'.format(' '.join([
                            spec['hdf5'].libs.ld_flags,
                            '-lhdf5_hl',
                            '-lhdf5_fortran',
                            spec['curl'].libs.ld_flags,
                            spec['zlib'].libs.ld_flags,
                        ])))

        if '+mpi' in spec:
            archmake.filter('^#SCALAPACK_LIBS=.*',
                            'SCALAPACK_LIBS={0}'.format(spec['scalapack'].libs.ld_flags))

        archmake.filter('^#LAPACK_LIBS=.*',
                        'LAPACK_LIBS={0}'.format(spec['lapack'].libs.ld_flags))

        if '+mpi' in spec:
            archmake.filter('^#FC_PARALLEL=.*', 'FC_PARALLEL={0}'.format(env['MPIF90']))

        archmake.filter('^#FC_SERIAL=.*', 'FC_SERIAL={0}'.format(env['FC']))
        archmake.filter('^#FPP =.*', 'FPP = {0} -E -P -x -c'.format(env['FC']))
        archmake.filter('^#FFLAGS =.*', 'FFLAGS= {0}'.format(self.final_fflags_string))
        archmake.filter('^#FFLAGS_DEBUG=.*', 'FFLAGS_DEBUG= -g -O0')


    def edit(self, spec, prefix):
        sh = which('sh')
        with working_dir('Obj'):
            sh('../Src/obj_setup.sh')
            # Mostly for reference than for practical reasons the launchpad public
            # version is kept. In this case the `arch.make` contents is generated
            # as whole and written to the file:
            if self.spec.satisfies('@4.1-b4'):
                with open('arch.make', 'w') as archmake:
                    for line in self.archmake_lp_content:
                        archmake.write('{0}\n'.format(line))
            # In case of a modern version, e.g. obtained from Git, the `master-raw`
            # makefile sample is copied and regex-filtered instead:
            elif (self.spec.satisfies('@master') or self.spec.satisfies('@psml')):
                copy('./ARCH-EXPERIMENTAL/master-raw.make', './arch.make')
                self.filter_archmake(FileFilter('./arch.make'))


    def build(self, spec, prefix):
        with working_dir('Obj'):
            make()              # build Siesta

        # These utils fail to build yet, mostly due to Makefile-s (mis)formatting:
        #FIXME: skipping builds of utilities by default
        skipped_batch_utils = [
            'Util/MPI_test',      # needs patch
            'Util/MPI_test/MPI',  # needs patch
            'Util/TS/TBtrans',    # needs patch
            'Util/TS/tshs2tshs',  # needs patch
            'Util/STM/ol-stm/Src', # needs FFTW3
            'Util/STM/ol-stm', # needs FFTW3
        ]

        if '+utils' in self.spec: # build Utils, all but skipped
            for dname in [f[0] for f in os.walk("Util")]:
                if dname not in skipped_batch_utils:
                    with working_dir(dname):
                        if (os.access('Makefile', os.F_OK)):
                            make(parallel=False)


    def install(self, spec, prefix):
        mkdir(prefix.bin)
        with working_dir('Obj'):
            install('siesta', prefix.bin)

        if '+utils' in self.spec: # install all Util executables produced at `build` stage
            for root, _, files in os.walk('Util'):
                for fname in files:
                    fname = join_path(root, fname)
                    if os.access(fname, os.X_OK):
                        install(fname, prefix.bin)
