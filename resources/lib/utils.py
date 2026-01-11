# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import uuid

import xbmc
import xbmcaddon

LOG_PREFIX = "[JELLYFIN-EXTRAS] "

ADDON_ID = "context.jellyfin.extras"
try:
    ADDON = xbmcaddon.Addon(ADDON_ID)
except Exception:
    ADDON = xbmcaddon.Addon()


def ls(string_id):
    return ADDON.getLocalizedString(string_id)


def log(msg):
    xbmc.log(LOG_PREFIX + str(msg), xbmc.LOGINFO)


def log_debug(msg):
    if get_setting_bool("debug", False):
        log(msg)


def get_setting(name, default=""):
    value = ADDON.getSetting(name)
    return value if value != "" else default


def set_setting(name, value):
    ADDON.setSetting(name, value)


def get_setting_bool(name, default=False):
    try:
        return ADDON.getSettingBool(name)
    except AttributeError:
        value = ADDON.getSetting(name)
        if value == "":
            return default
        return value.strip().lower() in ("true", "1", "yes")

def get_auth_mode():
    value = get_setting("auth_mode", "0")
    return value.strip()


def get_auth_token():
    if get_auth_mode() == "1":
        # Mode manuel
        token = get_setting("manual_api_key").strip()
        if token:
            return token
        return get_setting("api_key").strip()

    # Mode Quick Connect
    token = get_setting("access_token").strip()
    if token:
        return token
    return get_setting("api_key").strip()


def get_server_url():
    if get_auth_mode() == "1":
        # Mode manuel
        value = get_setting("manual_server_url").strip()
        if value:
            return value
    return get_setting("server_url").strip()


def get_user_id():
    if get_auth_mode() == "1":
        # Mode manuel
        value = get_setting("manual_user_id").strip()
        if value:
            return value
    return get_setting("user_id").strip()


def get_api_key():
    if get_auth_mode() == "1":
        # Mode manuel
        value = get_setting("manual_api_key").strip()
        if value:
            return value
    return get_setting("api_key").strip()


def get_auto_server_url():
    return get_setting("server_url").strip()


def set_auto_server_url(value):
    set_setting("server_url", value)


def set_auto_user_id(value):
    set_setting("user_id", value)


def get_device_id():
    device_id = get_setting("device_id").strip()
    if device_id:
        return device_id

    device_id = str(uuid.uuid4())
    set_setting("device_id", device_id)
    return device_id


def get_addon_version():
    return ADDON.getAddonInfo("version")


def get_jellyfin_plugin_server_url():
    return get_jellyfin_plugin_setting(
        [
            "server_url",
            "server",
            "serveraddress",
            "server_address",
            "address",
            "host",
            "hostname",
            "base_url",
        ]
    )


def get_jellyfin_plugin_setting(keys):
    if not xbmc.getCondVisibility("System.HasAddon(plugin.video.jellyfin)"):
        return ""

    try:
        jellyfin_addon = xbmcaddon.Addon("plugin.video.jellyfin")
    except Exception:
        return ""

    for key in keys:
        value = jellyfin_addon.getSetting(key)
        if value:
            return value.strip()

    return ""
