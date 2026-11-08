# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from time import localtime, strftime
from .Debug import logger


class ServiceEvent():

    def __init__(self, event_data):
        logger.info("event_data: %s", event_data)
        self.begin, self.duration, self.name, self.short_description, self.extended_description, _, _ = event_data

    def getBeginTime(self):
        return self.begin

    def getDuration(self):
        return self.duration

    def getEventId(self):
        return 0

    def getEventName(self):
        return self.name

    def getShortDescription(self):
        return self.short_description

    def getExtendedDescription(self, _original=False):
        return self.extended_description

    def getBeginTimeString(self):
        return strftime("%d.%m. %H:%M", localtime(self.begin))
