#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import sys
import platform
import anamdesktop


def get_oraclfolder():
    if platform.system() == 'Darwin':
        return 'macos'
    else:
        if platform.machine().endswith('64'):
            return 'win64'
        else:
            return 'win32'


ORACLE_HOME = os.path.join(os.getcwd(),
                           'oraclient_{}'.format(get_oraclfolder()))

environ = {}
environ['LD_LIBRARY_PATH'] = ORACLE_HOME
environ['ORACLE_HOME'] = ""
environ['NLS_LANG'] = ".AL32UTF8"

if platform.system() == 'Darwin':
    environ['DYLD_LIBRARY_PATH'] = ORACLE_HOME
    try:
        os.execve(sys.executable, [sys.executable, 'anamdesk.py'], environ)
    except Exception as exc:
        print("Failed re-exec: {}".format(exc))
        sys.exit(1)
else:
    environ['PATH'] = "{};{}".format(os.environ['PATH'], ORACLE_HOME)
    os.environ.update(environ)
    from anamdesktop.entry import main
    main()
