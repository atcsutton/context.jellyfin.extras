# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import xbmcgui

from resources.lib import utils


def _join_lines(lines):
    return "\n".join([line for line in lines if line])


def show_ok(title, *lines):
    message = _join_lines(lines)
    xbmcgui.Dialog().ok(title, message)


def show_yesno(title, *lines):
    message = _join_lines(lines)
    return xbmcgui.Dialog().yesno(title, message)


def show_text(title, text):
    xbmcgui.Dialog().textviewer(title, text)


def input_text(title, default=""):
    return xbmcgui.Dialog().input(title, default)


def _format_duration(ticks):
    """Convertit les RunTimeTicks Jellyfin en format lisible (ex: 1h 23min)"""
    if not ticks:
        return ""
    seconds = ticks // 10000000
    minutes = seconds // 60
    hours = minutes // 60
    minutes = minutes % 60
    
    if hours > 0:
        return "{}h {:02d}min".format(hours, minutes)
    elif minutes > 0:
        return "{}min".format(minutes)
    else:
        return "{}s".format(seconds)


def _get_thumbnail_url(item_id):
    """Construit l'URL de la miniature pour un item Jellyfin"""
    server_url = utils.get_server_url()
    if not server_url or not item_id:
        return ""
    return "{}/Items/{}/Images/Primary?maxWidth=400".format(
        server_url.rstrip("/"), item_id
    )


def pick_from_list(title, items, label_key="Name"):
    if not items:
        return None

    list_items = []
    for it in items:
        name = it.get(label_key, "")
        item_id = it.get("Id", "")
        
        # Durée au lieu de l'année
        duration = _format_duration(it.get("RunTimeTicks"))
        
        # Créer un ListItem avec miniature
        li = xbmcgui.ListItem(name, label2=duration)
        
        # Ajouter la miniature
        thumb_url = _get_thumbnail_url(item_id)
        if thumb_url:
            li.setArt({"thumb": thumb_url, "icon": thumb_url})
        
        list_items.append(li)

    # useDetails=True permet d'afficher les miniatures et label2
    idx = xbmcgui.Dialog().select(title, list_items, useDetails=True)
    if idx < 0:
        return None
    return items[idx]
