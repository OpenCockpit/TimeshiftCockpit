# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from Components.config import config
from Screens.Setup import Setup
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop, QUIT_RESTART
from .__init__ import _
from .Version import PLUGIN
from .Debug import logger, log_levels, setLogLevel
from .RecordingUtils import stopTimeshift, startTimeshift
from .ChannelSelection import ChannelSelection


class SetupScreen(Setup, ChannelSelection):

    def __init__(self, session):
        config.plugins.timeshiftcockpit.videodir.value = config.usage.timeshift_path.value
        Setup.__init__(self, session, setup="timeshiftcockpit", plugin="Extensions/TimeshiftCockpit", PluginLanguageDomain=PLUGIN)
        ChannelSelection.__init__(self, session)
        self.setTitle(PLUGIN + " - " + _("Setup"))

    def keyOK(self):
        current = self["config"].getCurrent()
        if current:
            cfg = current[1]
            if cfg in (config.plugins.timeshiftcockpit.fixed1, config.plugins.timeshiftcockpit.fixed2):
                self.getChannel(callback=lambda service_str: self._channelSelected(cfg, service_str))
                return
        Setup.keyOK(self)

    def _channelSelected(self, cfg_entry, service_str):
        logger.info("service_str: %s", service_str)
        if service_str is not None:
            cfg_entry.value = service_str
            self["config"].invalidate(self["config"].getCurrent())

    def keySave(self):
        permanent_changed = config.plugins.timeshiftcockpit.permanent.value != config.plugins.timeshiftcockpit.permanent.saved_value
        fixed_changed = (
            config.plugins.timeshiftcockpit.fixed1.value != config.plugins.timeshiftcockpit.fixed1.saved_value or
            config.plugins.timeshiftcockpit.fixed2.value != config.plugins.timeshiftcockpit.fixed2.saved_value
        )
        enabled_changed = config.plugins.timeshiftcockpit.enabled.value != config.plugins.timeshiftcockpit.enabled.saved_value
        setLogLevel(log_levels[config.plugins.timeshiftcockpit.debug_log_level.value])
        if enabled_changed:
            # the InfoBar patch that activates/deactivates the plugin only
            # runs at enigma2 startup (see plugin.py autoStart) - toggling
            # this setting has no effect until a GUI restart. This has to
            # open before Setup.keySave() below, which closes this screen -
            # a screen can only open a new modal dialog while it's still
            # the session's active one.
            self.session.openWithCallback(
                lambda answer: self._finishSave(permanent_changed, fixed_changed, answer),
                MessageBox,
                _("TimeshiftCockpit has been %s. Restart Enigma2 now for this to take effect?") % (
                    _("activated") if config.plugins.timeshiftcockpit.enabled.value else _("deactivated")),
                type=MessageBox.TYPE_YESNO,
                default=True
            )
        else:
            self._finishSave(permanent_changed, fixed_changed, False)

    def _finishSave(self, permanent_changed, fixed_changed, restart_answer):
        # Same reasoning as keySave()'s own comment above: this has to open
        # before Setup.keySave() below, which closes this screen - a screen
        # can only open a new modal dialog while it's still the session's
        # active one.
        if restart_answer:
            self.session.open(TryQuitMainloop, retvalue=QUIT_RESTART)
        Setup.keySave(self)
        if permanent_changed:
            if config.plugins.timeshiftcockpit.permanent.value:
                startTimeshift()
            else:
                stopTimeshift()
        elif fixed_changed:
            stopTimeshift()
            startTimeshift()
