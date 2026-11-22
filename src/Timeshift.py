# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


import os
from time import time
import NavigationInstance
from Components.config import config
from enigma import eEPGCache, eServiceReference
from Tools import Notifications
from Screens.MessageBox import MessageBox
from .Debug import logger
from .Playback import Playback
from .TSRecordingJob import TSRecordingJob
from .TimeshiftUtils import formatTime
from .RecordingUtils import calcRecordingFilename
from .FileUtils import deleteFiles
from .DelayTimer import DelayTimer
from .__init__ import _


POLL_INTERVAL = 250     # ms between the checks whether the recorder has written data
POLL_TIME = 20000       # ms to wait for the first data (the tuner has to tune in first) before the check is left to startPlayer()


class Timeshift(Playback, TSRecordingJob):

    def __init__(self, session, service_ref, infobar_instance):
        logger.info("service_ref: %s", service_ref.toString())
        Playback.__init__(self)
        TSRecordingJob.__init__(self)
        self.session = session
        self.service_ref = service_ref
        self.service_str = service_ref.toString()
        self.infobar_instance = infobar_instance
        self.record_service = None
        self.timeshift_start_time = 0
        self.timeshift_file_path = ""
        self.events_info = []
        # The record service is prepared right away (the tuner starts to tune), but the recording is only started when the
        # tuner has tuned in and the program info (PMT) is known: a recording started earlier has distortions at its beginning.
        # The record service of a timeshift is a simulated one, so the navigation sends no events for it (no evTunedIn): the
        # state of the record service is polled. The timeshift has started (timeshift_start_time is the time of its first
        # data) when the file has data, which is also what the player needs.
        self.recording = False
        self.started = False
        self.player_pending = False
        self.poll_timer = None
        self.poll_waited = 0

    def stopTimeshift(self):
        logger.info("record_service: %s", self.record_service)
        logger.info("timeshift_file_path: %s", self.timeshift_file_path)
        self.stopPolling()
        self.player_pending = False
        self.recording = False
        self.started = False
        if self.record_service:
            NavigationInstance.instance.stopRecordService(self.record_service)
            self.record_service = None
            deleteFiles(os.path.splitext(
                self.timeshift_file_path)[0] + ".*", True)

    def startTimeshift(self):
        # Returns the record service, or None if it could not be started.
        logger.info("...")
        if not self.record_service:
            self.record_service = self.record(self.service_ref)
            logger.debug("record_service: %s", self.record_service)
            logger.debug("timeshift_file_path: %s", self.timeshift_file_path)
        return self.record_service

    def startPlayer(self):
        if not self.record_service:
            return
        if self.checkStarted():
            Playback.startPlayer(self)
        else:
            logger.info("recording has no data yet, waiting for the tuner")
            self.player_pending = True
            self.startPolling()

    def hasTuner(self):
        # Only the DVB record service (also for DVB over IP streams) has a tune phase and program info to wait for. The record
        # service of the other types (4097, 5001, ...: gstreamer / exteplayer3) has neither: these are started at once.
        return self.service_ref.type in (eServiceReference.idDVB, eServiceReference.idDVB + 0x100)

    def isTunedIn(self):
        """Is the record service tuned in and is its program info known? (the same test as the streaming converter)"""
        if not self.hasTuner():
            return True
        try:
            stream = self.record_service.stream()
            data = stream and stream.getStreamingData()
            return bool(data) and any(data)
        except Exception as e:
            logger.debug("no stream data: %s", str(e))
            return False

    def startRecording(self):
        if self.record_service.start():
            logger.debug("start record failed.")
            DelayTimer(100, self.tuneFailed)
            return False
        self.recording = True
        return True

    def tuneFailed(self):
        # drop this timeshift: stopTimeshift() is done by the infobar, which also forgets it
        if self.record_service:
            if self.player_pending:
                Notifications.AddPopup(text=_("No timeshift available for playback"),
                                       type=MessageBox.TYPE_INFO, timeout=5, id="No_Timeshift")
            self.infobar_instance.removeTimeshift(self.service_str)

    def hasData(self):
        try:
            return os.path.getsize(self.timeshift_file_path) > 0
        except OSError:
            return False

    def checkStarted(self):
        """Has the recorder written data? Then the recording is started (and the player can be)."""
        if not self.started and self.recording and self.record_service and self.hasData():
            self.started = True
            self.timeshift_start_time = int(time())
            logger.debug("timeshift_start_time: %s",
                         formatTime(self.timeshift_start_time))
            self.events_info = self.getEventsInfo()
        return self.started

    def startPolling(self):
        self.stopPolling()
        self.poll_waited = 0
        self.poll_timer = DelayTimer(POLL_INTERVAL, self.poll)

    def stopPolling(self):
        if self.poll_timer:
            self.poll_timer.stop()
            self.poll_timer = None

    def poll(self):
        self.poll_timer = None
        if not self.record_service or self.started:
            return
        if not self.recording and self.isTunedIn():
            logger.info("tuned in, service: %s", self.service_str)
            if not self.startRecording():
                return
        if self.checkStarted():
            logger.info("recording has started, service: %s", self.service_str)
            if self.player_pending:
                self.player_pending = False
                self.startPlayer()
            return
        self.poll_waited += POLL_INTERVAL
        if self.poll_waited < POLL_TIME:
            self.poll_timer = DelayTimer(POLL_INTERVAL, self.poll)
        else:
            logger.warning("no tuner lock / data after %s ms, service: %s", self.poll_waited, self.service_str)
            if self.player_pending:
                self.player_pending = False
                Notifications.AddPopup(text=_("No timeshift available for playback"),
                                       type=MessageBox.TYPE_INFO, timeout=5, id="No_Timeshift")

    def getEventsInfo(self):
        # I = Event Id, B = Event Begin Time, D = Event Duration, T = Event Title
        # S = Event Short Description, E = Event Extended Description, C = Current Time
        # R = Service Reference String, N = Service Name, n = Short Service Name
        # X = Return a minimum of one tuple per service in the result list... even when no event was found
        logger.info("...")
        if self.service_ref and self.started:
            events_info = eEPGCache.getInstance().lookupEvent(
                ["BDTSENI", (self.service_ref.toString(), -1, self.timeshift_start_time, 24 * 60)])
            if len(events_info) > len(self.events_info):
                self.events_info = events_info
                logger.debug("events_info: %s", self.events_info)
        return self.events_info

    def record(self, service_ref):
        logger.info("...")
        record_service = NavigationInstance.instance.recordService(service_ref, True)
        if not record_service:
            logger.debug("no record_service")
            return None

        # Store immediately so getRecordings() filter can identify this
        # as a timeshift before prepare()/start() trigger any events
        self.record_service = record_service

        begin = end = int(time())
        self.timeshift_file_path = calcRecordingFilename(
            begin, service_ref, "Timeshift", config.usage.timeshift_path.value) + ".ts"
        if record_service.prepare(self.timeshift_file_path, begin, end, -1, "", "", "", True, False):
            logger.debug("prepare failed.")
            self.record_service = None
            NavigationInstance.instance.stopRecordService(record_service)
            return None

        self.startPolling()
        return record_service
