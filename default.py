# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from resources.lib import jellyfin_api
from resources.lib import kodi_context
from resources.lib import ui
from resources.lib import utils


def main():
    dbtype, imdb, title, year = kodi_context.get_movie_context()
    utils.log_debug("DBTYPE={} IMDB={} TITLE={} YEAR={}".format(dbtype, imdb, title, year))

    if dbtype.lower() != "movie":
        ui.show_ok("Jellyfin Extras", "Action disponible uniquement sur les films.")
        return

    user_id = utils.get_setting("user_id").strip()
    if not user_id:
        ui.show_ok("Jellyfin Extras", "UserId Jellyfin manquant.", "Renseignez-le dans les parametres.")
        return

    if not imdb:
        ui.show_ok("Jellyfin Extras", "IMDb ID manquant dans Kodi.", "Impossible de resoudre le film.")
        return

    item_id = jellyfin_api.find_item_id_from_imdb(imdb)
    if not item_id:
        ui.show_ok("Jellyfin Extras", "Impossible d'identifier l'item Jellyfin.")
        return

    extras = jellyfin_api.get_extras(item_id, user_id)
    if not extras:
        ui.show_ok("Jellyfin Extras", "Aucun extra trouve pour cet element.")
        return

    ui.pick_from_list("Bonus / Extras", extras, "Name")


+if __name__ == "__main__":
+    try:
+        main()
+    except Exception as exc:
+        utils.log("ERROR: {}".format(exc))
+        ui.show_ok("Jellyfin Extras", "Erreur", str(exc))
