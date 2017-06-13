#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import datetime

from PyQt5 import QtWidgets

from anamdesktop import logger
from anamdesktop.ui.common import NA
from anamdesktop.network import do_post
from anamdesktop.ui.dialog import CollectActionDialog
from anamdesktop.samba import copy_files, test_connection
from anamdesktop.utils import (
    get_folder_name, VALID_ATTACHMENTS, isototext, open_file)

import smb

# types of failures for image copy
MISSING = 1
COPYFAILED = 2
COPY_ERROR_TYPES = {
    MISSING: "SOURCE MANQUANTE",
    COPYFAILED: "ERREUR COPIE PARTAGE",
}


class ImagesCopyDialog(CollectActionDialog):
    ''' show collect meta and button to copy all images from USB to samba '''

    TITLE = "Copie des images"
    AUTO_INITUI = False  # we need to set source_dir first

    def __init__(self, collect_id, *args, **kwargs):
        super().__init__(collect_id, *args, **kwargs)
        self.source_dir = None
        self.initUI()

    @property
    def error_log_fname(self):
        return "erreurs-copie.log"

    @property
    def mapping(self):
        return self.dataset.get('targets')

    @property
    def nb_dossiers(self):
        return len(self.mapping.keys())

    @property
    def nb_personnes(self):
        nbp = 0
        for dossier_data in self.mapping.values():
            nbp += len(dossier_data.keys()) - 1  # 'dossier' is not person-rel
        return nbp

    @property
    def nb_images(self):
        nbi = 0
        for target in self.get_targets():

            seen_ids = []
            for attachment in target.get("_attachments"):
                # skip other attachments
                if attachment['labels']['slug'] not in VALID_ATTACHMENTS:
                    continue

                # skip if already copied (_hamed as duplicates)
                if attachment['id'] in seen_ids:
                    continue
                else:
                    seen_ids.append(attachment['id'])

                nbi += 1
        return nbi

    def select_source_dir(self, *args, **kwargs):
        ''' show folder picker and update `source_dir` and select_feedback '''
        fpath = str(QtWidgets.QFileDialog.getExistingDirectory(
            self, "Séléctionner le chemin de la clé USB"))

        # ensure selected folder as a `Dossiers` subfolder in it
        self.source_dir = "/".join((fpath, 'Dossiers')) \
            if fpath and 'Dossiers' in os.listdir(fpath) else None

        # update button activeness
        self.action_button.setDisabled(
            not self.nb_targets or not self.source_dir)

        # update feeback
        self.select_feedback.setText(
            self.source_dir if self.action_button.isEnabled()
            else "Dossier source incorrect")

    def open_user_log(self):
        ''' opens the images-copy-error log file in external reader '''
        open_file(self.error_log_fname)

    def get_action_btn_label(self):
        return "Copier {} images sur le partage".format(self.nb_images)

    def get_progress_maximum(self):
        return self.nb_indigents

    @property
    def can_be_actioned(self):
        return self.nb_targets and self.source_dir

    def get_fields(self):
        # already-copied string
        if not self.dataset.get('images_copied'):
            already_copied = "non"
        else:
            already_copied = isototext(self.dataset.get('images_copied_on'))
            nbe = self.dataset.get('images_nb_error')
            if nbe > 0:
                already_copied += " ({nbe} erreurs)".format(nbe=nbe)

        # select button and its feedback to select USB source dir
        self.select_button = QtWidgets.QPushButton("Sélectionner clé USB")
        self.select_button.clicked.connect(self.select_source_dir)
        self.select_feedback = QtWidgets.QLabel()

        return [
            ("Cercle", self.dataset.get('cercle', NA)),
            ("Commune", self.dataset.get('commune', NA)),
            ("Importé le", isototext(self.dataset.get('imported_on'))),
            ("Nb. dossiers", str(self.nb_dossiers)),
            ("Nb. personnes", str(self.nb_personnes)),
            ("Nb. images", str(self.nb_images)),
            ("Déjà copiés ?", already_copied),
            (self.select_button, self.select_feedback),
        ]

    def action_worker(self, *args, **kwargs):
        super().action_worker(*args, **kwargs)

        # disable folder change to prevent race condition
        self.select_button.setDisabled(True)

    def worker(self):
        ''' copy all expected images from USB folder to samba share

            - loop on targets ; for each
            - recompute original folder name
            - compute list of expected attachment images (for whole household)
            - ensure original files are present (or add to errors list)
            - retrieve DB IDs from mapping
            - compute new files and folders names for share

            - ensure samba share is writable
            - copy files to samba share (failures to errors list)
            - if errors not empty, write a summary in a log file
            - mark collect images copied on anam-receiver
            - display feedback '''

        mappings = self.dataset.get("targets", {})

        error_list = []

        # first prepare a full list of files to copy
        copy_list = {}
        for index, target in enumerate(self.get_targets()):
            # retrieve basic information from target
            try:
                ident = target.get("ident")
                logger.debug(ident)
                mapping = mappings.get(ident)
                dos_id = mapping.get('dossier')
                indigent_perso_id = mapping.get('indigent')
                first_name = target.get("enquete/prenoms")
                last_name = target.get("enquete/nom")
                name = "{last} {firsts}".format(
                    last=last_name.upper(),
                    firsts=first_name.title())
                folder = get_folder_name(ident, last_name, first_name)
                assert dos_id
                assert indigent_perso_id
                assert name
                assert folder
            except Exception as exp:
                # should NEVER happen
                logger.error("Missing indigent data in dataset")
                logger.exception(exp)

                self.status_bar.set_error(
                    "Données manquante sur les indigents.\n"
                    "L'import est peut-être corrompu ?")
                return

            copy_list[ident] = {'label': "{n}: {d}".format(n=name, d=dos_id),
                                'files': []}

            seen_ids = []
            for attachment in target.get("_attachments"):
                attach_slug = attachment['labels']['slug']

                # skip other attachments
                if attach_slug not in VALID_ATTACHMENTS:
                    continue

                # skip if already copied (_hamed as duplicates)
                if attachment['id'] in seen_ids:
                    continue
                else:
                    seen_ids.append(attachment['id'])

                # origin file
                fname = attachment['export_fname']
                fpath = os.path.join(self.source_dir, folder, fname)

                # find its perso_id
                if 'epouse' in fname or 'enfant' in fname:
                    perso_id = mapping.get(fname.split("_", 2)[1])
                    if 'epouse' in fname:
                        perso_type = 'conjoint'
                    elif 'enfant' in fname:
                        perso_type = 'enfant'
                else:
                    perso_id = indigent_perso_id
                    perso_type = 'assure'

                # build destination file name and path
                nfname = "{pid}_{ptype}_{dtype}.jpg".format(
                    pid=perso_id, dtype=attach_slug, ptype=perso_type)
                nfpath = "/".join([dos_id[-4:], dos_id, nfname])

                # update status bar to show we're working on it
                self.status_bar.setText("{name}: {fpath}".format(
                    name=name, fpath=nfpath))

                # skip if the origin file is not present
                if not os.path.exists(fpath):
                    error_list.append((fpath, nfpath, MISSING))
                    continue

                # make sure we're not adding duplicates
                if not (fpath, nfpath) in copy_list[ident]['files']:
                    copy_list[ident]['files'].append((fpath, nfpath))

        # check error list to fail early if the source is compromise
        if len(error_list) >= self.nb_images:
            self.status_bar.set_error(
                "Aucune image accessible depuis la source.\n"
                "Vérifiez la source et recommencez.")
            return

        self.status_bar.setText("Connexion au partage…")

        # ensure destination is ready to fail early if not
        if not test_connection():
            self.status_bar.set_error(
                "Impossible d'écrire sur le partage.\n"
                "Vérifiez les paramètres et recommencez.")
            return

        self.status_bar.setText("Connecté au partage.")

        # start file copies from copy list
        for index, copy_data in enumerate(copy_list.values()):
            # update status and progress bar (copies are bundled by dossier)
            self.progress_bar.setValue(index + 1)

            copy_progress = "{label}... copie de {nb} fichiers".format(
                label=copy_data['label'], nb=len(copy_data['files']))
            self.status_bar.setText(copy_progress)

            success = False
            failures = []
            try:
                success, failures = copy_files(copy_data['files'])
            except smb.base.SMBTimeout as exp:
                logger.exception(exp)
                self.status_bar.set_error(
                    "Perte de connexion avec le partage.\n"
                    "Vérifiez les paramètres et le réseau et recommencez.")
                return
            except Exception as exp:
                logger.exception(exp)

            # keep track of failed copies
            if not success:
                error_list += [(l, d, COPYFAILED) for l, d in failures]

        # copy is over
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_bar.setText("Finalisation…")

        # return error and don't upload if only errors
        nb_errors = len(error_list)
        if nb_errors == self.nb_images:
            self.status_bar.set_error(
                "Aucune image n'a pu être copiée.\n"
                "Vérifiez la source et les paramètres et recommencez.")
            return

        # upload results
        try:
            payload = {
                'images_nb_total': self.nb_images,
                'images_nb_error': nb_errors,
            }
            do_post("/collects/{cid}/mark_images_copied"
                    .format(cid=self.collect_id), payload=payload)
            upload_success = True
        except Exception as exp:
            logger.exception(exp)
            upload_success = False

        # display feedback
        if nb_errors == 0 and upload_success:
            self.status_bar.set_success(
                "Copie des images terminée avec succès.")
        else:
            msg = "Copie partielle des images terminée.\n" \
                "{nbe} erreurs sur {nbt} images.".format(
                    nbe=nb_errors, nbt=self.nb_images)
            if not upload_success:
                msg += "\nImpossible de transmettre les résultats de la copie."
            self.status_bar.set_warning(msg)

        # prepare a log file if partial copy
        if nb_errors:
            with open(self.error_log_fname, 'w') as f:
                # initial statistics
                f.write("Copie partielle des images de la collecte {id}.{cr}"
                        "Date de la copie: {date}.{cr}"
                        "Nb. images: {nbt}.{cr}"
                        "Nb. erreurs: {nbe}.{cr}{cr}".format(
                            cr=os.linesep,
                            id=self.ona_form_id,
                            date=datetime.datetime.now().isoformat(),
                            nbt=self.nb_images,
                            nbe=nb_errors))

                # list of [REASON] source -> destination lines
                for fpath, nfpath, error in error_list:
                    f.write("[{e}] {s} ---> {d}{cr}".format(
                        cr=os.linesep,
                        e=COPY_ERROR_TYPES.get(error),
                        s=fpath, d=nfpath))

            # make status bar clickable (opens log in reader)
            self.status_bar.on_click = self.open_user_log
