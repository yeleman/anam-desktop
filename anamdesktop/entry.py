#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import sys

from PyQt5 import QtWidgets, QtCore

from anamdesktop import setlocale, logger
from anamdesktop.ui.main import MainWindow


def destroy():
    logger.info("Exiting Application")
    QtCore.QCoreApplication.instance().quit
    sys.exit(0)


def main():
    logger.info("Starting Application")
    app = QtWidgets.QApplication(sys.argv)
    app.lastWindowClosed.connect(destroy)
    setlocale()
    window = MainWindow()
    window.reset()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
