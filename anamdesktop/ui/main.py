#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import json
import shutil

from PyQt5 import QtWidgets, QtGui, QtCore

from anamdesktop.network import do_post
from anamdesktop.ui.table import QTable
from anamdesktop.ui.home import HomeWidget
from anamdesktop.ui.upload import UploadDialog
from anamdesktop.ui.dbimport import ImportDialog
from anamdesktop.ui.settings import SettingsDialog
from anamdesktop.utils import open_file, get_version
from anamdesktop.ui.pictures import ImagesCopyDialog
from anamdesktop import (logger, UI_SIZE, IS_MAC,
                         LOG_FILE, HELP_FILE, APP_NAME, DEVELOPER)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.destroyed.connect(self.exit)
        self.initUI()

    def initUI(self):
        self.resize(*UI_SIZE)
        self.setWindowTitle("ANAM Desktop")
        self.setWindowIcon(QtGui.QIcon(
            os.path.join('img', 'anam-desktop.png')))

        menubar = QtWidgets.QMenuBar(None if IS_MAC else self)
        file_menu = menubar.addMenu("&Fichier")

        log_menu = file_menu.addMenu("&Logs")
        open_log_action = QtWidgets.QAction("Voir les logs", self)
        open_log_action.setShortcut('Ctrl+L')
        open_log_action.triggered.connect(self.openLogFile)
        export_log_action = QtWidgets.QAction("Exporter les logs", self)
        export_log_action.triggered.connect(self.exportLogFile)
        log_menu.addAction(open_log_action)
        log_menu.addAction(export_log_action)

        file_menu.addSeparator()

        upload_action = QtWidgets.QAction("Transmettre un export JSON", self)
        upload_action.triggered.connect(self.showUploadDialog)
        file_menu.addAction(upload_action)

        # on Mac, the following two are captured and not on File Menu
        if not IS_MAC:
            file_menu.addSeparator()

        settigs_action_name = "Preferences" if IS_MAC else "&Paramètres"
        settigs_action = QtWidgets.QAction(settigs_action_name, self)
        settigs_action.setShortcut("Ctrl+P")
        settigs_action.triggered.connect(self.showSettings)
        file_menu.addAction(settigs_action)

        exit_action = QtWidgets.QAction("&Quitter", self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip("Quitter l'application")
        exit_action.triggered.connect(self.exit)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menubar.addMenu("Affichage")
        self.toggle_archived_action = QtWidgets.QAction(
            "Afficher les archives", self)
        self.toggle_archived_action.setShortcut('Ctrl+A')
        self.toggle_archived_action.toggled.connect(
            self.toggle_archives_visibility)
        self.toggle_archived_action.setCheckable(True)
        view_menu.addAction(self.toggle_archived_action)

        self.toggle_imagesimport_action = QtWidgets.QAction(
            "Activer import d'images pour tous", self)
        self.toggle_imagesimport_action.setShortcut('Ctrl+I')
        self.toggle_imagesimport_action.toggled.connect(
            self.toggle_images_import)
        self.toggle_imagesimport_action.setCheckable(True)
        view_menu.addAction(self.toggle_imagesimport_action)

        # Help Menu (only win)
        help_menu = menubar.addMenu("&Aide")
        about_action = QtWidgets.QAction(
            "About" if IS_MAC else "À propos", self)
        about_action.setShortcut('Ctrl+H')
        about_action.triggered.connect(self.showAbout)
        open_help_action = QtWidgets.QAction("Guide utilisateur", self)
        open_help_action.setShortcut('F1')
        open_help_action.triggered.connect(self.openHelpFile)
        help_menu.addAction(about_action)
        help_menu.addAction(open_help_action)

        self.setMenuBar(menubar)
        self.setMenuWidget(menubar)

    def exit(self):
        self.close()
        self.destroy()

    def reset(self):
        ''' displays a new instance of Home (thus refreshing its contents) '''
        self.displayHome()

    def switchPage(self, widget):
        ''' change content of the MainWindow to `widget` '''
        self.setCentralWidget(widget)
        if isinstance(widget, QTable):
            widget.resize(self.width(), self.height())
        self.show()

    def displayHome(self):
        logger.info("Refreshing Home")
        self.switchPage(HomeWidget(self).content)

    def showAbout(self):
        QtWidgets.QMessageBox.information(
            self,
            "À propos de {}".format(APP_NAME),
            "{name} v{version}\n\n{dev}".format(
                name=APP_NAME, version=get_version(), dev=DEVELOPER),
            QtWidgets.QMessageBox.Ok)

    def showSettings(self):
        logger.info("Opening Settings")
        settings = SettingsDialog()
        settings.show()
        settings.exec_()
        logger.info("Closing Settings")
        self.reset()  # refreshing to apply settings changes

    def showImportDialog(self, collect_id):
        logger.info("Opening Import Dialog for #{}".format(collect_id))
        ImportDialog(collect_id=collect_id).exec_()
        logger.info("Closing Import Dialog for #{}".format(collect_id))
        self.reset()  # refreshing to apply collect's status change

    def showImagesCopyDialog(self, collect_id):
        logger.info("Opening Copy Dialog for #{}".format(collect_id))
        ImagesCopyDialog(collect_id=collect_id).exec_()
        logger.info("Closing Copy Dialog for #{}".format(collect_id))
        self.reset()  # refreshing to apply collect's status change

    def showUploadDialog(self):
        ''' displays an open file dialog to pick a json export file

            if file is legit, fires up an UploadDialog '''
        upload_fpath = QtWidgets.QFileDialog().getOpenFileName(
            self, "Séléctionner le fichier d'export JSON de la collecte",
            "C:/", filter="json (*.json)")
        if not upload_fpath or not upload_fpath[0]:
            return
        upload_fpath = upload_fpath[0]
        logger.info("Reading {} for upload".format(upload_fpath))

        try:
            assert os.path.exists(upload_fpath)
            with open(upload_fpath, 'r') as f:
                dataset = json.load(f)
            assert 'targets' in dataset
        except Exception as exp:
            logger.exception(exp)
            QtWidgets.QMessageBox.warning(
                self,
                "Impossible de lire le fichier JSON",
                "Le fichier sélectionné n'est pas un fichier "
                "d'export de collecte valide.\n"
                "Vérifiez le fichier et réessayez.",
                QtWidgets.QMessageBox.Ok)
        else:
            logger.info("Opening Upload Dialog for {}".format(upload_fpath))
            UploadDialog(dataset=dataset, fpath=upload_fpath).exec_()
            logger.info("Closing Upload Dialog for {}".format(upload_fpath))
            self.reset()

    def openHelpFile(self):
        ''' opens help file in external reader '''
        logger.info("Opening help file for display")
        open_file(HELP_FILE)

    def openLogFile(self):
        ''' opens log file in external reader '''
        logger.info("Opening log file for display")
        open_file(LOG_FILE)

    def exportLogFile(self):
        ''' displays a filesave dialog to copy log file to '''
        export_fpath = QtWidgets.QFileDialog().getSaveFileName(
            self, "Enregistrer le fichier de logs sous…",
            "C:/", filter="log (*.log *.txt)")

        if export_fpath and export_fpath[0]:
            shutil.copy(LOG_FILE, export_fpath[0])
            logger.info("Exported log file to {}".format(export_fpath[0]))

    @property
    def display_archived(self):
        ''' shortcut to actual display status of archives '''
        return self.toggle_archived_action.isChecked()

    @property
    def allow_imagesimport(self):
        ''' shortcut to actual display status of archives '''
        return self.toggle_imagesimport_action.isChecked()

    def toggle_archives_visibility(self, checked):
        ''' refreshes home page's content on toggle '''
        self.reset()

    def toggle_images_import(self, checked):
        ''' refreshes home page's content on toggle '''
        self.reset()

    def archive(self, collect_id):
        ''' archive the requested collect onto the remote anam-receiver

            triggered by Home's table button '''
        try:
            do_post('/collects/{id}/archive'.format(id=collect_id))
            self.reset()
        except Exception as exp:
            logger.error("Failed to archive #{}".format(collect_id))
            logger.exception(exp)
        else:
            logger.info("Archived #{}".format(collect_id))

    def unarchive(self, collect_id):
        ''' unarchive the requested collect onto the remote anam-receiver

            triggered by Home's table button '''
        try:
            do_post('/collects/{id}/unarchive'.format(id=collect_id))
            self.reset()
        except Exception as exp:
            logger.error("Failed to unarchive #{}".format(collect_id))
            logger.exception(exp)
        else:
            logger.info("Unarchived #{}".format(collect_id))
