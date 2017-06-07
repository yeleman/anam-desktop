#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import random
import datetime

import cx_Oracle

from anamdesktop.locations import get_asserted_commune_id
from anamdesktop.dbimport import cl, mx, ANAMDB_USER_ID, ANAMDB_SHORTDATE_FMT


def create_dossier(conn, ident, target):
    ''' insert an IM_DOSSIERS into DB and returns its DOS_ID '''

    stmt = ("INSERT INTO ANAM.IM_DOSSIERS ("
            "DOS_ID, DOS_DATE, DOS_STATUT, "
            "TYDO_ID, OGD_ID, "
            "DOS_CREE_PAR, DOS_DATE_CREATION, DOS_IMPUTATION, "
            "LOC_CODE, DOS_PERSO_NOM, DOS_PERSO_PRENOM, DOS_CERTIF_IND, "
            "DOS_TYP_SAISIE, OPV_CODE) VALUES ("
            ":dos_id, :dos_date, :dos_statut, "
            ":tydo_id, :ogd_id, "
            ":dos_cree_par, :dos_date_creation, :dos_imputation, "
            ":loc_code, :dos_perso_nom, :dos_perso_prenom, :dos_certif_ind, "
            ":dos_type_saisie, :opv_code) returning DOS_ID into :gen_dos_id")

    now = datetime.datetime.now()
    today = datetime.datetime(*now.timetuple()[:3])

    # TODO: replace with appropriate generated value
    incr = random.randint(1, 10000)
    dos_id = "{incr}-{date}".format(incr=incr,
                                    date=now.strftime(ANAMDB_SHORTDATE_FMT))

    certif_ind = "N°CI_{dos_id}".format(dos_id=dos_id)

    cercle_slug = target.get("localisation-enquete/lieu_cercle")
    commune_slug = target.get("localisation-enquete/lieu_commune")
    location_id = get_asserted_commune_id(commune_slug, cercle_slug)

    last_name = cl(target.get("enquete/nom")).upper()
    first_name = cl(target.get("enquete/prenoms")).upper()

    payload = {
        'dos_id': dos_id,
        'dos_date': today,
        'dos_statut': "NV",
        'tydo_id': "IND",
        'ogd_id': 40,
        'dos_cree_par': mx(ANAMDB_USER_ID, 30),
        'dos_date_creation': now,
        'dos_imputation': "PRIM",
        'loc_code': int(location_id),
        'dos_certif_ind': mx(certif_ind, 120),
        'dos_perso_nom': mx(last_name, 60),
        'dos_perso_prenom': mx(first_name, 60),
        'dos_type_saisie': "N",
        'opv_code': 1,
    }

    cursor = conn.cursor()
    gen_dos_id = None
    gen_dos_id_var = cursor.var(cx_Oracle.STRING)
    payload.update({'gen_dos_id': gen_dos_id_var})
    try:
        cursor.execute(stmt, payload)
        gen_dos_id = gen_dos_id_var.getvalue()
    except:
        raise
    finally:
        cursor.close()

    return gen_dos_id
