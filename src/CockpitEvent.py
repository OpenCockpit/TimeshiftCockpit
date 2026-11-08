# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from datetime import datetime
from Screens.InfoBar import InfoBar
from .Debug import logger
from .CutListUtils import ptsToSeconds
from .ServiceEvent import ServiceEvent


class CockpitEvent():

    def __init__(self, session, _service, timeshift_start_time, _service_center):
        logger.info("timeshift_start_time: %s", timeshift_start_time)
        self.session = session
        self.timeshift_start_time = timeshift_start_time
        self.event = None
        self.event_index = None
        self._last_event_index = None
        self.events_data = []
        self.getEventsData()

    def getEventsData(self):
        self.events_data = InfoBar.instance.getEventsInfo()
        logger.debug("events_data: %s", self.events_data)
        return self.events_data

    def getSeekPosition(self):
        logger.error("should be overridden in child class")
        return 0

    def doSkip(self, _target):
        logger.error("should be overridden in child class")

    def getRecordingLength(self):
        logger.error("should be overridden in child class")
        return 0

    def newEvent(self, _event):
        logger.error("should be overridden in child class")

    def previousEvent(self):
        logger.info("...")
        target = 0
        self.getEventInfo()
        if self.event_index:
            logger.debug("index: %s", self.event_index)
            event_data = self.events_data[self.event_index]
            event_start_time, _, _, _, _, _, _ = event_data
            position = self.timeshift_start_time + \
                ptsToSeconds(self.getSeekPosition())
            logger.debug("event_start_time: %s, position: %s",
                         event_start_time, position)
            if position - event_start_time < 15:
                logger.debug("skip to previous")
                event_data = self.events_data[self.event_index - 1]
                event_start_time, _, _, _, _, _, _ = event_data
            target = event_start_time - self.timeshift_start_time
            logger.debug("target: %s", target)
        self.doSkip(target)

    def nextEvent(self):
        logger.info("...")
        self.getEventInfo()
        target = ptsToSeconds(self.getRecordingLength())
        logger.debug("event_index: %s, len(events_data): %s",
                     self.event_index, len(self.events_data))
        if self.event_index is not None and self.event_index < len(self.events_data) - 1:
            event_data = self.events_data[self.event_index + 1]
            event_start_time, _, _, _, _, _, _ = event_data
            target = event_start_time - self.timeshift_start_time
            logger.debug("target: %s", target)
        self.doSkip(target)

    def getEvent(self):
        logger.info("event: %s", self.event)
        return self.event

    def getEventInfo(self):
        logger.info("...")
        before = 0
        offset = 0
        self.event = None
        self.event_index = None
        event_data = (0, 0, "", "", "", "", -1)
        position = self.timeshift_start_time + \
            ptsToSeconds(self.getSeekPosition())
        if not self.events_data:
            self.events_data = self.getEventsData()
        for i, __event_data in enumerate(self.events_data):
            __event_start_time, _, _, _, _, _, _ = __event_data
            if __event_start_time < position:
                self.event_index = i
                event_data = __event_data
                self.event = ServiceEvent(__event_data)
        if self.event_index is not None:
            if self.event_index == 0:
                before = max(0, self.timeshift_start_time - self.events_data[0][0])
            offset = max(
                0, self.events_data[self.event_index][0] - self.timeshift_start_time)
        if self.event_index != self._last_event_index:
            self._last_event_index = self.event_index
            self.newEvent(self.event)

        event_start_time, event_length, event_name, _, _, _, _ = event_data
        logger.debug(
            "before: %s, offset: %s, event_length: %s, event_start_time: %s, timeshift_start_time: %s, event_name: %s",
            before, offset, event_length,
            datetime.fromtimestamp(event_start_time),
            datetime.fromtimestamp(self.timeshift_start_time),
            event_name
        )
        return before, offset, event_length, event_start_time, self.timeshift_start_time
