# -*- coding: utf-8 -*-
# Copyright (C) 2017-2018, Luis Pedro Coelho <luis@luispedro.org> and Renato Alves <ralves@embl.de>
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

from __future__ import division
from glob import glob
try:
    import setuptools
except:
    print('''
setuptools not found.

On linux, the package is often called python-setuptools''')
    from sys import exit
    exit(1)

exec(compile(open('ngless/nglesspy_version.py').read(),
             'ngless/nglesspy_version.py', 'exec'))

try:
    long_description = open('README.md', encoding='utf-8').read()
except:
    long_description = open('README.md').read()



packages = setuptools.find_packages()
install_requires = open('requirements.txt').read()
tests_require = open('tests-requirements.txt').read()


classifiers = [
'Development Status :: 4 - Beta',
'Intended Audience :: Developers',
'Intended Audience :: Science/Research',
'Topic :: Software Development :: Libraries',
'Topic :: Scientific/Engineering :: Bio-Informatics',
'Topic :: Software Development :: Libraries :: Python Modules',
'Programming Language :: Python',
'Programming Language :: Python :: 3',
'Programming Language :: Python :: 3.4',
'Programming Language :: Python :: 3.5',
'Programming Language :: Python :: 3.6',
'Operating System :: OS Independent',
]

setuptools.setup(name = 'NGLessPy',
      version = __version__,
      description = 'NGLessPy: Python interface to NGLess',
      long_description = long_description,
      long_description_content_type='text/markdown',
      author = 'Luis Pedro Coelho',
      author_email = 'luis@luispedro.org',
      license = 'MIT',
      platforms = ['Any'],
      classifiers = classifiers,
      url = 'http://ngless.embl.de/',
      packages = packages,
      entry_points={
          'console_scripts' : [
              'ngless-count.py = ngless.bin.ngless_count:main',
              'ngless-map.py = ngless.bin.ngless_map:main',
              'ngless-mapstats.py = ngless.bin.ngless_mapstats:main',
              'ngless-select.py = ngless.bin.ngless_select:main',
              'ngless-trim.py = ngless.bin.ngless_trim:main',
              'ngless-unique.py = ngless.bin.ngless_unique:main',
              'ngless-install.py = ngless.bin.ngless_install:main',
          ],
      },
      test_suite = 'nose.collector',
      install_requires = install_requires,
      tests_require = tests_require,
      data_files=[("share/commonwl", glob("cwl/*"))],
      )

