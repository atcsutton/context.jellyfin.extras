# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import re
import ssl
import urllib.parse
import urllib.request
import urllib.error

from resources.lib import utils

JF_TIMEOUT = 10


def get_emby_auth_header():
    return (
        'MediaBrowser '
        'Client="Kodi", '
        'Device="Android", '
        'DeviceId="{}", '
        'Version="{}"'
    ).format(utils.get_device_id(), utils.get_addon_version())


def _log_http_response(method, url, status, body):
    preview = body[:500] if body else ""
    utils.log("HTTP {} {} -> {} body={}".format(method, url, status, preview))


def http_get(path, params=None, require_auth=True, base_url=None):
    """
    GET Jellyfin API with X-Emby-Token.
    Returns decoded JSON dict/list.
    """
    base = (base_url or utils.get_server_url() or "").strip().rstrip("/")
    if not base:
        raise ValueError("Missing Jellyfin server URL setting.")

    url = base + path
    if params:
        qs = urllib.parse.urlencode(params)
        url = url + ("&" if "?" in url else "?") + qs

    headers = {
        "Accept": "application/json",
        "X-Emby-Authorization": get_emby_auth_header(),
    }
    if require_auth:
        token = utils.get_auth_token()
        if not token:
            raise ValueError("Missing Jellyfin API key or access token setting.")
        headers["X-Emby-Token"] = token

    req = urllib.request.Request(url, headers=headers, method="GET")

    ctx = None
    if url.lower().startswith("https") and not utils.get_setting_bool("verify_https", True):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=JF_TIMEOUT, context=ctx) as resp:
            raw = resp.read()
            text = raw.decode("utf-8", "ignore") if raw else ""
            _log_http_response("GET", url, resp.getcode(), text)
            if not raw:
                return None
            return json.loads(text)
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", "ignore")
        except Exception:
            body = ""
        _log_http_response("GET", url, exc.code, body)
        raise


def http_post(path, body=None, params=None, require_auth=True, headers=None, base_url=None):
    """
    POST Jellyfin API with optional X-Emby-Token.
    Returns decoded JSON dict/list.
    """
    base = (base_url or utils.get_server_url() or "").strip().rstrip("/")
    if not base:
        raise ValueError("Missing Jellyfin server URL setting.")

    url = base + path
    if params:
        qs = urllib.parse.urlencode(params)
        url = url + ("&" if "?" in url else "?") + qs

    if headers is None:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Emby-Authorization": get_emby_auth_header(),
        }
    if require_auth:
        token = utils.get_auth_token()
        if not token:
            raise ValueError("Missing Jellyfin API key or access token setting.")
        headers["X-Emby-Token"] = token

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    ctx = None
    if url.lower().startswith("https") and not utils.get_setting_bool("verify_https", True):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=JF_TIMEOUT, context=ctx) as resp:
            raw = resp.read()
            text = raw.decode("utf-8", "ignore") if raw else ""
            _log_http_response("POST", url, resp.getcode(), text)
            if not raw:
                return None
            return json.loads(text)
    except urllib.error.HTTPError as exc:
        body_text = ""
        try:
            body_text = exc.read().decode("utf-8", "ignore")
        except Exception:
            body_text = ""
        _log_http_response("POST", url, exc.code, body_text)
        raise


def _normalize_name(value):
    value = value or ""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _log_candidates(prefix, items):
    utils.log("{} {}".format(prefix, len(items)))
    for idx, item in enumerate(items[:5]):
        name = item.get("Name") or ""
        year = item.get("ProductionYear")
        provider_ids = item.get("ProviderIds") or {}
        imdb_id = provider_ids.get("Imdb") or provider_ids.get("imdb") or ""
        utils.log("cand: Name={} Year={} imdb={}".format(name, year, imdb_id))


def _pick_best_match(items, imdb_tt, year=None, title=None):
    imdb_tt = (imdb_tt or "").strip().lower()
    year_int = None
    if year:
        try:
            year_int = int(year)
        except Exception:
            year_int = None

    matches = []
    for item in items:
        provider_ids = item.get("ProviderIds") or {}
        imdb_id = provider_ids.get("Imdb") or provider_ids.get("imdb") or ""
        if imdb_id.strip().lower() == imdb_tt:
            matches.append(item)

    if matches:
        if year_int:
            exact = [it for it in matches if it.get("ProductionYear") == year_int]
            if exact:
                return exact[0]
        return matches[0]

    if title:
        norm_title = _normalize_name(title)
        if norm_title:
            by_name = [it for it in items if _normalize_name(it.get("Name")) == norm_title]
            if by_name:
                if year_int:
                    exact = [it for it in by_name if it.get("ProductionYear") == year_int]
                    if exact:
                        return exact[0]
                return by_name[0]

    return None


def find_item_id_from_imdb(imdb_tt, title=None, year=None):
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
            "Limit": "10",
        }
        user_id = utils.get_user_id()
        if user_id:
            params["UserId"] = user_id

        data = http_get("/Search/Hints", params=params) or {}

        items = data.get("SearchHints", []) if isinstance(data, dict) else []
        utils.log("Search/Hints count: {}".format(len(items)))
        if not items:
            if user_id:
                fallback_path = "/Users/{}/Items".format(user_id)
                fallback_params = {
                    "IncludeItemTypes": "Movie",
                    "Recursive": "true",
                    "Limit": "10",
                    "AnyProviderIdEquals": "imdb.{}".format(imdb_tt),
                    "Fields": "ProviderIds",
                }

                fallback = http_get(fallback_path, params=fallback_params) or {}
                fallback_items = fallback.get("Items", []) if isinstance(fallback, dict) else []
                _log_candidates("Items fallback candidates:", fallback_items)

                picked = _pick_best_match(fallback_items, imdb_tt, year=year, title=title)
                if picked:
                    item_id = picked.get("Id")
                    utils.log(
                        "Items fallback selected: {} ({})".format(item_id, picked.get("Name"))
                    )
                    return item_id

            if title:
                title_params = {
                    "SearchTerm": title,
                    "IncludeItemTypes": "Movie",
                    "Limit": "10",
                }
                if user_id:
                    title_params["UserId"] = user_id

                title_data = http_get("/Search/Hints", params=title_params) or {}
                title_items = title_data.get("SearchHints", []) if isinstance(title_data, dict) else []
                _log_candidates("Title fallback candidates:", title_items)

                picked = _pick_best_match(title_items, imdb_tt, year=year, title=title)
                if picked:
                    item_id = picked.get("Id")
                    utils.log(
                        "Items fallback selected: {} ({})".format(item_id, picked.get("Name"))
                    )
                    return item_id

            return None

        if len(items) == 1:
            return items[0].get("Id")

        from resources.lib import ui
        chosen = ui.pick_from_list(utils.ls(32034), items, "Name")
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

    path = "/Users/{}/Items/{}/Extras".format(user_id, item_id)
    utils.log("Fetch extras via {}".format(path))
    try:
        data = http_get(path)
        if isinstance(data, list):
            return data
        return []
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise

    utils.log("Extras endpoint 404, trying SpecialFeatures")

    path = "/Items/{}/SpecialFeatures".format(item_id)
    try:
        data = http_get(path)
        utils.log("SpecialFeatures status 200")
        if isinstance(data, list):
            return data
    except urllib.error.HTTPError as exc:
        utils.log("SpecialFeatures status {}".format(exc.code))
        if exc.code != 404:
            raise

    path = "/Users/{}/Items/{}/SpecialFeatures".format(user_id, item_id)
    try:
        data = http_get(path)
        utils.log("SpecialFeatures status 200")
        if isinstance(data, list):
            return data
    except urllib.error.HTTPError as exc:
        utils.log("SpecialFeatures status {}".format(exc.code))
        if exc.code != 404:
            raise

    path = "/Users/{}/Items/{}/Children".format(user_id, item_id)
    params = {
        "Recursive": "true",
        "Fields": "Path,ExtraType,ProviderIds",
    }
    try:
        data = http_get(path, params=params) or {}
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        return []

    items = data.get("Items", []) if isinstance(data, dict) else []
    utils.log("Children candidates {}".format(len(items)))

    extras = []
    keywords = ("extras", "bonus", "featurette", "making", "deleted", "interview", "trailer")
    for item in items:
        extra_type = item.get("ExtraType")
        if extra_type:
            extras.append(item)
            continue

        name = (item.get("Name") or "").lower()
        path_value = (item.get("Path") or "").lower()
        if any(k in name for k in keywords) or any(k in path_value for k in keywords):
            extras.append(item)

    utils.log("Children extras detected {}".format(len(extras)))
    return extras


def is_quick_connect_enabled(base_url=None):
    try:
        data = http_get("/QuickConnect/Enabled", require_auth=False, base_url=base_url)
    except Exception:
        return None

    if isinstance(data, bool):
        return data
    if isinstance(data, dict):
        return data.get("Enabled")
    return None


def quick_connect_initiate(base_url=None):
    headers = {
        "Accept": "application/json",
        "Content-Length": "0",
        "X-Emby-Authorization": get_emby_auth_header(),
    }
    try:
        return http_post("/QuickConnect/Initiate", body=None, require_auth=False, headers=headers, base_url=base_url)
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", "ignore")
        except Exception:
            body = ""
        utils.log(
            "Quick Connect initiate failed: url={} status={} body={}".format(
                exc.url, exc.code, body
            )
        )
        raise


def quick_connect_poll(secret, base_url=None):
    return http_get("/QuickConnect/Connect", params={"secret": secret}, require_auth=False, base_url=base_url)


def authenticate_with_quick_connect(secret, base_url=None):
    attempts = [
        ("body Secret", {"Secret": secret}, None),
        ("body secret", {"secret": secret}, None),
        ("query secret", None, {"secret": secret}),
    ]

    for label, body, params in attempts:
        utils.log("Quick Connect auth attempt: {}".format(label))
        try:
            data = http_post(
                "/Users/AuthenticateWithQuickConnect",
                body=body,
                params=params,
                require_auth=False,
                base_url=base_url,
            )
            return data
        except urllib.error.HTTPError as exc:
            utils.log(
                "Quick Connect auth failed: {} status={}".format(label, exc.code)
            )
            continue
        except Exception as exc:
            utils.log("Quick Connect auth error: {} {}".format(label, exc))
            continue

    return None
