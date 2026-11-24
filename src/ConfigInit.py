# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from Screens.ChannelSelection import service_types_tv
from Components.config import config
from Components.config import ConfigSelection, ConfigYesNo, ConfigSubsection, ConfigNothing, NoSave
from .MovieCoverDownloadUtils import choices_cover_source
from .ChannelSelection import getServiceList
from .Debug import logger
from .__init__ import _


def getChannelChoices(bouquet):
    logger.info("...")
    servicetypes = bouquet + " ORDER BY name"
    service_list = getServiceList(servicetypes)
    # logger.debug("service_list: %s", service_list)
    channels = []
    if service_list:
        for service_str, service_name in service_list:
            if "::" not in service_str:
                channels.append((service_str, service_name))
    channels.sort(key=lambda channel: channel[1].lower())
    choices = [("", _("Inactive"))] + channels
    # logger.debug("choices: %s", choices)
    return choices


def _initialChoices(name):
    # Only "Inactive" plus the saved channel (if any), so that the saved value survives the load of the setting. The
    # full list of channels is built by populateChannelChoices() at session start, not while the plugin is imported.
    saved = config.plugins.timeshiftcockpit.content.stored_values.get(name)
    choices = [("", _("Inactive"))]
    if saved:
        choices.append((saved, saved))
    return choices


def populateChannelChoices():
    """Replace the placeholder choices of the fixed channels by the list of all TV channels (see _initialChoices)."""
    logger.info("...")
    for cfg in (config.plugins.timeshiftcockpit.fixed1, config.plugins.timeshiftcockpit.fixed2):
        cfg.setChoices(getChannelChoices(service_types_tv), default="")


logger.debug("...")
if not hasattr(config.plugins, "timeshiftcockpit"):
    config.plugins.timeshiftcockpit = ConfigSubsection()
config.plugins.timeshiftcockpit.fake_entry = NoSave(ConfigNothing())
config.plugins.timeshiftcockpit.cover_source = ConfigSelection(
    default="tvs_id", choices=choices_cover_source)
config.plugins.timeshiftcockpit.enabled = ConfigYesNo(default=True)
config.plugins.timeshiftcockpit.permanent = ConfigYesNo(default=False)
config.plugins.timeshiftcockpit.fixed1 = ConfigSelection(
    default="", choices=_initialChoices("fixed1"))
logger.debug(
    "fixed1: %s", config.plugins.timeshiftcockpit.fixed1.value)
config.plugins.timeshiftcockpit.fixed2 = ConfigSelection(
    default="", choices=_initialChoices("fixed2"))
logger.debug(
    "fixed2: %s", config.plugins.timeshiftcockpit.fixed2.value)
# the timeshift recordings go to the first recording folder (a bookmark of MovieCockpit: they are in its list)
config.plugins.timeshiftcockpit.videodir = ConfigSelection(
    default=config.movielist.videodirs.value[0], choices=config.movielist.videodirs.value)
config.plugins.timeshiftcockpit.enable_stream = ConfigYesNo(default=True)
