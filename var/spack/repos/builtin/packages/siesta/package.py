# Copyright 2020 The SIESTA group
# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack import *
import os
import stat


class Siesta(MakefilePackage):
    """SIESTA performs electronic structure calculations and ab initio molecular
       dynamics simulations of molecules and solids."""

    homepage = "https://departments.icmab.es/leem/siesta/"
    git      = "https://gitlab.com/siesta-project/siesta.git"

    maintainers = ['vdikan']

    version('4.1-b4', sha256='19fa19a23adefb9741a436c6b5dbbdc0f57fb66876883f8f9f6695dfe7574fe3',
            url='https://launchpad.net/siesta/4.1/4.1-b4/+download/siesta-4.1-b4.tar.gz')
    version('elsi', sha256='4c7b2edae2a7c9ca89b53731d87e925863b117ae460296dbd1198f75d8d47a8d',
            url='https://gitlab.com/garalb/siesta/-/archive/trunk-elsi-dm/siesta-trunk-elsi-dm.tar.gz')

    version('master',  branch='master')
    version('psml',  branch='psml-support')

    variant('mpi', default=True, description='Build parallel version with MPI.')
    variant('flook', default=True, description='Build SIESTA with flook support to interface with Lua.')
    variant('utils', default=True, description='Build the utilities suit bundled with SIESTA (./Util dir).')
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
    depends_on('fftw@3:')
    depends_on('elsi@2.7:+enable_pexsi')

    depends_on('libxc@3.0.0') # NOTE: hard-wired libxc version, Siesta does not link against newer ones yet
    depends_on('libgridxc +libxc ~mpi', when='~mpi')
    depends_on('libgridxc +libxc +mpi', when='+mpi')

    depends_on('flook', when='+flook')

    depends_on('xmlf90',  when='@master,psml,elsi')
    depends_on('libpsml', when='@master,psml,elsi')

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
        if '+flook' in self.spec:
            fppflags.append('-DSIESTA__FLOOK')

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

        if "+flook" in spec:
            conf.append('FLOOK_LIBS=-L/{0}/lib -lflookall -ldl'.format(spec['flook'].prefix))

        conf.append('FPPFLAGS = $(DEFS_PREFIX)-DFC_HAVE_ABORT')
        conf.append('FPPFLAGS+= {0}'.format(self.final_fppflags_string))

        conf.append('INCFLAGS+= {0}'.format(self.final_incflags_string))

        conf.append('NETCDF_LIBS = {0}'.format(' '.join([
            spec['netcdf-fortran'].libs.ld_flags,
            spec['hdf5'].libs.ld_flags,
            '-lhdf5_fortran',
            spec['zlib'].libs.ld_flags,
        ])))

        conf.append('LIBS = $(NETCDF_LIBS) -lpthread $(SCALAPACK_LIBS) $(LAPACK_LIBS) $(BLAS_LIBS) $(FLOOK_LIBS)')

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

        if self.spec.satisfies('@elsi'):
            archmake.filter('^WITH_ELSI=.*', 'WITH_ELSI=1')

        if '+flook' in spec:
            archmake.filter('^WITH_FLOOK=.*', 'WITH_FLOOK=1')

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

        # Linking ELSI with PEXSI
        #FIXME: doesnt work. PEXSI invocations expect -DSIESTA__PEXSI flag,
        # and that doesn't compile due to missing `f_interface.f90`.
        archmake.filter('^#ELSI_ROOT=', 'ELSI_ROOT={0}'.format(spec['elsi'].prefix))
        archmake.filter('^#LIBS_CPLUS=', 'LIBS_CPLUS=')
        # archmake.filter('-DSIESTA__ELSI ', '-DSIESTA__ELSI -DSIESTA__PEXSI ')

        if "+flook" in spec:
            archmake.filter('^#FLOOK_ROOT=', 'FLOOK_ROOT={0}'.format(spec['flook'].prefix))

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
        archmake.filter('^#FFTW_ROOT=.*', 'FFTW_ROOT={0}'.format(spec['fftw'].prefix))

        if '+mpi' in spec:
            archmake.filter('^#FC_PARALLEL=.*', 'FC_PARALLEL={0}'.format(env['MPIF90']))

        archmake.filter('^#FC_SERIAL=.*', 'FC_SERIAL={0}'.format(env['FC']))
        archmake.filter('^#FPP =.*', 'FPP = {0} -E -P -x -c'.format(env['FC']))
        archmake.filter('^#FFLAGS =.*', 'FFLAGS= {0}'.format(self.final_fflags_string))
        archmake.filter('^#FFLAGS_DEBUG=.*', 'FFLAGS_DEBUG= -g -O0')

        archmake.filter('^#RANLIB=.*', 'RANLIB={0}'.format('ranlib' if which('ranlib') else 'echo'))


    def edit(self, spec, prefix):
        sh = which('bash')

        with open('SIESTA.release', 'w') as siesta_release:
            # Outputs version marker to bypass `SIESTA_vgen.sh` check
            siesta_release.write('spack_{0}_{1}'.format(self.version[0], self.siesta_arch_string))

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
            elif (self.spec.satisfies('@master') or
                  self.spec.satisfies('@psml') or
                  self.spec.satisfies('@elsi')):
                copy('./ARCH-EXPERIMENTAL/master-raw.make', './arch.make')
                self.filter_archmake(FileFilter('./arch.make'))


    def build(self, spec, prefix):
        sh = which('sh')  # erase

        with working_dir('Obj'):
            make()              # build Siesta

        # Libs missing/not buildable yet:
        # libfdict for TBtrans
        # FFTW3 for STM
        if '+utils' in self.spec: # build Utils
            # The following is a workaround to suppress inner `make`-invocations stderr
            # that outputs garbage into tty that Spack cannot parse.
            with working_dir("Util"):
                with open('build_spack.sh', 'w') as build_proxy:
                    build_proxy.write('#!/bin/bash\n./build_all.sh >/dev/null 2>/dev/null\n')
                st = os.stat('build_spack.sh')
                os.chmod('build_spack.sh', st.st_mode | stat.S_IEXEC)
                sh("./build_spack.sh")


    def install(self, spec, prefix):
        mkdir(prefix.bin)
        with working_dir('Obj'):
            install('siesta', prefix.bin)

        if '+utils' in self.spec: # install all Util executables produced at `build` stage
            for root, _, files in os.walk('Util'):
                for fname in files:
                    fname = join_path(root, fname)
                    if (os.access(fname, os.X_OK) and
                        (not fname.lower().endswith(('.sh')))):
                        install(fname, prefix.bin)
