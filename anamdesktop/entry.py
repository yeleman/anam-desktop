#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import sys

from PyQt5 import QtWidgets

from anamdesktop import setlocale
from anamdesktop.ui.main import MainWindow


def main():

    app = QtWidgets.QApplication(sys.argv)
    setlocale()
    window = MainWindow()
    window.reset()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
