#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime

from anamdesktop.dbimport import mx, to_date


def create_attachment(conn, dos_id, perso_id, pj_data, member, member_type):
    ''' insert an IM_PERSO_PJ_mobile into ANAM DB '''

    stmt = ("INSERT INTO ANAM.IM_PERSO_PJ_mobile ("
            "PERSO_ID, PJ_ID, PPJ_DATE_DEB, DOS_ID, "
            "PPJ_NUM_PIECE, PPJ_DELIVRE_PAR, "
            "PPJ_VALIDITE, PPJ_DATE_FIN) VALUES ("
            ":perso_id, :pj_id, :ppj_date_deb, :dos_id, "
            ":ppj_num_piece, :ppj_delivree_par, "
            ":ppj_validite, :ppj_date_fin)")

    # retrieve PJ_ID from pj_data
    pj_id = {
        'acte-naissance': 'EXTNAIS',
        'acte-mariage': 'EXTMARI',
        'certificat-frequentation': 'CERTSCO',
        'certificat-medical': 'CERTMED',
        'certificat-indigence': 'CERTIND',
    }.get(pj_data.get("labels", {}).get("slug"))

    # exit silently if requested data is not supported
    if not pj_id:
        return

    ppj_date_deb = None
    ppj_num_piece = None
    ppj_delivree_par = None
    ppj_date_fin = None

    if member_type == 'indigent':
        if pj_id == 'EXTNAIS':
            ppj_num_piece = member.get(
                "acte-naissance/numero_acte_naissance")
            ppj_delivree_par = member.get(
                "acte-naissance/centre_acte_naissance")

        elif pj_id == 'CERTIND':
            # we only retrieve a picture of this
            pass

    elif member_type == 'spouse':
        if pj_id == 'EXTNAIS':
            ppj_num_piece = member.get(
                "epouses/e_acte-naissance/e_numero_n")
            ppj_delivree_par = member.get(
                "epouses/e_acte-naissance/e_centre_n")

        elif pj_id == 'EXTMARI':
            ppj_num_piece = member.get("epouses/e_acte-mariage/e_numero_m")
            ppj_delivree_par = member.get("epouses/e_acte-mariage/e_centre_m")

    elif member_type == 'child':
        if pj_id == 'EXTNAIS':
            ppj_num_piece = member.get(
                "enfants/enfant_acte-naissance/enfant_numero_n")
            ppj_delivree_par = member.get(
                "enfants/enfant_acte-naissance/enfant_centre_n")

        elif pj_id == 'CERTSCO':
            ppj_date_deb = to_date(member.get(
                "enfants/situation/"
                "enfant_certificat-frequentation/enfant_date_f"))
            ppj_delivree_par = member.get(
                "enfants/situation/"
                "enfant_certificat-frequentation/enfant_centre_f")

        elif pj_id == 'CERTMED':
            ppj_date_deb = to_date(member.get(
                "enfants/situation/enfant_certificat-medical/enfant_date_m"))
            ppj_delivree_par = member.get(
                "enfants/situation/enfant_certificat-medical/enfant_centre_m")

    # ppj_date_deb is mandatory although we miss it for most
    if not ppj_date_deb:
        ppj_date_deb = datetime.date.today()

    payload = {
        'perso_id': perso_id,
        'pj_id': pj_id,
        'ppj_date_deb': ppj_date_deb,
        'dos_id': dos_id,
        'ppj_num_piece': mx(ppj_num_piece, 20),
        'ppj_delivree_par': mx(ppj_delivree_par, 80),
        'ppj_validite': 12,
        'ppj_date_fin': ppj_date_fin,
    }

    cursor = conn.cursor()
    try:
        cursor.execute(stmt, payload)
    except:
        raise
    finally:
        cursor.close()


def get_attachments(target, member_type, index=None):
    ''' list of `hamed` attachment data for this person (type and index) '''
    attachments = target.get("_hamed_attachments")
    if member_type == 'indigent':
        return [attachment for key, attachment in attachments.items()
                if key not in ('epouses', 'enfants')]

    mkey = "epouses" if member_type == "spouse" else "enfants"
    return [attachment for key, attachment
            in attachments.get(mkey)[index].items()]
