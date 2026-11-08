# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from time import time
from Screens.InfoBar import InfoBar as InfoBarOrg
from Screens.MessageBox import MessageBox
from Screens.Standby import inStandby
from Components.ActionMap import HelpableActionMap
from Components.config import config
from Components.ServiceEventTracker import ServiceEventTracker
from Tools import Notifications
from enigma import eTimer, eServiceReference, iPlayableService, iRecordableService
import NavigationInstance
from .Debug import logger
from .Timeshift import Timeshift
from .DelayTimer import DelayTimer
from .JobUtils import getPendingJobs
from .__init__ import _
from .Version import ID


instance = None


class InfoBar(InfoBarOrg):

    def __init__(self, session):
        InfoBarOrg.__init__(self, session)
        InfoBarOrg.instance = self
        global instance  # pylint: disable=global-statement
        instance = self
        self.service_str = ""
        self.service_ref = None
        self.first = True
        self.fixed_services = []
        self.timeshifts = {}
        self._event_tracker = ServiceEventTracker(
            screen=self,
            eventmap={
                iPlayableService.evStart: self.__serviceStarted,
            }
        )
        self.wait_for_time_timer = eTimer()
        self.wait_for_time_timer.callback.append(self.__serviceStarted)
        self.max_timeshifts = 0
        NavigationInstance.instance.record_event.append(self.gotRecordEvent)
        self.setFixedServices()

        # pressing pause on live TV fires "timeshiftStart" in Enigma2's own
        # "InfobarTimeshiftActions" keymap context - this binding is what
        # actually wires that key press to startTimeshift() below; without
        # it, the key press reaches no active handler and Enigma2 shows the
        # disabled-action icon instead of starting timeshift. A distinct key
        # name (not "TimeshiftActions") avoids colliding with InfoBarOrg's
        # own ActionMap of that name, which gates itself on core's own
        # (unused here) recording-based timeshift state and would otherwise
        # keep intercepting the key as permanently disabled.
        self["TSCTimeshiftActions"] = HelpableActionMap(
            self, "InfobarTimeshiftActions",
            {
                "timeshiftStart": (self.startTimeshift, _("start timeshift")),
            }
        )

    def gotRecordEvent(self, _service, event):
        if event == iRecordableService.evRecordWriteError:
            self.removeTimeshift()

    def setFixedServices(self):
        self.fixed_services = []
        fixed1 = config.plugins.timeshiftcockpit.fixed1.value
        if fixed1:
            self.fixed_services.append(fixed1)
        fixed2 = config.plugins.timeshiftcockpit.fixed2.value
        if fixed2:
            self.fixed_services.append(fixed2)
        self.max_timeshifts = len(self.fixed_services) + 1
        logger.debug("max_timeshifts: %s", self.max_timeshifts)

    def __serviceStarted(self):
        logger.info("...")
        if config.plugins.timeshiftcockpit.permanent.value:
            if int(time()) > 1000000:
                DelayTimer(100, self.startTimeshifts)
            else:
                self.wait_for_time_timer.start(1000, True)

    def startTimeshift(self):
        # pause
        logger.info("...")
        if not config.plugins.timeshiftcockpit.permanent.value:
            self.service_ref = self.session.nav.getCurrentlyPlayingServiceReference()
            self.service_str = self.service_ref.toString()
            self.addTimeshift(self.service_str)
        if self.service_str in self.timeshifts:
            self.timeshifts[self.service_str].startPlayer()
            self.first = False
        else:
            Notifications.AddPopup(text=_("No timeshift available for playback"),
                                   type=MessageBox.TYPE_INFO, timeout=5, id="No_Timeshift")

    def startTimeshifts(self):
        # zap
        logger.info("first: %s", self.first)
        last_service_str = self.service_str
        self.service_ref = self.session.nav.getCurrentlyPlayingServiceReference()
        if self.service_ref:
            self.service_str = self.service_ref.toString()
            # logger.debug("zapping to: %s", self.service_str)
            for fixed_service_str in self.fixed_services:
                self.addTimeshift(fixed_service_str)
            if self.service_str != last_service_str:
                # logger.debug("service changed")
                if last_service_str and last_service_str not in self.fixed_services:
                    self.removeTimeshift(last_service_str)
                self.addTimeshift(self.service_str)

    def addTimeshift(self, service_str=None):
        logger.info("service_str: %s, timeshifts: %s",
                    service_str, self.timeshifts.keys())
        if service_str is not None:
            if service_str.startswith("4097:") and config.plugins.timeshiftcockpit.enable_stream.value is False:
                logger.info("skipping timeshift for 4097 service: %s", service_str)
                return
            logger.debug("max_timeshifts: %s", self.max_timeshifts)
            if service_str not in self.timeshifts and len(self.timeshifts) < self.max_timeshifts:
                self.timeshifts[service_str] = Timeshift(
                    self.session, eServiceReference(service_str), instance)
                if self.timeshifts[service_str].startTimeshift() is None:
                    self.timeshifts.pop(service_str, None)
        else:
            self.setFixedServices()
            self.service_str = ""
            self.startTimeshifts()

    def removeTimeshift(self, service_str=None):
        logger.info("service_str: %s, timeshifts: %s",
                    service_str, self.timeshifts.keys())
        if service_str is not None:
            if service_str in self.timeshifts and not self.isTimeshiftRecording(service_str):
                self.timeshifts[service_str].stopTimeshift()
                self.timeshifts.pop(service_str, None)
        else:
            for tmp_service_str in self.timeshifts.copy():
                self.removeTimeshift(tmp_service_str)
        logger.info("service_str: %s, timeshifts: %s",
                    service_str, self.timeshifts.keys())

    def startTSRecording(self, service_ref, event_data):
        logger.info("...")
        service_str = service_ref.toString()
        self.timeshifts[service_str].addTSRecordingJob(event_data, service_ref)

    def stopTSRecording(self, service_str):
        logger.info("service_str: %s, self.service_str: %s",
                    service_str, self.service_str)
        if not inStandby:
            if service_str not in self.fixed_services and self.service_str != service_str:
                self.removeTimeshift(service_str)
                self.addTimeshift(self.service_str)
        else:
            self.removeTimeshift(service_str)

    def getEventsInfo(self):
        logger.info("service_str: %s", self.service_str)
        return self.timeshifts[self.service_str].getEventsInfo()

    def isTimeshifting(self):
        is_timeshifting = len(self.timeshifts) > 0
        logger.info("service_str: %s, is_timeshifting: %s",
                    self.service_str, is_timeshifting)
        return is_timeshifting

    def isTimeshiftRecording(self, path_or_ref=""):
        is_timeshift_recording = False
        jobs = getPendingJobs(ID)
        for job in jobs:
            if path_or_ref:
                if path_or_ref in [job.target_path, job.service_str]:
                    is_timeshift_recording = True
                    break
            else:
                is_timeshift_recording = True
                break
        logger.debug("path_or_ref: %s, is_timeshift_recording: %s",
                     path_or_ref, is_timeshift_recording)
        return is_timeshift_recording

    def getTimeshiftRecordings(self, service_str=""):
        logger.info("...")
        recordings_list = []
        jobs = getPendingJobs(ID)
        for job in jobs:
            if service_str:
                if job.service_str == service_str:
                    recordings_list.append(job.target_path)
            else:
                recordings_list.append(job.target_path)
        return recordings_list
