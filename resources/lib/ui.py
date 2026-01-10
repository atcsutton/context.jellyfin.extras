# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import xbmcgui


def show_ok(title, line1, line2=""):
    if line2:
        xbmcgui.Dialog().ok(title, line1, line2)
    else:
        xbmcgui.Dialog().ok(title, line1)


def pick_from_list(title, items, label_key="Name"):
    if not items:
        return None

    labels = []
    for it in items:
        name = it.get(label_key, "")
        year = it.get("ProductionYear")
        if year:
            labels.append("{} ({})".format(name, year))
        else:
            labels.append(name)

    idx = xbmcgui.Dialog().select(title, labels)
    if idx < 0:
        return None
    return items[idx]
