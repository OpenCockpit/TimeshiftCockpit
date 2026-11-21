# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0

"""Let a running timeshift recording count as a recording for the front panel led (and the other users of RecordState).

A timeshift recording is a copy job (ffmpeg), not a recording of the navigation: session.nav.getRecordings() does not know
it, so the "recording" state of the session (session.screen["RecordState"]) stays off and the led does not blink. The
RecordState source of the session is switched to a subclass that adds the number of running timeshift recordings to the
number of real recordings. The source then tells its downstream elements (the FrontpanelLed renderers of SessionGlobals
among them) that it changed, so they set the led pattern the way they do for a normal recording, and set it back
when the last one has ended, whatever else (a real recording, standby) is going on."""

from Components.Sources.RecordState import RecordState
from .Debug import logger


class TSRecordState(RecordState):
    """RecordState that counts the running timeshift recordings as well."""

    def getRecordsRunning(self):
        return self._records + len(self.ts_tasks)

    def setRecordsRunning(self, value):
        # RecordState.gotRecordEvent stores the number of real recordings here
        self._records = value

    records_running = property(getRecordsRunning, setRecordsRunning)


def _getRecordState(session):
    try:
        record_state = session.screen["RecordState"]
    except Exception as e:
        logger.debug("no RecordState: %s", str(e))
        return None
    if not isinstance(record_state, TSRecordState):
        # the instance attribute of the original class would hide the property of the subclass
        records = record_state.__dict__.pop("records_running", 0)
        record_state.__class__ = TSRecordState
        record_state._records = records
        record_state.ts_tasks = set()
    return record_state


def startTSRecordingLed(session, task):
    record_state = _getRecordState(session)
    if record_state is not None and task not in record_state.ts_tasks:
        logger.info("task: %s", task)
        record_state.ts_tasks.add(task)
        record_state.changed((record_state.CHANGED_ALL,))


def stopTSRecordingLed(session, task):
    record_state = _getRecordState(session)
    if record_state is not None and task in record_state.ts_tasks:
        logger.info("task: %s", task)
        record_state.ts_tasks.discard(task)
        record_state.changed((record_state.CHANGED_ALL,))
