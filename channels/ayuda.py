# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# ayuda - Videos de ayuda y tutoriales para pelisalacarta
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
# contribuci?n de jurrabi
# ----------------------------------------------------------------------
import os
import xbmc

from channels import youtube_channel
from core import config
from core import logger
from core.item import Item
from platformcode import platformtools

CHANNELNAME = "ayuda"


def isGeneric():
    return True


def mainlist(item):
    logger.info("pelisalacarta.channels.ayuda mainlist")
    itemlist = []

    cuantos = 0

    if config.is_xbmc():
        itemlist.append(Item(channel=CHANNELNAME, action="updatebiblio",
                             title="Buscar nuevos episodios y actualizar biblioteca", folder=False))
        cuantos += cuantos

    itemlist.append(Item(channel=CHANNELNAME, action="", title="",
                         folder=False))

    if config.is_xbmc():
        # Al poner folder=False el log muestra: "WARNING: Attempt to use invalid handle -1"
        itemlist.append(Item(channel=CHANNELNAME,
                             action="force_creation_advancedsettings",
                             title="Crear fichero advancedsettings.xml optimizado", folder=True))
        cuantos += cuantos

    if config.is_xbmc():
        itemlist.append(Item(channel=CHANNELNAME,
                             action="recover_advancedsettings",
                             title="Restaurar advancedsettings.xml del backup", folder=False))
        cuantos += cuantos

    itemlist.append(Item(channel=CHANNELNAME, action="", title="",
                         folder=False))

    if cuantos > 0:
        itemlist.append(Item(channel=CHANNELNAME,
                             action="tutoriales", title="Ver guías y tutoriales en vídeo"))
    else:
        itemlist.extend(tutoriales(item))

    return itemlist


def tutoriales(item):
    playlists = youtube_channel.playlists(item, "tvalacarta")

    itemlist = []

    for playlist in playlists:
        if playlist.title == "Tutoriales de pelisalacarta":
            itemlist = youtube_channel.videos(playlist)

    return itemlist


def force_creation_advancedsettings(item):

    # Ruta del advancedsettings
    advancedsettings_kodi = xbmc.translatePath("special://userdata/advancedsettings.xml")
    advancedsettings_pelisalacarta = os.path.join(config.get_runtime_path(), "resources",
                                                  "advancedsettings.xml")
    fichero_backup = os.path.join(config.get_data_path(), "original_advancedsettings_backup.xml")

    # Archivos temporales para la modificacion de advancedsettings.xml:
    advancedsettings_same = os.path.join(config.get_data_path(), "same.txt")
    advancedsettings_trans = os.path.join(config.get_data_path(), "trans.txt")

    if os.path.exists(advancedsettings_kodi):
        logger.info("pelisalacarta.channels.ayuda La ruta de advanced settings del usuario existe!")

        if platformtools.dialog_yesno("pelisalacarta",
                                      "Esto modificara los ajustes avanzados de Kodi. ",
                                      "Deseas continuar?") == 1:

            # Backup del advancedsettings existente, antes de modificarlo.
            with open(advancedsettings_kodi) as f_origen:
                if not os.path.exists(fichero_backup):
                    with open(fichero_backup, "w") as f_backup:
                        for line in f_origen:
                            f_backup.write(line)
                else:
                    if platformtools.dialog_yesno("pelisalacarta",
                                                  "Backup anterior encontrado. ",
                                                  "Deseas sobreescribirlo?") == 1:
                        os.remove(fichero_backup)
                        with open(fichero_backup, "w") as f_backup:
                            for line in f_origen:
                                f_backup.write(line)
                        platformtools.dialog_notification("pelisalacarta",
                                                          "Backup terminado!")
                        logger.info("pelisalacarta.channels.ayuda Backup terminado!")
                    else:
                        platformtools.dialog_notification("pelisalacarta",
                                                          "Backup no modificado")
                        logger.info("pelisalacarta.channels.ayuda Backup no modificado!")

            # Edicion de advancedsettings.xml
            with open(os.path.join(advancedsettings_pelisalacarta)) as f_mod:
                with open(os.path.join(advancedsettings_trans), "w") as f_trans:
                    with open(os.path.join(advancedsettings_same), "w") as f_same:
                        lines_seen = set()
                        special_lines_seen = set()
                        for line_mod in f_mod:
                            with open(os.path.join(advancedsettings_kodi)) as f_orig:
                                if (line_mod.startswith(("<advancedsettings>",
                                                         "</network>",
                                                         "</advancedsettings>")) and line_mod
                                        not in special_lines_seen):
                                    f_same.write(line_mod)
                                    if not line_mod.startswith("</network>"):
                                        f_trans.write(line_mod)
                                    special_lines_seen.add(line_mod)

                                for line_orig in f_orig:
                                    if (line_orig.startswith(("<advancedsettings>",
                                                              "</advancedsettings>")) and line_orig
                                            not in special_lines_seen and line_orig not in
                                            lines_seen):
                                        lines_seen.add(line_orig)

                                    if (line_orig == line_mod and line_orig not in lines_seen and
                                            line_orig not in special_lines_seen):
                                        line_same = line_orig
                                        f_same.write(line_same)
                                        lines_seen.add(line_orig)

                                    if (not line_orig.startswith(("<autodetectpingtime>",
                                                                  "<curlclienttimeout>",
                                                                  "<curllowspeedtime>",
                                                                  "<curlretries>",
                                                                  "<disableipv6>",
                                                                  "<cachemembuffersize>")) and
                                            line_orig not in lines_seen and line_orig not in
                                            special_lines_seen):
                                        line_trans = line_orig
                                        if line_orig.startswith("<network>"):
                                            f_same.write(line_orig)
                                        f_trans.write(line_trans)
                                        lines_seen.add(line_orig)

            import filecmp
            if filecmp.cmp(advancedsettings_pelisalacarta, advancedsettings_same):
                platformtools.dialog_notification("pelisalacarta",
                                                  "advancessettings.xml estaba optimizado!")
            else:
                platformtools.dialog_notification("pelisalacarta",
                                                  "advancessettings.xml no estaba optimizado!")

            # Se vacia advancedsettings.xml
            open(os.path.join(advancedsettings_kodi)).close

            nospaces = False
            with open(os.path.join(advancedsettings_pelisalacarta)) as f_mod:
                if filecmp.cmp(advancedsettings_pelisalacarta, advancedsettings_same):
                    platformtools.dialog_ok("pelisalacarta",
                                            "advancessettings.xml estaba optimizado!",
                                            "(No sera editado)")
                else:
                    platformtools.dialog_notification("pelisalacarta",
                                                      "modificando advancedsettings.xml...")
                    with open(os.path.join(advancedsettings_trans)) as f_trans:
                        with open(os.path.join(advancedsettings_kodi), "w") as f_orig:
                            for line_trans in f_trans:
                                if line_trans.startswith("<network>"):
                                    for line_mod in f_mod:
                                        if not line_mod.startswith(("<advancedsettings>",
                                                                    "</network>",
                                                                    "</advancedsettings>")):
                                            f_orig.write(line_mod)
                                else:
                                    if (line_trans.startswith("</advancedsettings>") or
                                            nospaces):
                                        line_trans = os.linesep.join([s for s in
                                                                     line_trans.splitlines()
                                                                     if s])
                                        f_orig.write(line_trans)
                                        nospaces = True
                                    else:
                                        f_orig.write(line_trans)

                            if os.path.getsize(advancedsettings_same) == 0:
                                logger.info("UPSSS, ocurrio un error: same.txt esta vacio!")
                            if os.path.getsize(advancedsettings_trans) == 0:
                                logger.info("UPSSS, ocurrio un error: trans.txt esta vacio!")
                                for line_mod in f_mod:
                                    f_orig.write(line_mod)

                    platformtools.dialog_ok("pelisalacarta",
                                            "Se ha modificado el fichero advancedsettings.xml",
                                            "con la configuración óptima para el streaming")
            if os.path.exists(advancedsettings_same):
                logger.info("pelisalacarta.channels.ayuda Archivo de comparacion eliminado")
                os.remove(advancedsettings_same)
            if os.path.exists(advancedsettings_trans):
                logger.info("pelisalacarta.channels.ayuda Archivo de translacion eliminado")
                os.remove(advancedsettings_trans)
        else:
            platformtools.dialog_notification("pelisalacarta",
                                              "Operacion cancelada por el usuario")

    else:
        # Si no hay advancedsettings.xml se copia el advancedsettings.xml desde el directorio
        # resources al userdata.
        with open(advancedsettings_pelisalacarta) as f_optimo:
            with open(advancedsettings_kodi, "w") as f_original:
                for line in f_optimo:
                    f_original.write(line)
        platformtools.dialog_ok("pelisalacarta",
                                "Se ha creado un fichero advancedsettings.xml",
                                "con la configuración óptima para streaming")

    logger.info("pelisalacarta.channels.ayuda 'force_creation_advancedsettings' method finnished")

    return []


def recover_advancedsettings(item):
    logger.info("pelisalacarta.channels.ayuda recover_advancedsettings")

    fichero_backup = os.path.join(config.get_data_path(),
                                  "original_advancedsettings_backup.xml")
    advancedsettings_kodi = xbmc.translatePath("special://userdata/advancedsettings.xml")

    if platformtools.dialog_yesno("pelisalacarta",
                                  "Deseas restaurar el backup de advancedsettings.xml?") == 1:
        if os.path.exists(fichero_backup):
            logger.info("pelisalacarta.channels.ayuda Existe un backup de advancedsettings.xml")
            with open(fichero_backup) as f_backup:
                with open(advancedsettings_kodi, "w") as f_original:
                    for line in f_backup:
                        f_original.write(line)
            platformtools.dialog_ok("pelislacarta",
                                    "Backup restaurado correctamente")

        else:
            logger.info("pelisalacarta.channels.ayuda No hay ningun backup disponible")
            if platformtools.dialog_yesno("pelisalacarta",
                                          "No hay ningun backup disponible."
                                          "Deseas crearlo?") == 1:
                with open(fichero_backup, "w") as f_backup:
                    for line in f_origen:
                        f_backup.write(line)
                platformtools.dialog_notification("pelisalacarta", "Backup hecho!")
                logger.info("pelisalacarta.channels.ayuda Backup terminado!")
            else:
                platformtools.dialog_notification("pelisalacarta", "Backup no hecho!")
                logger.info("pelisalacarta.channels.ayuda Backup no hecho!")

    else:
        platformtools.dialog_notification("pelisalacarta",
                                          "Operacion cancelada por el usuario")
        logger.info("pelisalacarta.channels.ayuda Optimizacion de adavancedsettings.xml cancelada!")

    return []


def updatebiblio(item):
    logger.info("pelisalacarta.channels.ayuda updatebiblio")

    import library_service
    library_service.update_ayuda()

    # platformtools.dialog_notification(" ", "Actualizando biblioteca...")

    return []
