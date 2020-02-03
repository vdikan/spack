# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack import *


class Libpsml(AutotoolsPackage):
    """A library to handle pseudopotentials in PSML
    (Pseudopotential Markup Language File) format."""

    homepage = "https://siesta-project.github.io/psml-docs"
    url      = "https://gitlab.com/siesta-project/libraries/libpsml/-/archive/libpsml-1.1.8/libpsml-libpsml-1.1.8.tar.gz"
    git      = "https://gitlab.com/siesta-project/libraries/libpsml.git"

    maintainers = ['vdikan']

    version('1.1.8', sha256='77498783be1bc7006819f36c42477b5913464b8c660203f7d6b7f7e25aa29145')

    depends_on('autoconf', type='build')
    depends_on('automake', type='build')
    depends_on('libtool',  type='build')
    depends_on('m4',       type='build')

    depends_on('xmlf90')

    def autoreconf(self, spec, prefix):
        autoreconf('--install', '--verbose', '--force')

    def configure_args(self):
        args = ["--with-xmlf90=%s" % self.spec['xmlf90'].prefix]
        return args

    @run_after('install')
    def fix_mk(self):
        mkfile = FileFilter(join_path(self.prefix,
                                      'share', 'org.siesta-project', 'psml.mk'))
        mkfile.filter('^PSML_XMLF90_ROOT\s= .*',
                      'PSML_XMLF90_ROOT = {0}'.format(self.spec['xmlf90'].prefix))
