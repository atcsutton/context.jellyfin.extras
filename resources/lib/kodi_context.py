# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import xbmc


def get_label(name):
    return xbmc.getInfoLabel(name) or ""


def get_movie_context():
    dbtype = get_label("ListItem.DBTYPE")
    imdb = get_label("ListItem.IMDBNumber")
    title = get_label("ListItem.Title")
    year = get_label("ListItem.Year")
    return dbtype, imdb, title, year
