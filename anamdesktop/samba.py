#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import uuid

from path import Path as p
from smb.SMBConnection import SMBConnection
from smb.smb_structs import OperationFailure

from anamdesktop import logger, SETTINGS
from anamdesktop.network import test_socket

SAMBA_PORT = 445


class FailedToCreateTree(Exception):
    pass


def smb_connect(address=None, username=None, password=None):
    ''' prepare and return a valid SMB Connection object

        Uses global settings for unspecified parameters '''

    conn = SMBConnection(username=username or SETTINGS.get('picserv_username'),
                         password=password or SETTINGS.get('picserv_password'),
                         my_name="ANAM-DESKTOP",
                         remote_name="")
    assert conn.connect(address or SETTINGS.get('picserv_ip'), 139)
    return conn


def create_folder(path, service_name=None, conn=None):
    ''' create a folder at `path` on the SMB share `service_name` '''

    conn = conn or smb_connect()
    conn.createDirectory(
        service_name=service_name or SETTINGS.get('picserv_share'), path=path)


def delete_folder(path, service_name=None, conn=None):
    ''' delete a folder at `path` on the SMB share `service_name` '''

    conn = conn or smb_connect()
    conn.deleteDirectory(
        service_name=service_name or SETTINGS.get('picserv_share'), path=path)


def delete_file(path, service_name=None, conn=None):
    ''' delete a file at `path` on the SMB share `service_name` '''

    conn = conn or smb_connect()
    conn.deleteFiles(
        service_name=service_name or SETTINGS.get('picserv_share'),
        path_file_pattern=path)


def copy_files(files, service_name=None, conn=None):
    ''' copy a list of files to `service_name`

        files is a list of (source_path, destitionation_path) tuples

        returns (success, [list, of, failures]) '''

    conn = conn or smb_connect()
    service_name = service_name or SETTINGS.get('picserv_share')

    def _create_folder(service_name, path):
        try:
            sharedFile = conn.getAttributes(service_name=service_name,
                                            path=path)
            assert sharedFile.isDirectory
        except OperationFailure:
            # does not exist, create folder
            create_folder(path, service_name, conn)
        except AssertionError:
            # is not a directory. remove and recreate
            delete_file(path, service_name, conn)
            create_folder(path, service_name, conn)
        else:
            # path already exist and is directory. moving on.
            return

    def _create_folder_tree(service_name, dest_filename):
        # create recursing folders on destination
        walked_folders = []
        for folder in p(dest_filename).splitall()[:-1]:
            if not folder:
                continue

            walked_folders.append(folder)
            path = os.path.join(*walked_folders)

            _create_folder(service_name, path)

    failures = []

    for local_filename, dest_filename in files:
        logger.debug("Copying `{}` to `{}`"
                     .format(local_filename, dest_filename))

        # create all folders up to dest_filename on samba share
        try:
            _create_folder_tree(service_name, dest_filename)
        except Exception as exp:
            logger.debug("Unable to create folder tree for `{}`"
                         .format(dest_filename))
            logger.exception(exp)
            failures.append((local_filename, dest_filename))
            continue

        try:
            # write file on destination (overwrites if exists)
            with open(local_filename, 'rb') as local_file:
                assert conn.storeFile(
                    service_name, dest_filename, local_file) > 0
        except Exception as exp:
            logger.error("Unable to write {s} onto {d} on SMB {sh}"
                         .format(s=local_filename, d=dest_filename,
                                 sh=service_name))
            logger.exception(exp)
            failures.append((local_filename, dest_filename))

    return not failures, failures


def test_connection(address=None, username=None, password=None,
                    service_name=None):
    ''' test whether an SMB share is writable '''

    address = address or SETTINGS.get('picserv_ip')
    username = username or SETTINGS.get('picserv_username')
    password = password or SETTINGS.get('picserv_password')
    service_name = service_name or SETTINGS.get('picserv_share')

    # test whether server is reachable and has a samba service
    if not test_socket(address, SAMBA_PORT):
        return False

    try:
        conn = smb_connect(address=address,
                           username=username, password=password)
    except:
        return False

    # generate random UUID as folder name
    fname = uuid.uuid4().urn[9:]
    try:
        create_folder(path=fname, service_name=service_name, conn=conn)
        delete_folder(path=fname, service_name=service_name, conn=conn)
        return True
    except:
        return False
