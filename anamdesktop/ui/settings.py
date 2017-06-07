#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from PyQt5 import QtWidgets, QtCore

from anamdesktop.samba import test_connection
from anamdesktop.oracle import ora_connect, ORACLE_PORT
from anamdesktop.network import test_socket, test_webservice
from anamdesktop import SETTINGS, logger, save_settings, SETTINGS_FILE


class FormLayout(QtWidgets.QFormLayout):
    ''' fields expanding, left-aligned label QFormLayout '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.setLabelAlignment(QtCore.Qt.AlignLeft)


class SettingLineEdit(QtWidgets.QLineEdit):
    ''' a QLineEdit automaticaly filled by it's setting value (from key) '''
    def __init__(self, settings_key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        value = SETTINGS.get(settings_key)
        if value:
            self.setText(value)


class SettingsGroupChecker(object):
    ''' a list of SettingLineEdit fields which are validated all-together

        creates a check button and label displaying status of check()
        change to any of them triggers a tampered state '''

    def __init__(self, dialog, fields):
        self.dialog = dialog
        self.fields = fields
        self.initUI()
        self.check()

    @property
    def name(self):
        return self.__class__.__name__

    def getfield(self, key):
        return getattr(self.dialog, key)

    def initUI(self):
        for field in self.fields:
            self.getfield(field).textChanged.connect(self.changed)

        self.check_label = QtWidgets.QLabel("")
        self.check_button = QtWidgets.QPushButton("vérifier")
        self.check_button.setDefault(False)
        self.check_button.setAutoDefault(False)
        self.check_button.clicked.connect(self.check)

    def for_row(self):
        ''' ordered tuple to be passed to QGridLayout.addRow() '''
        return (self.check_button, self.check_label)

    def change_label(self, text, color):
        self.check_label.setText(text)
        self.check_label.setStyleSheet('QLabel {color: ' + color + ';}')

    def changed(self, *args, **kwargs):
        self.change_label("paramètres non vérifiés", 'orange')

    def check(self):
        self.check_button.setDisabled(True)
        self.change_label("vérification en cours…", 'yellow')

        if self.do_check():
            logger.info("Settings OK for {}".format(self.name))
            self.change_label("paramètres OK", 'green')

        else:
            logger.info("Settings incorrect for {}".format(self.name))
            self.change_label("paramètres incorrects", 'red')
        self.check_button.setDisabled(False)

    def do_check(self):
        ''' overwrite this with your check. must return bool-like '''
        pass


class SambaChecker(SettingsGroupChecker):
    ''' tests whether samba share is writable '''

    def do_check(self):
        try:
            assert test_connection(
                address=self.getfield('picserv_ip').text(),
                username=self.getfield('picserv_username').text(),
                password=self.getfield('picserv_password').text(),
                service_name=self.getfield('picserv_share').text())
        except Exception as e:
            logger.debug("Unable to connect to samba share.")
            logger.debug(e)
            return False
        else:
            return True


class OracleChecker(SettingsGroupChecker):
    ''' tests whether the oracle DB is available for connection '''

    def do_check(self):
        def test_conn():
            conn = ora_connect(
                address=self.getfield('db_serverip').text(),
                username=self.getfield('db_username').text(),
                password=self.getfield('db_password').text(),
                service=self.getfield('db_sid').text())
            conn.close()
            return True
        if not test_socket(address=self.getfield('db_serverip').text(),
                           port=ORACLE_PORT):
            return False
        try:
            return test_conn()
        except Exception as e:
            logger.debug("Unable to connect to oracle database.")
            logger.debug(e)
            return False


class WebAPIChecker(SettingsGroupChecker):
    ''' tests whether the anam-receiver webservice responds to api/check '''

    def do_check(self):
        return test_webservice(url=self.getfield('store_url').text(),
                               token=self.getfield('store_token').text())


class SettingsDialog(QtWidgets.QDialog):

    DIALOG_SIZE = (700, 200)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Modifications des paramètres")
        self.setModal(True)
        self.resize(*SettingsDialog.DIALOG_SIZE)
        self.layout = QtWidgets.QGridLayout()

        # Photo mount point
        self.picserv = QtWidgets.QGroupBox("Dossier partagé des photos")
        self.picserv_layout = FormLayout(self.picserv)
        self.picserv_ip = SettingLineEdit('picserv_ip')
        self.picserv_username = SettingLineEdit('picserv_username')
        self.picserv_password = SettingLineEdit('picserv_password')
        self.picserv_share = SettingLineEdit('picserv_share')
        self.picserv_layout.addRow("Adresse IP", self.picserv_ip)
        self.picserv_layout.addRow("Identifiant", self.picserv_username)
        self.picserv_layout.addRow("Mot de passe", self.picserv_password)
        self.picserv_layout.addRow("Nom du partage", self.picserv_share)

        self.samba_checker = SambaChecker(
            dialog=self, fields=['picserv_ip', 'picserv_username',
                                 'picserv_password', 'picserv_share'])
        self.picserv_layout.addRow(*self.samba_checker.for_row())
        self.picserv.setLayout(self.picserv_layout)

        # Oracle Database
        self.oracle = QtWidgets.QGroupBox("Base de données Oracle")
        self.oracle_layout = FormLayout(self.oracle)
        self.db_serverip = SettingLineEdit('db_serverip')
        self.db_username = SettingLineEdit('db_username')
        self.db_password = SettingLineEdit('db_password')
        self.db_sid = SettingLineEdit('db_sid')
        self.oracle_layout.addRow("Adresse IP", self.db_serverip)
        self.oracle_layout.addRow("Identifiant", self.db_username)
        self.oracle_layout.addRow("Mot de passe", self.db_password)
        self.oracle_layout.addRow("SID", self.db_sid)

        self.oracle_checker = OracleChecker(
            dialog=self, fields=['db_serverip', 'db_username',
                                 'db_password', 'db_sid'])
        self.oracle_layout.addRow(*self.oracle_checker.for_row())
        self.oracle.setLayout(self.oracle_layout)

        # anam-receiver
        self.store = QtWidgets.QGroupBox("Server RAMED/ANAM (anam-receiver)")
        self.store_layout = FormLayout(self.store)
        self.store_url = SettingLineEdit('store_url')
        self.store_token = SettingLineEdit('store_token')
        self.store_layout.addRow("URL", self.store_url)
        self.store_layout.addRow("Token", self.store_token)

        self.oracle_checker = WebAPIChecker(
            dialog=self, fields=['store_url', 'store_token'])
        self.store_layout.addRow(*self.oracle_checker.for_row())
        self.store.setLayout(self.store_layout)

        # save/cancel buttons
        self.save = QtWidgets.QGroupBox("Mettre à jour les paramètres")
        self.save_layout = QtWidgets.QVBoxLayout(self.save)
        self.save_button = QtWidgets.QPushButton("&Enregistrer")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QtWidgets.QPushButton("&Annuler")
        self.cancel_button.clicked.connect(self.close)
        self.save_layout.addWidget(self.save_button)
        self.save_layout.addWidget(self.cancel_button)
        self.save.setLayout(self.save_layout)

        self.layout.addWidget(self.picserv, 0, 0)
        self.layout.addWidget(self.oracle, 0, 1)
        self.layout.addWidget(self.store, 1, 0)
        self.layout.addWidget(self.save, 1, 1)

        self.setLayout(self.layout)

    def save_settings(self):
        logger.info("Updating SETTINGS")
        for key, value in SETTINGS.items():
            if hasattr(self, key):
                ledit = getattr(self, key)
                if ledit.text():
                    SETTINGS.update({key: ledit.text()})
        save_settings(SETTINGS_FILE, SETTINGS)
        self.close()
