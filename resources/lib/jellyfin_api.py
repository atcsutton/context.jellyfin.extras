# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import ssl
import urllib.parse
import urllib.request

from resources.lib import utils

JF_TIMEOUT = 10


def http_get(path, params=None):
    """
    GET Jellyfin API with X-Emby-Token.
    Returns decoded JSON dict/list.
    """
    base = utils.get_setting("server_url").strip().rstrip("/")
    api_key = utils.get_setting("api_key").strip()
    if not base:
        raise ValueError("Missing Jellyfin server URL setting.")
    if not api_key:
        raise ValueError("Missing Jellyfin API key setting.")

    url = base + path
    if params:
        qs = urllib.parse.urlencode(params)
        url = url + ("&" if "?" in url else "?") + qs

    headers = {
        "Accept": "application/json",
        "X-Emby-Token": api_key,
    }

    req = urllib.request.Request(url, headers=headers, method="GET")

    ctx = None
    if url.lower().startswith("https") and not utils.get_setting_bool("verify_https", True):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, timeout=JF_TIMEOUT, context=ctx) as resp:
        raw = resp.read()
        if not raw:
            return None
        return json.loads(raw.decode("utf-8"))


def find_item_id_from_imdb(imdb_tt):
    """
    Resolve Jellyfin ItemId from IMDb id using /Search/Hints.
    """
    imdb_tt = (imdb_tt or "").strip()
    if not imdb_tt:
        return None

    try:
        params = {
            "SearchTerm": imdb_tt,  # ex: tt1877830
            "IncludeItemTypes": "Movie",
            "Remote": "false",
            "Limit": "10",
        }
        user_id = utils.get_setting("user_id").strip()
        if user_id:
            params["UserId"] = user_id

        data = http_get("/Search/Hints", params=params) or {}

        items = data.get("SearchHints", []) if isinstance(data, dict) else []
        if not items:
            return None

        if len(items) == 1:
            return items[0].get("Id")

        from resources.lib import ui
        chosen = ui.pick_from_list("Choisir le film Jellyfin", items, "Name")
        return chosen.get("Id") if chosen else None

    except Exception as exc:
        utils.log("IMDb resolve via Search/Hints failed: {}".format(exc))
        return None


def get_extras(item_id, user_id):
    """
    Get extras/bonus for a Jellyfin item.
    """
    if not item_id or not user_id:
        return []

    data = http_get("/Users/{}/Items/{}/Extras".format(user_id, item_id))
    if isinstance(data, list):
        return data
    return []
