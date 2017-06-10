#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import threading

from PyQt5 import QtWidgets, QtCore

from anamdesktop.network import do_get
from anamdesktop.ui.common import DialogTitle, StatusLabel


class ActionDialogButton(QtWidgets.QPushButton):
    ''' QPushButton storing ref to collect_id and MainWindow method to call '''
    def __init__(self, collect_id, method, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collect_id = collect_id
        self.method = method
        self.clicked.connect(self.on_click)

    def on_click(self):
        mainw = self.parent().parent().parent()
        getattr(mainw, self.method)(self.collect_id)


class CollectDialogInterface(object):
    ''' provides shortcut access to properties from self.dataset '''

    def get_targets(self):
        return self.dataset.get("dataset", {}).get("targets")

    @property
    def nb_targets(self):
        return len(self.get_targets())

    @property
    def name(self):
        return ("Enquête sociale de {commune}, cercle de {cercle}"
                .format(commune=self.dataset.get('commune'),
                        cercle=self.dataset.get('cercle')))

    def get_indigents(self):
        return [target
                for target in self.dataset.get('dataset', {})
                                          .get('targets', [])
                if target.get('certificat-indigence')]

    @property
    def nb_indigents(self):
        return len(self.get_indigents())

    @property
    def nb_indigents_male(self):
        if self.nb_indigents == 0:
            return 0
        return sum([1
                    for target in self.get_indigents()
                    if target.get("enquete/sexe") == "masculin"])

    @property
    def nb_indigents_female(self):
        if self.nb_indigents == 0:
            return 0
        return sum([1
                    for target in self.get_indigents()
                    if target.get("enquete/sexe") == "feminin"])

    @property
    def nb_non_indigents(self):
        return self.dataset.get('nb_non_indigents')

    @property
    def nb_submissions(self):
        return self.dataset.get('nb_submissions')

    @property
    def ona_form_id(self):
        return self.dataset.get('ona_form_id')


class CollectActionDialog(QtWidgets.QDialog, CollectDialogInterface):

    TITLE = "CollectActionDialog"
    SIZE = (350, 250)
    AUTO_INITUI = True
    DOWNLOAD_DATASET = True

    def __init__(self, collect_id=None, dataset=None, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.collect_id = None
        self.dataset = None

        if self.DOWNLOAD_DATASET:
            assert collect_id
            self.download_dataset(collect_id)
        else:
            self.dataset = dataset or {}

        if self.AUTO_INITUI:
            self.initUI()

    def download_dataset(self, collect_id):
        self.collect_id = collect_id
        self.dataset = (do_get('/collects/{}'.format(self.collect_id)) or {}) \
            .get('collect')

    def get_title(self):
        ''' override with yout dialog's title '''
        return self.ona_form_id

    def get_action_btn_label(self):
        ''' override with label for your action button '''
        return "action"

    def get_progress_minimum(self):
        ''' override with min value for your progress bar '''
        return 0

    def get_progress_maximum(self):
        ''' override with max value for your progress bar '''
        return 100

    @property
    def can_be_actioned(self):
        ''' override with bool whether action button should be active '''
        return False

    def get_fields(self):
        ''' override with list of tuples of label/value

            label and value can be either str or QWidget '''
        return []

    def worker(self):
        ''' override this with your action code

            please update:
                - progress bar
                - status bar with self.status_bar.set_*
                    set_success, set_warning, set_error '''

        self.progress_bar.setValue(self.get_progress_maximum())
        self.status_bar.set_warning("You should have override me!")

    def initUI(self):
        self.setWindowTitle(self.TITLE)
        self.setModal(True)
        self.resize(*self.SIZE)

        self.layout = QtWidgets.QGridLayout()

        # prepare action button
        self.action_button = QtWidgets.QPushButton(self.get_action_btn_label())
        self.action_button.clicked.connect(self.start_action)
        if not self.can_be_actioned:
            self.action_button.setDisabled(True)

        # prepare progress bar (appears on button click - replaces it)
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximum(self.get_progress_maximum())
        self.progress_bar.setMinimum(self.get_progress_minimum())
        self.progress_bar.setValue(self.get_progress_minimum())

        # prepare status bar
        self.status_bar = StatusLabel()

        # display a title
        self.layout.addWidget(DialogTitle(self.get_title()), 0, 0, 1, 2)

        for index, (label, value) in enumerate(self.get_fields()):
            row = index + 1  # row0 is title row

            label_widget = QtWidgets.QLabel(label) \
                if isinstance(label, str) else label
            self.layout.addWidget(label_widget, row, 0)

            value_widget = QtWidgets.QLabel(value) \
                if isinstance(value, str) else value
            self.layout.addWidget(value_widget, row, 1)

        row += 1  # spacing

        # action button
        self.layout.addWidget(self.action_button, row, 0, 1, 2)
        row += 1

        self.layout.addWidget(self.status_bar, row, 0, 1, 2)
        row += 1

        self.setLayout(self.layout)

    def start_action(self, *args, **kwargs):
        threading.Thread(target=self.action_worker, args=()).start()

    def action_worker(self, *args, **kwargs):
        # disable button to prevent double click
        self.action_button.setDisabled(True)

        # replace button by progress bar
        self.layout.replaceWidget(self.action_button, self.progress_bar,
                                  QtCore.Qt.FindChildrenRecursively)
        self.layout.removeWidget(self.action_button)
        self.action_button.close()

        self.worker()
