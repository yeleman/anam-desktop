#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import datetime

from anamdesktop import logger
from anamdesktop.ui.common import NA
from anamdesktop.utils import datetotext
from anamdesktop.ui.dialog import CollectActionDialog
from anamdesktop.network import do_post, test_webservice


class UploadDialog(CollectActionDialog):
    ''' display basic meta on selected file's data and allow upload of it '''

    TITLE = "Transmission manuelle"
    DOWNLOAD_DATASET = False

    def __init__(self, dataset, *args, **kwargs):
        self.fpath = kwargs.pop('fpath') if 'fpath' in kwargs else None
        super().__init__(dataset=dataset, *args, **kwargs)

    def get_targets(self):
        ''' overriden cause our dataset is flat to ['dataset'] '''
        return self.dataset.get("targets")

    def get_action_btn_label(self):
        return "Transmettre cette collecte"

    def get_progress_maximum(self):
        return self.nb_targets

    @property
    def can_be_actioned(self):
        return self.nb_targets > 0

    def get_fields(self):
        try:
            created_on = datetotext(datetime.datetime.utcfromtimestamp(
                os.path.getctime(self.fpath)))
        except:
            created_on = NA
        return [
            ("Cercle", self.dataset.get('cercle', NA)),
            ("Commune", self.dataset.get('commune', NA)),
            ("Fichier créé le", created_on),
            ("Nb. Soumissions", str(self.nb_targets)),
        ]

    def worker(self):
        ''' upload (POST) dataset to anam-receiver '''

        try:
            assert test_webservice()
        except Exception as exp:
            logger.exception(exp)
            self.status_bar.set_error(
                "Connexion impossible au service anam-receiver. "
                "Vérifiez les paramètres.")
            return

        try:
            do_post("/upload/", payload=self.dataset)
        except Exception as exp:
            logger.exception(exp)
            self.status_bar.set_error(
                "Échec de la transmission manuelle.\n"
                "Vérifiez le fichier, le réseau et recommencez.")
        else:
            self.status_bar.set_success(
                "Transmission manuelle terminée avec succès.")
        finally:
            self.progress_bar.setValue(self.progress_bar.maximum())
