#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from anamdesktop import logger
from anamdesktop.ui.common import NA
from anamdesktop.utils import isototext
from anamdesktop.network import do_post
from anamdesktop.dbimport import import_target
from anamdesktop.ui.dialog import CollectActionDialog
from anamdesktop.oracle import ora_connect, ora_disconnect, ora_test


class ImportDialog(CollectActionDialog):
    ''' show collect meta-data and button to import it all into oracle DB '''

    TITLE = "Importer dans la BDD ANAM"

    def get_action_btn_label(self):
        return "importer {} cibles".format(self.nb_targets)

    def get_progress_maximum(self):
        return self.nb_targets

    @property
    def can_be_actioned(self):
        return self.nb_targets > 0  # now importing all targets

    def get_fields(self):
        nb_targets_str = "{nbi} ({nbih}H / {nbif}F)".format(
            nbi=self.nb_targets,
            nbih=self.nb_targets_male,
            nbif=self.nb_targets_female)
        return [
            ("Cercle", self.dataset.get('cercle', NA)),
            ("Commune", self.dataset.get('commune', NA)),
            ("Reçu le", isototext(self.dataset.get('started_on'))),
            ("Nb. Soumissions", str(self.nb_submissions)),
            ("Nb. cibles", nb_targets_str),
        ]

    def worker(self):
        ''' imports collect data into anam oracle DB

            - connect to database
            - loop on all targets ; for each
            - create a DOSSIER for the indigent/household
            - create a IM_PERSONNES_MOBILE for the indigent
            - create many IM_PERSO_PJ_MOBILE for the indigent
            - create zero-plus IM_PERSONNES_MOBILE for the indigent spouses
            - create many IM_PERSO_PJ_MOBILE for the indigent spouses
            - create zero-plus IM_PERSONNES_MOBILE for the indigent children
            - create many IM_PERSO_PJ_MOBILE for the indigent children
            - POST to anam-receiver to mark collect imported

            rollback if any of this failed '''

        try:
            assert ora_test()
            conn = ora_connect()
        except Exception as exp:
            logger.exception(exp)
            self.status_bar.set_error("Connexion impossible à la base Oracle. "
                                      "Vérifiez les paramètres.")
            return

        # will hold reference to both json IDs and oracle DB IDs
        mapping = {}
        nb_imported = 0
        self.progress_bar.setValue(self.progress_bar.maximum() // 2)
        for index, target in enumerate(self.get_indigents()):
            # retrieve name to update progress bar
            first_name = target.get("enquete/prenoms")
            last_name = target.get("enquete/nom")
            name = "{last} {firsts}".format(
                last=last_name.upper(),
                firsts=first_name.title())
            self.status_bar.setText(name)
            # self.progress_bar.setValue(index + 1)

            try:
                # import_target returns a DOS_ID: dict() of all mappings
                mapping.update(import_target(conn, target))
            except Exception as exp:
                logger.error("DB import error on #{}: {}".format(index, name))
                logger.exception(exp)
                self.status_bar.set_error(
                    "Impossible d'importer les données (ORACLE).\n"
                    "Les données n'ont pas été importées.\n{exp}"
                    .format(exp=exp))
                conn.rollback()
                ora_disconnect(conn)
                return

            # commit if every 1,000 indigents
            if index % 50 == 0:
                try:
                    conn.commit()
                    nb_imported += 50
                except Exception as exp:
                    logger.error("DB Commit error on #{}: {}".format(index, name))
                    logger.exception(exp)
                    self.status_bar.set_error(
                        "Impossible d'importer certaines données "
                        "(ORACLE/COMMIT/THOUSANDS).\n"
                        "ATTENTION: {nb} indigents ont été importés dans "
                        "la base de données Oracle !!\n{exp}"
                        .format(nb=nb_imported, exp=exp))
                    conn.rollback()
                    ora_disconnect(conn)
                    return

        # commit remaining batch of statements
        try:
            conn.commit()
            nb_imported = self.nb_targets
        except Exception as exp:
            logger.error("DB Commit error on last batch: {}".format(name))
            logger.exception(exp)
            self.status_bar.set_error(
                "Impossible d'importer les données (ORACLE/COMMIT/END).\n"
                "ATTENTION: {nb} indigents ont été importés dans "
                "la base de données Oracle !!\n{exp}"
                .format(nb=nb_imported, exp=exp))
            conn.rollback()
            return
        else:
            self.status_bar.set_success("Données Oracle importées.")
        finally:
            ora_disconnect(conn)

        # update progress UI as we're done
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_bar.setText("Finalisation…")

        # mark collect imported on anam-receiver and submits the mappings
        try:
            do_post("/collects/{cid}/mark_imported"
                    .format(cid=self.collect_id), mapping)
        except Exception as exp:
            logger.exception(exp)
            self.status_bar.set_error(
                "Impossible mettre à jour le service web ANAM.\n"
                "ATTENTION: {nb} indigents ont été importés dans la base "
                "de données Oracle !!\n{exp}".format(nb=nb_imported, exp=exp))
            return
        else:
            self.status_bar.set_success("Import terminé avec success.")
