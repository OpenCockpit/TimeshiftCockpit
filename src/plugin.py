# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


import os
from Plugins.Plugin import PluginDescriptor
from Components.config import config
import Screens.InfoBar
from .__init__ import _
from .Debug import logger
from .Version import VERSION
from . import ConfigInit  # noqa: F401, pylint: disable=unused-import
from .InfoBar import InfoBar
from .SetupScreen import SetupScreen
from .FileUtils import deleteFiles
from .SkinUtils import loadPluginSkin


loadPluginSkin("TimeshiftOverview")


def openSettings(session, **__):
    logger.info("...")
    session.open(SetupScreen)


def menuHook(menuid, **__):
    # Menu / Setup / Recordings, Playback & Timeshift: next to Recording (weight 10), Playback (12) and Timeshift (15).
    # The id must not be "timeshift_setup": an entry of a plugin with the id of an existing one replaces it.
    if menuid == "rec":
        return [("TimeshiftCockpit", openSettings, "timeshiftcockpit_setup", 16)]
    return []


def autoStart(reason, **__):
    if reason == 0:  # startup
        if config.plugins.timeshiftcockpit.enabled.value:
            logger.info("+++ Version: %s starts...", VERSION)
            Screens.InfoBar.InfoBar = InfoBar
    elif reason == 1:  # shutdown
        logger.info("--- shutdown")
        deleteFiles(os.path.join(
            config.usage.timeshift_path.value, "*Timeshift*"))


def Plugins(**__):
    descriptors = [
        PluginDescriptor(
            where=[
                PluginDescriptor.WHERE_AUTOSTART
            ],
            fnc=autoStart
        ),
        PluginDescriptor(
            name="TimeshiftCockpit" + " - " + _("Setup"),
            description=_("Configure timeshift modes and channels"),
            icon="plugin.png",
            where=[
                PluginDescriptor.WHERE_PLUGINMENU,
                PluginDescriptor.WHERE_EXTENSIONSMENU,
            ],
            fnc=openSettings
        ),
        PluginDescriptor(
            name="TimeshiftCockpit",
            description=_("Configure timeshift modes and channels"),
            where=PluginDescriptor.WHERE_MENU,
            needsRestart=False,
            fnc=menuHook
        ),
    ]
    try:
        descriptors += [
            PluginDescriptor(
                where=PluginDescriptor.WHERE_SKINCHANGE,
                fnc=loadPluginSkin
            )
        ]
    except Exception:
        pass

    return descriptors
