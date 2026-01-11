# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import urllib.parse

import xbmc
import xbmcgui

from resources.lib import jellyfin_api
from resources.lib import kodi_context
from resources.lib import ui
from resources.lib import utils


def open_settings():
    xbmc.executebuiltin("Addon.OpenSettings(context.jellyfin.extras)")


def ensure_server_url():
    server_url = utils.get_auto_server_url()
    if server_url:
        return server_url

    server_url = utils.get_jellyfin_plugin_server_url()
    if server_url:
        utils.set_auto_server_url(server_url)
        return server_url

    server_url = ui.input_text(utils.ls(32024))
    if server_url:
        utils.set_auto_server_url(server_url.strip())
        return server_url.strip()

    return ""


def run_quick_connect():
    utils.log("Quick Connect: settings action triggered")
    utils.log("Quick Connect: start")
    xbmcgui.Dialog().notification(utils.ls(32001), utils.ls(32035), xbmcgui.NOTIFICATION_INFO, 3000)
    progress = None
    try:
        server_url = ensure_server_url()
        if not server_url:
            return

        # Sauvegarder immédiatement l'URL pour les appels API
        utils.set_auto_server_url(server_url)

        utils.log("Quick Connect server_url: {}".format(server_url))
        enabled = jellyfin_api.is_quick_connect_enabled(base_url=server_url)
        if enabled is False:
            ui.show_ok(utils.ls(32001), utils.ls(32002), utils.ls(32003))
            ui.show_ok(utils.ls(32001), utils.ls(32004), utils.ls(32005))
            return

        init = jellyfin_api.quick_connect_initiate(base_url=server_url) or {}
        code = init.get("Code")
        secret = init.get("Secret")
        utils.log(
            "Quick Connect initiate keys: Code={} Secret={}".format(
                bool(code), bool(secret)
            )
        )
        if not code or not secret:
            ui.show_ok(utils.ls(32001), utils.ls(32007))
            return

        link = server_url.rstrip("/") + "/web/"
        ui.show_ok(
            utils.ls(32001),
            "{}\n{}".format(
                utils.ls(32036).format(code),
                utils.ls(32037).format(link),
            ),
        )

        progress = xbmcgui.DialogProgress()
        progress.create(utils.ls(32001), utils.ls(32009))
        max_attempts = 30
        last_state = None
        for attempt in range(max_attempts):
            if progress.iscanceled():
                return

            data = jellyfin_api.quick_connect_poll(secret, base_url=server_url) or {}
            token = data.get("AccessToken") or data.get("Token") or data.get("access_token")
            user_id = data.get("UserId") or data.get("user_id")
            authenticated = data.get("Authenticated")
            auth_flag = bool(authenticated)
            state = "authenticated={}".format(auth_flag)
            if state != last_state:
                utils.log("Quick Connect poll state: {}".format(state))
                last_state = state

            if auth_flag:
                auth_data = jellyfin_api.authenticate_with_quick_connect(secret, base_url=server_url) or {}
                access_token = auth_data.get("AccessToken") or auth_data.get("accessToken")
                user = auth_data.get("User") or auth_data.get("user") or {}
                auth_user_id = auth_data.get("UserId") or auth_data.get("user_id")
                if not auth_user_id and isinstance(user, dict):
                    auth_user_id = user.get("Id") or user.get("id")

                token_preview = ""
                if access_token:
                    token_preview = "{}...".format(access_token[:6])

                utils.log(
                    "Quick Connect auth result: token_present={} token_preview={} user_id_present={}".format(
                        bool(access_token), token_preview, bool(auth_user_id)
                    )
                )

                if access_token and auth_user_id:
                    utils.set_setting("access_token", access_token)
                    utils.set_auto_user_id(auth_user_id)
                    utils.set_setting("linked", "true")
                    ui.show_ok(utils.ls(32001), utils.ls(32010))
                    return

                ui.show_ok(utils.ls(32001), utils.ls(32043), utils.ls(32044))
                return

            progress.update(int(((attempt + 1) / float(max_attempts)) * 100))
            xbmc.sleep(2000)

        ui.show_ok(utils.ls(32001), utils.ls(32012), utils.ls(32013))
    except Exception as exc:
        utils.log("Quick Connect exception: {}".format(exc))
        ui.show_ok(utils.ls(32001), utils.ls(32038), str(exc))
    finally:
        if progress:
            progress.close()
        utils.log("Quick Connect finished")


def _has_quick_connect_arg():
    for arg in sys.argv[1:]:
        if arg == "quick_connect":
            return True
        if "quick_connect" in arg and "action=" in arg:
            return True
        if arg.startswith("?") and "quick_connect" in arg:
            return True
    return False


def main():
    if _has_quick_connect_arg():
        run_quick_connect()
        return

    dbtype, imdb, title, year = kodi_context.get_movie_context()
    utils.log_debug("DBTYPE={} IMDB={} TITLE={} YEAR={}".format(dbtype, imdb, title, year))

    if dbtype.lower() != "movie":
        ui.show_ok(utils.ls(32000), utils.ls(32014))
        return

    user_id = utils.get_user_id()
    if not user_id:
        if ui.show_yesno(
            utils.ls(32000),
            utils.ls(32015),
            utils.ls(32016),
        ):
            open_settings()
        return

    if not imdb:
        ui.show_ok(utils.ls(32000), utils.ls(32017), utils.ls(32018))
        return

    item_id = jellyfin_api.find_item_id_from_imdb(imdb, title=title, year=year)
    if not item_id:
        ui.show_ok(utils.ls(32000), utils.ls(32019))
        return

    extras = jellyfin_api.get_extras(item_id, user_id)
    if not extras:
        ui.show_ok(utils.ls(32000), utils.ls(32020))
        return

    chosen = ui.pick_from_list(utils.ls(32032), extras, "Name")
    if not chosen:
        return

    extra_id = chosen.get("Id")
    if not extra_id:
        ui.show_ok(utils.ls(32000), utils.ls(32021))
        return

    if not xbmc.getCondVisibility("System.HasAddon(plugin.video.jellyfin)"):
        ui.show_ok(utils.ls(32000), utils.ls(32022))
        return

    url = "plugin://plugin.video.jellyfin/?mode=play&id={}".format(
        urllib.parse.quote(extra_id)
    )
    xbmc.executebuiltin('PlayMedia("{}")'.format(url))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        utils.log("ERROR: {}".format(exc))
        ui.show_ok(utils.ls(32000), utils.ls(32023), str(exc))
