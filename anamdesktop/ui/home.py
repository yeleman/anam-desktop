#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from collections import OrderedDict

from PyQt5 import QtWidgets

from anamdesktop.network import do_get
from anamdesktop.utils import isototext
from anamdesktop.ui.common import ErrorLabel
from anamdesktop.ui.table import QTable, QCellItem
from anamdesktop.ui.dialog import ActionDialogButton


class ArchiveToggleButton(QtWidgets.QPushButton):
    ''' togglable QPushButton to archive/unarchive a collect

        references the MainWindow which hold the actual actions
        toggles its text and collect status '''

    def __init__(self, collect_id, archived, *args, **kwargs):
        super().__init__("", *args, **kwargs)
        self.collect_id = collect_id
        self.archived = archived
        self.clicked.connect(self.on_click)
        self.update_text()

    def update_text(self):
        self.setText("désarchiver" if self.archived else "archiver")

    def on_click(self):
        mainw = self.parent().parent().parent().parent()
        action = mainw.unarchive if self.archived else mainw.archive

        try:
            action(self.collect_id)
            self.archived = not self.archived
            self.update_text()
        except:
            pass


class HomeWidget(QtWidgets.QWidget):
    ''' main widget representing a table-list of all collects retrieved '''

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.initUI()

    def initUI(self):
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                           QtWidgets.QSizePolicy.Ignored)
        self.layout = QtWidgets.QVBoxLayout()

        self.collects = (do_get('/collects', or_none=True) or {}) \
            .get('collects')

        if self.get_collects() is not None:
            self.content = self.create_table()
        else:
            self.content = ErrorLabel(
                "Impossible de récupérer les données.<br />"
                "Vérifier les paramètres.")

        self.layout.addWidget(self.content)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.content:
            self.content.resize(self.width(), self.height())

    @property
    def display_archived(self):
        ''' shortcut to MainWindow's display_archived boolean '''
        return self.parent().display_archived

    def get_collects(self):
        ''' filtered (archive-wise) list of retrieved collects '''
        if self.collects is None:
            return None
        return [collect for collect in self.collects
                if not collect.get('archived', False) or self.display_archived]

    def create_table(self):
        headers = OrderedDict([
            ('cercle', "Cercle"),
            ('commune', "Commune"),
            ('id', "ID"),
            ('nb_submissions', "Cibles"),
            ('started_on', "Reçu le"),
            ('action_import', "Import"),
            ('action_copy', "Images"),
            ('action_archive', "Archivage"),
        ])

        cercle_col, commune_col, ona_id_col, nb_sum_col, \
            received_on_col, import_btn_col, copy_img_col, \
            archive_btn_col = range(0, 8)

        table = QTable(self, headers=headers)
        table.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                  QtWidgets.QSizePolicy.Minimum))

        table.setRowCount(len(self.get_collects()))
        table.setColumnCount(len(headers))

        for row_id, collect in enumerate(self.get_collects()):
            # cercle
            table.setItem(row_id, cercle_col, QCellItem(collect.get('cercle')))

            # commune
            table.setItem(row_id, commune_col,
                          QCellItem(collect.get('commune')))

            # ID (ona-form-id)
            table.setItem(row_id, ona_id_col,
                          QCellItem(collect.get('ona_form_id')))

            # Nb. of submissions
            table.setItem(row_id, nb_sum_col,
                          QCellItem(str(collect.get('nb_submissions')),
                                    centered=True))

            # Received on (started_on)
            table.setItem(row_id, received_on_col,
                          QCellItem(isototext(collect.get('started_on'))))

            ''' import button '''
            import_button = ActionDialogButton(collect.get('id'),
                                               'showImportDialog',
                                               "importer")

            # can not import a collect which has already been imported
            if collect.get('imported'):
                import_button.setText(isototext(collect.get('imported_on')))

            import_button.setDisabled(
                not collect.get('can_be_imported', False))

            table.setCellWidget(row_id, import_btn_col, import_button)

            ''' images copy button '''
            copy_button = ActionDialogButton(collect.get('id'),
                                             'showImagesCopyDialog',
                                             "copier images")

            # collect must have been imported to allow images copy
            copy_button.setDisabled(
                not collect.get('can_be_copied', False))

            # just visualy highlight that it's already been copied (redoable)
            if collect.get('images_copied'):
                copy_button.setText(isototext(collect.get('images_copied_on')))

            table.setCellWidget(row_id, copy_img_col, copy_button)

            ''' archive button '''
            archive_button = ArchiveToggleButton(
                collect.get('id'), collect.get('archived', False))

            table.setCellWidget(row_id, archive_btn_col, archive_button)

        # update columns adjustments
        table.refresh()

        return table
