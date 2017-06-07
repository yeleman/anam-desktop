#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import cx_Oracle

from anamdesktop import SETTINGS

ORACLE_PORT = 1521


def ora_disconnect(conn):
    ''' close `conn` connection to Oracle DB '''
    conn.close()


def ora_connect(address, username, password, service):
    ''' prepare and return a working Oracle connection based on params '''
    return cx_Oracle.connect('{username}/{password}@{address}/{service}'
                             .format(username=username,
                                     password=password,
                                     address=address,
                                     service=service))


def ora_autoconnect():
    ''' return a working Oracle connection based on global settings '''
    return ora_connect(address=SETTINGS.get('db_serverip'),
                       username=SETTINGS.get('db_username'),
                       password=SETTINGS.get('db_password'),
                       service=SETTINGS.get('db_sid'))
