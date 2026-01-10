# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import xbmc
import xbmcaddon

LOG_PREFIX = "[JELLYFIN-EXTRAS] "

ADDON = xbmcaddon.Addon()


def log(msg):
    xbmc.log(LOG_PREFIX + str(msg), xbmc.LOGINFO)


def log_debug(msg):
    if get_setting_bool("debug", False):
        log(msg)


def get_setting(name, default=""):
    value = ADDON.getSetting(name)
    return value if value != "" else default


def get_setting_bool(name, default=False):
    try:
        return ADDON.getSettingBool(name)
    except AttributeError:
        value = ADDON.getSetting(name)
        if value == "":
            return default
        return value.strip().lower() in ("true", "1", "yes")
