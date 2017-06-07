#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from PyQt5 import QtWidgets, QtGui, QtCore

NA = "n/a"


class ErrorLabel(QtWidgets.QLabel):
    ''' a red, bold QLabel to display app-wide error messages '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = QtGui.QFont()
        font.setBold(True)
        self.setFont(font)
        self.setStyleSheet('color: red;')


class DialogTitle(QtWidgets.QLabel):
    '''  a larger centered text titling the dialog window '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(20)
        self.setFont(font)
        self.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)


class StatusLabel(QtWidgets.QLabel):
    ''' a QLabel displaying live-changing progress then status of action

        status is color-coded based on method used (success, warning, error)
        self.on_click if defined should be a callable and it then called
        on click '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        font = QtGui.QFont()
        font.setPointSize(10)
        self.setFont(font)

        self.on_click = None

    def change_color(self, color):
        self.setStyleSheet('color: ' + color + ';')

    def set_color_text(self, color, text):
        self.change_color(color)
        self.setText(text)

    def set_success(self, text):
        self.set_color_text('green', text)

    def set_warning(self, text):
        self.set_color_text('orange', text)

    def set_error(self, text):
        self.set_color_text('red', text)

    def mousePressEvent(self, event):
        if self.on_click is not None:
            self.on_click()
