#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime

from anamdesktop.locations import get_asserted_commune_id
from anamdesktop.dbimport import cl, mx, nname, ANAMDB_USER_ID


def request_dos_id(conn):
    stmt = ("SELECT LPAD(ANAM.SQ_DAY_DOSS.NEXTVAL, 4, '0') || '-' || "
            "LPAD(TO_CHAR (SYSDATE, 'FMDD'), 2, '0') || "
            "LPAD(TO_CHAR (SYSDATE, 'FMMM'), 2, '0') || "
            "TO_CHAR (SYSDATE, 'FMRRRR') INTO :gen_dos_id FROM DUAL")

    cursor = conn.cursor()
    gen_dos_id = None
    try:
        cursor.execute(stmt)
        gen_dos_id = cursor.fetchone()[-1]
    except:
        raise
    finally:
        cursor.close()

    return gen_dos_id


def create_dossier(conn, ident, target):
    ''' insert an IM_DOSSIERS_MOBILE into DB and returns its DOS_ID '''

    stmt = ("INSERT INTO IM_DOSSIERS_MOBILE ("
            "DOS_ID, DOS_DATE, DOS_STATUT, "
            "TYDO_ID, OGD_ID, "
            "DOS_CREE_PAR, DOS_DATE_CREATION, DOS_IMPUTATION, "
            "LOC_CODE, DOS_PERSO_NOM, DOS_PERSO_PRENOM, DOS_CERTIF_IND, "
            "DOS_TYP_SAISIE, OPV_CODE) VALUES ("
            ":dos_id, :dos_date, :dos_statut, "
            ":tydo_id, :ogd_id, "
            ":dos_cree_par, :dos_date_creation, :dos_imputation, "
            ":loc_code, :dos_perso_nom, :dos_perso_prenom, :dos_certif_ind, "
            ":dos_type_saisie, :opv_code)")

    now = datetime.datetime.now()
    today = datetime.datetime(*now.timetuple()[:3])

    dos_id = request_dos_id(conn)

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
        'dos_perso_nom': mx(nname(last_name), 60),
        'dos_perso_prenom': mx(nname(first_name), 60),
        'dos_type_saisie': "N",
        'opv_code': 1,
    }

    cursor = conn.cursor()
    try:
        cursor.execute(stmt, payload)
    except:
        raise
    finally:
        cursor.close()

    return dos_id
