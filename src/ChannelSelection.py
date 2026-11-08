# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0

from Screens.ChoiceBox import ChoiceBox
from Screens.ChannelSelection import service_types_tv
from .ChannelListUtils import getServiceList, getTVBouquets
from .__init__ import _
from .Debug import logger


class ChannelSelection():
    def __init__(self, session):
        self.session = session
        self.callback = None

    def getChannel(self, callback):
        logger.info("...")
        self.__callback = callback
        bouquet_list = self.getBouquets()
        self.session.openWithCallback(
            self.gotBouquet,
            ChoiceBox,
            title=_("Select bouquet"),
            list=bouquet_list,
            keys=[]
        )

    def getBouquets(self):
        logger.info("...")
        tvbouquets = getTVBouquets()
        alist = []
        alist.append(["Alle Sender (Enigma)", service_types_tv])
        for bouquet in tvbouquets:
            logger.debug("bouquet: %s", bouquet)
            alist.append([bouquet[1], bouquet[0]])
        return alist

    def gotBouquet(self, choice):
        logger.info("choice: %s", choice)
        if choice:
            channel_list = self.getChannels(choice[1])
            self.session.openWithCallback(
                self.gotChannel,
                ChoiceBox,
                title=_("Select channel"),
                list=channel_list,
                keys=[]
            )
        else:
            self.__callback(None)

    def getChannels(self, bouquet):
        logger.info("...")
        alist = []
        servicetypes = bouquet + " ORDER BY name"
        service_list = getServiceList(servicetypes)
        logger.debug("service_list: %s", service_list)
        if service_list:
            for service, ename in service_list:
                if "::" not in service:
                    alist.append((ename, service))
        return alist

    def gotChannel(self, choice):
        logger.info("choice: %s", choice)
        if choice:
            self.__callback(choice[1])
        else:
            self.__callback(None)
