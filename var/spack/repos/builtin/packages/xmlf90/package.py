# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack import *


class Xmlf90(AutotoolsPackage):
    """xmlf90 is a suite of libraries to handle XML in Fortran."""

    homepage = "https://launchpad.net/xmlf90"
    url      = "https://launchpad.net/xmlf90/trunk/1.5/+download/xmlf90-1.5.4.tar.gz"
    git      = "https://gitlab.com/siesta-project/libraries/xmlf90.git"

    maintainers = ['vdikan']

    # version('master',  branch='master')

    version('1.5.4', sha256='a0b1324ff224d5b5ad1127a6ad4f90979f6b127f1a517f98253eea377237bbe4')
    version('1.5.3', sha256='a5378a5d9df4b617f51382092999eb0f20fa1a90ab49afbccfd80aa51650d27c')
    version('1.5.2', sha256='666694db793828d1d1e9aea665f75c75ee21772693465a88b43e6370862abfa6',
            url="https://launchpad.net/xmlf90/trunk/1.5/+download/xmlf90-1.5.2.tgz")

    depends_on('autoconf', type='build', when='@1.5.2')
    depends_on('automake', type='build', when='@1.5.2')
    depends_on('libtool',  type='build', when='@1.5.2')
    depends_on('m4',       type='build', when='@1.5.2')

    sanity_check_is_dir  = ['lib', 'share', 'include']
    sanity_check_is_file = [join_path('share', 'org.siesta-project',
                                      'xmlf90.mk')]

    @when('@1.5.2')
    def autoreconf(self, spec, prefix):
        autoreconf('--install', '--verbose', '--force')

    def configure_args(self):
        if self.spec.satisfies('%gcc'):
            return ['FCFLAGS=-ffree-line-length-none']
        return []

    # @run_after('install')
    # def fix_mk(self):
    #     install(join_path(self.prefix, 'share', 'org.siesta-project',
    #                       'xmlf90.mk'), prefix)
