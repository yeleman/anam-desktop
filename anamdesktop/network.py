#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import socket
import urllib

import requests

from anamdesktop import SETTINGS, logger


def get_auth_headers(token=SETTINGS.get('store_token')):
    ''' `authorization header (dict) for `requests` using `token` '''
    return {'Authorization': "Token {}".format(token)}


def do_get(path,
           or_none=False,
           server_url=SETTINGS.get('store_url', ''),
           server_token=SETTINGS.get('store_token')):
    ''' performs GET request on API.

        see. `do_request()` '''
    return do_request(path, 'GET',
                      or_none=or_none,
                      server_url=server_url, server_token=server_token)


def do_post(path, payload=None,
            or_none=False,
            server_url=SETTINGS.get('store_url', ''),
            server_token=SETTINGS.get('store_token')):
    ''' performs POST request with `payload` on API.

        see. `do_request()` '''
    return do_request(path, 'POST', {'json': payload},
                      or_none=or_none,
                      server_url=server_url, server_token=server_token)


def do_request(path, method, kwargs={},
               or_none=False,
               server_url=SETTINGS.get('store_url', ''),
               server_token=SETTINGS.get('store_token')):
    ''' performs a GET or POST on `path`

        URL is computed from `server_url`, /api and `path`
        Authorization header sent with `server_token`

        Excepts `anam-receiver` formatted JSON response.
        Raises on non-success status response.

        returns response as JSON '''
    url = ''.join((server_url, '/api', path))

    if not test_url_socket(url):
        logger.info("{} requests to {} failed. No socket.".format(method, url))
        if or_none:
            return None
        else:
            raise IOError("Unable to connect to {}. Network Error".format(url))

    req = None
    try:
        req = getattr(requests, method.lower())(
            url, headers=get_auth_headers(server_token), timeout=3, **kwargs)
        assert req.status_code in (200, 201)
        resp = req.json()
        assert resp['status'] == 'success'
        return resp
    except Exception as exp:
        if req:
            logger.error(req.status_code, req.text)
        logger.exception(exp)

        # silented error
        if or_none:
            return None
        raise


def test_socket(address, port):
    ''' tests whether a service is listening at `address`:`port`

        timeouts after 2 seconds '''

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((address, port))
    return result == 0


def test_url_socket(url):
    try:
        u = urllib.parse.urlparse(url)
    except Exception as exp:
        logger.error("Unable to parse URL `{}`".format(url))
        logger.exception(exp)
        return False

    # check if address and port are reachable
    return test_socket(u.hostname, u.port)


def test_webservice(url, token):
    if not test_url_socket(url):
        return False

    # check that the service is responding
    return do_get(
        '/check', server_url=url, server_token=token, or_none=True) is not None
