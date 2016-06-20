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
        itemlist.append(Item(channel=CHANNELNAME,
                             action="force_creation_advancedsettings",
                             title="Crear fichero advancedsettings.xml optimizado", folder=False))
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
    advancedsettings_pelisalacarta = os.path.join(config.get_runtime_path(),
                                                  "resources",
                                                  "advancedsettings.xml")

    if os.path.exists(advancedsettings_kodi):
        logger.info("pelisalacarta.channels.ayuda La ruta de advanced settings del usuario existe!")

        if platformtools.dialog_yesno("pelisalacarta",
                                      "Esto modificara los ajustes avanzados de Kodi. Deseas continuar?") == 1:

                fichero_origen = open(advancedsettings_kodi)
                texto_original = fichero_origen.read()
                fichero_origen.close()

                # Backup del advancedsettings existente, antes de modificarlo.
                fichero_backup = os.path.join(config.get_data_path(),
                                              "original_advancedsettings_backup.xml")
                if not os.path.exists(fichero_backup):
                    fichero_bak = open(fichero_backup, "w")
                    fichero_bak.write(texto_original)
                    fichero_bak.close()
                else:
                    if platformtools.dialog_yesno("Backup anterior encontrado",
                                                  "Deseas sobreescribirlo?") == 1:
                        fichero_bak = open(fichero_backup, "w")
                        fichero_bak.write(texto_original)
                        fichero_bak.close()
                        platformtools.dialog_notification("pelisalacarta",
                                                          "Backup terminado!")
                    else:
                        platformtools.dialog_notification("pelisalacarta",
                                                          "Backup no modificado")

                # Escribir en advancedsettings.xml despues de varias comprobaciones
                with open(advancedsettings_kodi) as file1:
                    with open(advancedsettings_pelisalacarta) as file2:
                        # FIXME No hace bien la comparacion!
                        same = set(file2).intersection(file1)
                        with open(os.path.join(config.get_data_path(),
                                               "same.txt"), "w") as f_same:
                            for line in same:
                                f_same.write(line)

                with open(advancedsettings_pelisalacarta) as f_optimo:
                    if same == f_optimo:
                        platformtools.dialog_ok("pelisalacarta",
                                                "Los cambios ya estaban aplicados")
                    else:
                        platformtools.dialog_ok("pelisalacarta",
                                                "Los ajustes avanzados no estaban optimizados")
                        with open(advancedsettings_kodi) as f_original:
                            with open(os.path.join(config.get_data_path(),
                                                   "trans.txt"), "w") as f_trans:
                                for line in f_original:
                                    f_trans.write(line)
                                    if line.startswith("<network>"):
                                        break

                                f_trans.write('\n')

                                continue_writting = False

                                for line in f_original:
                                    if line.startswith("</network>") or continue_writting:
                                        f_trans.write(line)
                                        continue_writing = True

                        # Se vacia el advancedsettings original
                        open(advancedsettings_kodi, "w").close()

                        # Se vuelve a abrir el archivo de transisicion para ser leido
                        with open(os.path.join(config.get_data_path(), "trans.txt")) as f_trans:
                            with open(advancedsettings_kodi, "w") as advsettings_out:
                                for line in f_trans:
                                    if not line.startswith("<network>"):
                                        advsettings_out.write(line)
                                    else:
                                        for line in f_optimo:
                                            if line.startswith(("<network>",
                                                                "<advancedsettings>")):
                                                advsettings_out.write(line)
                                                # break

                        platformtools.dialog_ok("pelisalacarta",
                                                "Se ha modificado el fichero advancedsettings.xml",
                                                "con la configuración óptima para el streaming")

                os.remove(os.path.join(config.get_data_path(), "trans.txt"))

        else:
                platformtools.dialog_notification("pelisalacarta",
                                                  "Operacion cancelada por el usuario")

    else:
        # Si no hay advancedsettings.xml se copia el advancedsettings.xml
        # desde el directorio resources al userdata.
        with open(advancedsettings_pelisalacarta) as f_optimo:
            with open(advancedsettings_kodi, "w") as f_original:
                for line in f_optimo:
                    f_original.write(line)
        platformtools.dialog_ok("pelisalacarta",
                                "Se ha creado un fichero advancedsettings.xml",
                                "con la configuración óptima para streaming")

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
            platformtools.dialog_ok("pelisalacarta",
                                    "No hay ningun backup disponible para poder restaurar")
        # TODO terminarlo
    else:
        platformtools.dialog_notification("pelisalacarta",
                                          "Operacion cancelada por el usuario")
    return []


def updatebiblio(item):
    logger.info("pelisalacarta.channels.ayuda updatebiblio")

    import library_service
    library_service.update_ayuda()

    # platformtools.dialog_notification(" ", "Actualizando biblioteca...")

    return []
