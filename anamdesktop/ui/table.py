#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from PyQt5 import QtWidgets, QtCore, QtGui


class QTable(QtWidgets.QTableWidget):
    ''' custom design QTable (stetched, scroll) for passed headers '''

    def __init__(self, parent, *args, **kwargs):
        self.headers = kwargs.pop("headers")
        super().__init__(parent, *args, **kwargs)
        self.initUI()

    def initUI(self):
        self.setAutoScroll(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)
        self.refresh()

    def refresh(self):
        for index, header in enumerate(self.headers.values()):
            self.setHorizontalHeaderItem(index, QCellHeaderItem())

        self.setHorizontalHeaderLabels(self.headers.values())
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setVisible(True)
        self.resizeColumnsToContents()

        self.horizontalHeader().setSectionResizeMode(
            self.horizontalHeader().Stretch)

        self.update()


class QCellItem(QtWidgets.QTableWidgetItem):
    ''' custom design (alignment) QTableWidgetItem '''

    def __init__(self, *args, **kwargs):
        self.centered = kwargs.pop('centered') \
            if 'centered' in kwargs else False

        super().__init__(*args, **kwargs)

        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

        if self.centered:
            self.setTextAlignment(
                QtCore.Qt.AlignHCenter |
                QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter)
        else:
            self.setTextAlignment(
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)


class QCellHeaderItem(QtWidgets.QTableWidgetItem):
    ''' custom design (font, alignment) QTableWidgetItem for headers '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = QtGui.QFont()
        font.setBold(True)
        self.setFont(font)

        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

        self.setTextAlignment(
            QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter |
            QtCore.Qt.AlignCenter)
