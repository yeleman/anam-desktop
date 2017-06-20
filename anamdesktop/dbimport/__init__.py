#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime

from anamdesktop import logger
from anamdesktop.utils import to_ascii

ANAMDB_USER_ID = "HAMEDCOLLECT"
ANAMDB_DATE_FMT = "%m/%d/%Y %H:%M:%S"
ANAMDB_SHORTDATE_FMT = "%d%m%Y"


def mx(text, length):
    ''' return `text` truncated to `length` '''
    if len(str(text)) > length - 1:
        return str(text)[:length - 1]
    return text


def cl(s, ascii_only=False):
    ''' normalize input to a strip'd version '''
    if s is None:
        return None
    if ascii_only:
        return to_ascii(s.strip())
    return s.strip()


def to_date(data):
    ''' convert xform YYYY-MM-DD dates to datetime object '''
    try:
        return datetime.date(*[int(i) for i in data.split("-")])
    except:
        return None


def import_target(conn, target):
    ''' import target and all its dependents into ANAM DB

        returns a json/oracle mapping of identifiers '''

    from anamdesktop.dbimport.dossiers import create_dossier
    from anamdesktop.dbimport.personnes import (create_hh_member,
                                                get_indigent_data,
                                                get_spouse_data,
                                                get_child_data)
    from anamdesktop.dbimport.attachments import (create_attachment,
                                                  get_attachments)

    def import_attachments(mtype, member, index=None):
        ''' create all attachments for a specified person '''
        for ix, attachment in enumerate(get_attachments(target, mtype, index)):
            create_attachment(conn, dos_id, pid, attachment, member, mtype)
            logger.info("Created IM_PERSO_PJ_MOBILE {} for {}"
                        .format(ix, mtype))

    # retrieve identifier as we'll use it to bind with dossier_id
    ident = target.get('ident')
    assert ident

    # ensure target is indigent
    assert target.get('certificat-indigence')

    # create DOSSIER
    dos_id = create_dossier(conn, ident, target)

    logger.info("Created IM_DOSSIERS_MOBILE #{}".format(dos_id))

    # create indigent first
    pid = create_hh_member(conn, dos_id, get_indigent_data(target), target)
    logger.info("Created IM_PERSONNES_MOBILE (indigent) #{}".format(pid))

    # record perso_id
    ident_map = {'indigent': pid,
                 'dossier': dos_id}

    # import indigent's attachments
    import_attachments('indigent', target)

    # add spouses
    for index, spouse in enumerate(target.get("epouses", [])):
        pid = create_hh_member(
            conn, dos_id, get_spouse_data(pid, target, index),
            target, ind_id=pid)
        logger.info("Created IM_PERSONNES_MOBILE (spouse {}) #{}"
                    .format(index, pid))

        ident_map.update({'epouse{}'.format(index + 1): pid})
        import_attachments("spouse", spouse, index)

    # add children
    for index, child in enumerate(target.get("enfants", [])):
        pid = create_hh_member(
            conn, dos_id, get_child_data(pid, target, index),
            target, ind_id=pid)
        logger.info("Created IM_PERSONNES_MOBILE (child {}) #{}"
                    .format(index, pid))

        ident_map.update({'enfant{}'.format(index + 1): pid})
        import_attachments("child", child, index)

    return {ident: ident_map}
