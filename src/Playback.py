# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0

# pylint: disable=no-member

from Components.config import config
import Screens.Standby
from .Debug import logger
from .CockpitPlayer import CockpitPlayer
from .ServiceUtils import getService


class Playback():

    def __init__(self):
        logger.info("...")

    def startPlayer(self):
        logger.info("...")
        service = getService(self.timeshift_file_path)
        if service:
            self.session.openWithCallback(self.startPlayerCallback, CockpitPlayer, service, config.plugins.timeshiftcockpit,
                                          self.timeshift_start_time, self.infobar_instance, self.service_ref)
        else:
            logger.error("service: %s", self.service)

    def startPlayerCallback(self, action=""):
        logger.info("action: %s", action)
        if not config.plugins.timeshiftcockpit.permanent.value:
            self.infobar_instance.removeTimeshift(self.service_ref.toString())
        if action == "up":
            self.infobar_instance.switchChannelUp()
        elif action == "down":
            self.infobar_instance.switchChannelDown()
        elif action == "power_down":
            self.session.open(Screens.Standby.TryQuitMainloop, 1)
