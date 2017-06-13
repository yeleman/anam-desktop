#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import json
import locale
import logging
import platform
import logging.config

UI_SIZE = (900, 600)
LOG_FILE = 'anam-desktop.log'
HELP_FILE = "Aide ANAM Desktop.pdf"
IS_MAC = platform.system() == 'Darwin'
SETTINGS_FILE = "anam-desktop.settings"

VERSION = (1, 1)
DEVELOPER = "yɛlɛman"
APP_NAME = "ANAM Desktop"

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': LOG_FILE,
        },
    },
    'loggers': {
        'iso8601': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False,
        },
        '': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'anamdesktop': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
})
logger = logging.getLogger('anamdesktop')


def setlocale():
    locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8" if IS_MAC else "fra_FRA")


def read_settings(filename):
    # defaults
    settings = {
        'picserv_ip': "192.168.1.10",
        'picserv_username': None,
        'picserv_password': None,
        'picserv_share': None,

        'db_serverip': "192.168.1.11",
        'db_username': None,
        'db_password': None,
        'db_sid': None,

        'store_url': "http://192.168.1.10:8080",
        'store_token': None,
    }
    try:
        with open(filename, 'r') as f:
            file_data = json.load(f)
    except:
        pass
    else:
        settings.update(file_data)

    return settings


def save_settings(filename, settings):
    logger.info("Saving settings to file `{}`".format(filename))
    try:
        with open(filename, 'w') as f:
            return json.dump(settings, f, indent=4)
    except Exception as exp:
        logger.error("Unable to save settings to file `{}`".format(filename))
        logger.exception(exp)
        return False

SETTINGS = read_settings(SETTINGS_FILE)
