# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from time import time, strftime, localtime
from Screens.InfoBar import InfoBar
from Screens.ChoiceBox import ChoiceBox
from .__init__ import _
from .Debug import logger


class EventChoiceBox():
    def __init__(self):
        logger.info("...")

    def openEventChoiceBox(self, session, _title, callback):
        logger.info("...")
        alist = []
        events_data = InfoBar.instance.getEventsInfo()
        if events_data:
            now = int(time())
            for event_data in events_data:
                logger.debug("event_data: %s", event_data)
                if event_data[0] < now:
                    alist.append(
                        (f"{strftime('%H:%M', localtime(event_data[0]))} - {event_data[2]}", list(event_data)))
        alist.sort(key=lambda x: x[0], reverse=True)

        session.openWithCallback(
            callback,
            ChoiceBox,
            list=alist,
            keys=[],
            title=_title
        )
