#!/usr/bin/python
# -*- coding: utf-8 -*-


__license__   = 'GPL v3'
__copyright__ = '2014, Jim Miller'
__docformat__ = 'restructuredtext en'

import os
from glob import glob

from makezip import createZipFile

if __name__=="__main__":
    
    filename="SmartEject.zip"
    exclude=['*.pyc','*~','*.xcf','makezip.py','makeplugin.py','*.po','*.pot','*.notes','*default.mo']
    # from top dir. 'w' for overwrite
    #from calibre-plugin dir. 'a' for append
    files=['translations',]
    files.extend(glob('*.py'))
    files.extend(glob('plugin-import-name-*.txt'))
    createZipFile(filename,"w",
                  files,exclude=exclude)
    
