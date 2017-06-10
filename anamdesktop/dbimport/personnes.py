#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime

import cx_Oracle

from anamdesktop.dbimport import mx, cl, to_date, ANAMDB_USER_ID
from anamdesktop.locations import (get_asserted_commune_id,
                                   get_cercle_id, get_region_id)


def create_hh_member(conn, dos_id, member_data, target, ind_id=None):
    ''' insert an IM_PERSONNES_mobile into ANAM DB '''
    stmt = ("INSERT INTO ANAM.IM_PERSONNES_mobile ("
            "OGD_ID, DOS_ID,"
            "PERSO_CIVILITE, PERSO_NOM, PERSO_PRENOM, PERSO_SEXE, "
            "PERSO_DATE_NAISSANCE, PERSO_LOCALITE_NAISSANCE, "
            "PERSO_SIT_MAT, PERSO_NATIONALITE, PERSO_PAYS_NAISSANCE, "
            "PERSO_NOM_PERE, PERSO_NOM_MERE, PERSO_RELATION, "
            "PERSO_TYPE_PERSO, "
            "PERSO_ADR_REGION_DISTRICT, PERSO_ADR_LOCALITE, "
            "PERSO_ADR_QUARTIER, PERSO_ADR_TEL, PERSO_NINA, "
            "PERSO_ETAT_VALIDATION, "
            "PERSO_PRENOM_PERE, PERSO_PRENOM_MERE, "
            "PERSO_SAISIE_PAR, PERSO_SAISIE_DATE, "
            "PERSO_PERSO_ID, PERSO_ETAT_IMMATRICULATION "
            ") VALUES ("
            ":ogd_id, :dos_id,"
            ":perso_civilite, :perso_nom, :perso_prenom, :perso_sexe, "
            ":perso_date_naissance, :perso_localite_naissance, "
            ":perso_sit_mat, :perso_nationalite, :perso_pays_naissance, "
            ":perso_nom_pere, :perso_nom_mere, :perso_relation, "
            ":perso_type_perso, "
            ":perso_adr_region_district, :perso_adr_localite, "
            ":perso_adr_quartier, :perso_adr_tel, :perso_nina, "
            ":perso_etat_validation, "
            ":perso_prenom_pere, :perso_prenom_mere, "
            ":perso_saisie_par, :perso_saisie_date, "
            ":perso_perso_id, :perso_etat_immatriculation) "
            "returning PERSO_ID into :perso_id")

    now = datetime.datetime.now()
    type_perso = "IND" if member_data['relation'] != 'A' else ""
    pays_naissance = "MLI" if member_data['loc_naissance'] != '0' else "000"
    nationalite = "MALIENNE" if pays_naissance == "MLI" else "INCONNUE"

    payload = {
        'ogd_id': 40,
        'dos_id': dos_id,
        'perso_civilite': member_data['civilite'],
        'perso_nom': mx(member_data['nom'], 35),
        'perso_prenom': mx(member_data['prenom'], 60),
        'perso_sexe': member_data['sexe'],
        'perso_date_naissance': member_data['ddn'],
        'perso_localite_naissance': member_data['loc_naissance'],
        'perso_sit_mat': member_data['sit_mat'],
        'perso_nationalite': mx(nationalite, 15),
        'perso_pays_naissance': mx(pays_naissance, 3),
        'perso_nom_pere': mx(member_data['nom_pere'], 30),
        'perso_nom_mere': mx(member_data['nom_mere'], 30),
        'perso_relation': member_data['relation'],
        'perso_type_perso': type_perso,
        'perso_adr_region_district': member_data.get('district'),
        'perso_adr_localite': member_data.get('commune'),
        'perso_adr_quartier': mx(member_data.get('quartier'), 30),
        'perso_adr_tel': mx(member_data.get('tel'), 12),
        'perso_nina': mx(member_data.get('nina'), 15),
        'perso_etat_validation': "N",
        'perso_prenom_pere': mx(member_data['prenom_pere'], 30),
        'perso_prenom_mere': mx(member_data['prenom_mere'], 30),
        'perso_saisie_par': mx(ANAMDB_USER_ID, 30),
        'perso_saisie_date': now,
        'perso_perso_id': ind_id,
        'perso_etat_immatriculation': "N",
    }

    cursor = conn.cursor()
    perso_id = None
    perso_id_var = cursor.var(cx_Oracle.NUMBER)
    payload.update({'perso_id': perso_id_var})
    try:
        cursor.execute(stmt, payload)
        perso_id = int(perso_id_var.getvalue())
    except:
        raise
    finally:
        cursor.close()

    return perso_id


def get_situtation_matrimoniale(data):
    ''' converts situtation_matrimoniale from xform to ANAM DB '''
    return {
        'celibataire': "C",
        'divorce': "D",
        'marie': "M",
        'veuf': "V"}.get(data, "A")


def get_sexe(data):
    ''' converts sexe from xform to ANAM DB '''
    return {
        'masculin': "M",
        'feminin': "F",
    }.get(data, "M")


def get_civilite(sexe, is_child=False):
    ''' converts civilite from xform to ANAM DB '''
    if sexe == 'M':
        return "M"
    else:
        return "MLLE" if is_child else "MME"


def get_ddn(tddn, ddn, an):
    ''' datetime from xform data based on supplied dob or yob '''
    return to_date(ddn) if tddn == "ddn" else datetime.date(int(an), 1, 1)


def get_lieu_naissance(data, prefix):
    ''' converts xfrom lieu_naissance to ANAMDB location ID '''
    naiss_region_slug = data.get("{}region".format(prefix))
    naiss_region_id = get_region_id(naiss_region_slug)
    naiss_cercle_slug = data.get("{}cercle".format(prefix))
    naiss_cercle_id = get_cercle_id(naiss_cercle_slug)
    naiss_commune_slug = data.get("{}commune".format(prefix))
    try:
        naiss_commune_id = get_asserted_commune_id(
            naiss_commune_slug, naiss_cercle_slug)
    except:
        naiss_commune_id = None

    naissance_location = None
    if naiss_commune_id:
        naissance_location = naiss_commune_id
    elif naiss_cercle_id:
        naissance_location = naiss_cercle_id
    elif naiss_region_id:
        naissance_location = naiss_region_id

    return naissance_location


def get_indigent_data(target):
    ''' preprare member_data for the indigent based on `target` '''
    sit_mat = get_situtation_matrimoniale(
        target.get("enquete/situation-matrimoniale"))
    sexe = get_sexe(target.get("enquete/sexe"))

    ddn = get_ddn(target.get("enquete/type-naissance"),
                  target.get("enquete/ddn"),
                  target.get("enquete/annee-naissance"))

    lieu_naissance = get_lieu_naissance(target, "enquete/")

    # survey location
    addr_region_slug = target.get("localisation-enquete/lieu_region")
    addr_region_id = get_region_id(addr_region_slug)
    addr_cercle_slug = target.get("localisation-enquete/lieu_cercle")
    addr_cercle_id = get_cercle_id(addr_cercle_slug)
    addr_commune_slug = target.get("localisation-enquete/lieu_commune")
    try:
        addr_commune_id = get_asserted_commune_id(
            addr_commune_slug, addr_cercle_slug)
    except:
        addr_commune_id = None

    if addr_cercle_id:
        district = addr_cercle_id
    else:
        district = addr_region_id

    tel = None
    for d in target.get("enquete/telephones", []):
        _tel = d.get("enquete/telephones/numero")
        if _tel:
            tel = _tel
        break

    return {
        'sexe': sexe,
        'civilite': get_civilite(sexe, False),
        'nom': cl(target.get("enquete/nom")),
        'prenom': cl(target.get("enquete/prenoms")),
        'ddn': ddn,
        'loc_naissance': lieu_naissance,
        'sit_mat': sit_mat,
        'nom_pere': cl(target.get("enquete/filiation/nom-pere")),
        'prenom_pere': cl(target.get("enquete/filiation/prenoms-pere")),
        'nom_mere': cl(target.get("enquete/filiation/nom-mere")),
        'prenom_mere': cl(target.get("enquete/filiation/prenoms-mere")),
        'relation': "A",

        'district': district,
        'commune': addr_commune_id,
        'quartier': cl(target.get("enquete/adresse")),
        'tel': tel,
        'nina': cl(target.get("nina"))}


def get_spouse_data(ind_id, target, index):
    ''' preprare member_data for the specified spouse based on `target` '''

    spouse = target.get("epouses", [])[index]

    lieu_naissance = get_lieu_naissance(spouse, "epouses/e_")
    ind_sexe = get_sexe(target.get("enquete/sexe"))
    sexe = "M" if ind_sexe == "F" else "F"

    ddn = get_ddn(spouse.get("epouses/e_type-naissance"),
                  spouse.get("epouses/e_ddn"),
                  spouse.get("epouses/e_annee-naissance"))

    return {
        'ind_id': ind_id,

        'sexe': sexe,
        'civilite': get_civilite(sexe, False),
        'nom': cl(spouse.get("epouses/e_nom")),
        'prenom': cl(spouse.get("epouses/e_prenoms")),
        'ddn': ddn,
        'loc_naissance': lieu_naissance,
        'sit_mat': "M",
        'nom_pere': cl(spouse.get("epouses/e_p_nom")),
        'prenom_pere': cl(spouse.get("epouses/e_p_prenoms")),
        'nom_mere': cl(spouse.get("epouses/e_m_nom")),
        'prenom_mere': cl(spouse.get("epouses/e_m_prenoms")),
        'relation': "M",
    }


def get_child_data(ind_id, target, index):
    ''' preprare member_data for the specified child based on `target` '''

    child = target.get("enfants", [])[index]
    lieu_naissance = get_lieu_naissance(child, "enfants/enfant_")
    ind_sexe = get_sexe(target.get("enquete/sexe"))
    sexe = get_sexe(child.get("enfants/enfant_sexe"))

    ddn = get_ddn(child.get("enfants/enfant_type-naissance"),
                  child.get("enfants/enfant_ddn"),
                  child.get("enfants/enfant_annee-naissance"))

    ind_noms = [cl(target.get("enquete/nom")),
                cl(target.get("enquete/prenoms"))]
    autre_noms = [cl(child.get("enfants/nom-autre-parent")),
                  cl(child.get("enfants/prenoms-autre-parent"))]

    if ind_sexe == "M":
        pere_noms = ind_noms
        mere_noms = autre_noms
    else:
        pere_noms = autre_noms
        mere_noms = ind_noms

    return {
        'ind_id': ind_id,

        'sexe': sexe,
        'civilite': get_civilite(sexe, True),
        'nom': cl(child.get("enfants/enfant_nom")),
        'prenom': cl(child.get("enfants/enfant_prenoms")),
        'ddn': ddn,
        'loc_naissance': lieu_naissance,
        'sit_mat': "",
        'nom_pere': pere_noms[0],
        'prenom_pere': pere_noms[1],
        'nom_mere': mere_noms[0],
        'prenom_mere': mere_noms[1],
        'relation': "E",
    }
