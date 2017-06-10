#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import cx_Oracle

from anamdesktop import SETTINGS
from anamdesktop.network import test_socket

ORACLE_PORT = 1521


def ora_disconnect(conn):
    ''' close `conn` connection to Oracle DB '''
    conn.close()


def ora_connect(address=None, username=None, password=None, service=None):
    ''' prepare and return a working Oracle connection based on params '''

    return cx_Oracle.connect(
        '{username}/{password}@{address}/{service}'
        .format(username=username or SETTINGS.get('db_username'),
                password=password or SETTINGS.get('db_password'),
                address=address or SETTINGS.get('db_serverip'),
                service=service or SETTINGS.get('db_sid')))


def ora_test(address=None, username=None, password=None, service=None):
    ''' tests oracle credentials by connecting to it '''

    def test_conn():
        conn = ora_connect(address=address, username=username,
                           password=password, service=service)
        conn.close()
        return True

    # check that server is reachable and open
    if not test_socket(address, ORACLE_PORT):
        return False

    # check that we can actually connect to it
    try:
        return test_conn()
    except:
        return False
