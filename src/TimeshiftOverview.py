# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from ServiceReference import ServiceReference
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Components.Button import Button
from Components.Sources.List import List
from Components.ActionMap import HelpableActionMap
from .__init__ import _
from .ServiceUtils import getPicon
from .Debug import logger


class TimeshiftOverview(Screen, HelpableScreen):

    def __init__(self, session, infobar_instance):
        self.infobar_instance = infobar_instance
        Screen.__init__(self, session)
        self.skinName = "TimeshiftOverview"
        HelpableScreen.__init__(self)

        self["actions"] = HelpableActionMap(
            self,
            "TimeshiftCockpitActions",
            {
                "OK": (self.exit, _("Exit")),
                "EXIT": (self.exit, _("Exit")),
                "RED": (self.exit, _("Exit")),
                "GREEN": (self.exit, _("Exit")),
            },
            prio=-1
        )

        self.setTitle(_("Timeshifts Overview"))
        self["list"] = List()
        self["key_green"] = Button()
        self["key_red"] = Button(_("Exit"))
        self["key_yellow"] = Button()
        self["key_blue"] = Button()
        self.onLayoutFinish.append(self.fillList)
        self.onShow.append(self.__disableSelection)

    def exit(self):
        self.close()

    def __disableSelection(self):
        try:
            self["list"].master.master.setSelectionEnabled(0)
        except AttributeError:
            pass

    def fillList(self):
        logger.info("...")
        alist = []
        for service_str in self.infobar_instance.timeshifts.keys():
            pixmap_ptr = getPicon(service_str)
            service_name = ServiceReference(service_str).getServiceName()
            timeshift_type = f"{_('type')}: {_('fixed') if service_str in self.infobar_instance.fixed_services else _('variable')}"
            timeshift_recordings = f"{_('recordings')}: {len(self.infobar_instance.getTimeshiftRecordings(service_str))}"
            alist.append((pixmap_ptr, service_name, timeshift_type, timeshift_recordings))
        alist = sorted(alist, key=lambda x: (x[2], x[1]))
        self["list"].setList(alist)
