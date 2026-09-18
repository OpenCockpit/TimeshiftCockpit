# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


import os
from time import time
from Components.ActionMap import HelpableActionMap
from Components.config import config
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Sources.COCCurrentService import COCCurrentService
from Screens.Screen import Screen, ScreenSummary
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBarGenerics import InfoBarAudioSelection, InfoBarShowHide, InfoBarNotifications
from Screens.MessageBox import MessageBox
from ServiceReference import ServiceReference
from enigma import iPlayableService
from .__init__ import _
from .Debug import logger
from .CockpitSeek import CockpitSeek
from .CockpitCueSheet import CockpitCueSheet
from .MovieInfoEPG import MovieInfoEPG
from .CockpitPVRState import CockpitPVRState
from .Version import ID
from .EventChoiceBox import EventChoiceBox
from .DelayTimer import DelayTimer
from .TimeshiftUtils import manageTimeshiftRecordings
from .TimeshiftOverview import TimeshiftOverview
from .CutListUtils import secondsToPts


class CockpitPlayerSummary(ScreenSummary):

    def __init__(self, session, parent):
        ScreenSummary.__init__(self, session, parent=parent)
        self.skinName = ["CockpitPlayerSummary", "ScreenSummary"]


class CockpitPlayer(
        Screen, HelpableScreen, InfoBarBase, InfoBarNotifications, CockpitSeek, InfoBarShowHide, InfoBarAudioSelection, CockpitPVRState, CockpitCueSheet, EventChoiceBox):

    ENABLE_RESUME_SUPPORT = False
    ALLOW_SUSPEND = False

    def __init__(self, session, service, config_plugins_plugin, timeshift_start_time, infobar_instance, service_ref):
        logger.info("timeshift_start_time: %s", timeshift_start_time)
        self.service = service
        self.config_plugins_plugin = config_plugins_plugin
        self.timeshift_start_time = timeshift_start_time
        self.infobar_instance = infobar_instance
        self.service_ref = service_ref

        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
        InfoBarShowHide.__init__(self)
        InfoBarBase.__init__(self)
        InfoBarAudioSelection.__init__(self)
        InfoBarNotifications.__init__(self)
        CockpitCueSheet.__init__(self, service)
        EventChoiceBox.__init__(self)

        self["Service"] = COCCurrentService(session.nav, self)

        event_start = True
        self.service_started = False
        self.last_service = session.nav.getCurrentlyPlayingServiceReference()

        CockpitSeek.__init__(self, session, service, event_start,
                             timeshift_start_time, timeshift=True, service_center=None)
        CockpitPVRState.__init__(self)

        # one or more of the InfoBarXXX mixins above resets self.skinName to
        # their own default when they run their own __init__ (same
        # Screen.__init__-overwrites-skinName pattern seen elsewhere in this
        # codebase) - setting it straight after Screen.__init__() wasn't
        # enough, since later mixin __init__ calls stomped it again. Setting
        # it last, after every base __init__ has run, is what actually
        # sticks - this is why skin lookup was falling back to an
        # undefined embedded skin ("<embedded-in-CockpitPlayer>",
        # position=(?, ?)) instead of resolving TimeshiftCockpitPlayer.
        self.skinName = "CockpitPlayer"

        self._event_tracker = ServiceEventTracker(
            screen=self,
            eventmap={
                iPlayableService.evStart: self.__serviceStarted,
            }
        )

        actions = {
            "EXIT": (self.leavePlayer, _("Stop timeshift")),
            "STOP": (self.leavePlayer, _("Stop timeshift")),
            "POWER": (self.powerDown, _("Power off")),
            "INFO": (self.showMovieInfo, _("Movie info")),
            "NEXT": (self.nextEvent, _("Next event")),
            "PREVIOUS": (self.previousEvent, _("Previous event")),
            "MENU": (self.selectEventPlayback, _("Show events")),
            "RECORD": (self.selectEventRecording, _("Record timeshift Event")),
            "BLUE": (self.blueKey, _("Show active timeshifts")),
            "YELLOW": (self.yellowKey, _("Manage timeshift recordings"))
        }

        if config_plugins_plugin.permanent.value:
            actions["UP"] = (self.up, _("Open service list"))
            actions["DOWN"] = (self.down, _("Open service list"))

        self["actions"] = HelpableActionMap(
            self,
            "TimeshiftCockpitActions",
            actions,
            -1
        )

        self.execing = None
        self.cut_list = []

        self.onShown.append(self.__onShown)

    def noOp(self):
        return

    def blueKey(self):
        self.session.open(TimeshiftOverview, self.infobar_instance)

    def yellowKey(self):
        manageTimeshiftRecordings(self.session, ID)

    def powerDown(self):
        self.leavePlayer("power_down")

    def up(self):
        self.leavePlayer("up")

    def down(self):
        self.leavePlayer("down")

    def getInfo(self):
        return None

    def getEvent(self):
        return self.event

    def newEvent(self, event):
        self["Service"].newEvent(event)

    def selectEventPlayback(self):
        self.openEventChoiceBox(self.session, _(
            "Select a timeshift event for playback"), self.selectEventPlaybackCallback)

    def selectEventPlaybackCallback(self, answer=None):
        logger.info("...")
        if answer:
            event_start = answer[1][0]
            logger.debug("event_start: %s", event_start)
            self.doSkip(max(0, event_start - self.timeshift_start_time))
            self.setSeekState(self.SEEK_STATE_PLAY)

    def selectEventRecording(self):
        logger.info("...")
        self.openEventChoiceBox(self.session, _(
            "Select a timeshift event for recording"), self.selectEventRecordingCallback)

    def selectEventRecordingCallback(self, answer=None):
        logger.info("...")
        if answer:
            event_data = answer[1]
            logger.debug("event_data: %s", event_data)
            self.infobar_instance.startTSRecording(
                self.service_ref, event_data)
            DelayTimer(1000, self.session.open, MessageBox, _(
                "Recording timeshift event now") + "...", MessageBox.TYPE_INFO, 5)

    def createSummary(self):
        return CockpitPlayerSummary

    def __onShown(self):
        logger.info("...")
        if not os.path.exists(config.usage.timeshift_path.value):
            self.session.open(MessageBox, _("Timeshift directory does not exist")
                              + ": " + config.usage.timeshift_path.value, MessageBox.TYPE_ERROR)
            self.leavePlayer()
            return
        if not self.service_started:
            self.session.nav.playService(self.service)

    def __serviceStarted(self):
        logger.info("...")
        if not self.service_started:
            self.service_started = True
            if not config.plugins.timeshiftcockpit.permanent.value:
                self.session.nav.pnav.pause(1)
                self.pauseService()
            else:
                self.pauseService()
                self.doSkip(int(time()) - self.timeshift_start_time)

    def showMovieInfo(self):
        # self.event is only ever refreshed as a side effect of
        # getEventInfo(), which nothing calls automatically on entering the
        # player - only nextEvent()/previousEvent()/skipForward()/
        # skipBackward() do, reactively. Refresh it here too, or INFO
        # pressed before any of those shows nothing on a still-None event.
        self.getEventInfo()
        if self.event:
            self.session.open(MovieInfoEPG, self.event,
                              ServiceReference(self.service))

    def showPVRStatePic(self, show):
        self.show_state_pic = show

    def leavePlayer(self, ret_val=None):
        logger.info("...")
        self.session.nav.stopService()
        self.session.nav.playService(self.last_service)
        if not config.plugins.timeshiftcockpit.permanent.value:
            self.session.nav.pnav.pause(0)
        self.onShown.remove(self.__onShown)
        self.close(ret_val)

    def doEofInternal(self, playing):
        logger.info("playing: %s, self.execing: %s", playing, self.execing)
        # self.pvr_state_dialog.hide()
        self.showPVRStatePic(False)
        self.doSeekRelative(-secondsToPts(5))
        self.setSeekState(self.SEEK_STATE_PLAY)
