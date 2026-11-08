# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


import os
from time import strftime, localtime
from enigma import eEPGCache, eServiceReference
from Components.config import config
from .Debug import logger
from .ParserMetaFile import ParserMetaFile
from .FileUtils import writeFile
from .PluginUtils import getPlugin, WHERE_JOBCOCKPIT


ERROR_NONE = 0
ERROR_NO_DISKSPACE = 1
ERROR_ABORT = 2
ERROR = 100


def formatTime(seconds):
    return strftime("%Y-%m-%d %H:%M:%S", localtime(seconds))


def calcRecordingTimes(timeshift_start_time, event_start_time, event_duration):
    logger.info("...")
    logger.debug("*in* timeshift_start_time: %s",
                 formatTime(timeshift_start_time))
    logger.debug("*in* event_start_time: %s", formatTime(event_start_time))
    logger.debug("*in* event_duration: %s", event_duration)
    copy_begin_time = max(timeshift_start_time, event_start_time
                          - config.recording.margin_before.value * 60)
    copy_end_time = event_start_time + event_duration + \
        config.recording.margin_after.value * 60
    logger.debug("*out* copy_begin_time: %s", formatTime(copy_begin_time))
    logger.debug("*out* copy_end_time: %s", formatTime(copy_end_time))
    return copy_begin_time, copy_end_time


def createEitFile(service_str, target_path, eventid):
    filename = os.path.splitext(target_path)[0] + ".eit"
    serviceref = eServiceReference(service_str)
    eEPGCache.getInstance().saveEventToFile(filename, serviceref, eventid, -1, -1)


def createMetaFile(service_str, target_path, event_start_time, event_title, event_description, event_length):
    logger.info("target_path: %s, event_start_time: %s, event_title: %s, event_description: %s, event_length: %s",
                target_path, event_start_time, event_title, event_description, event_length)
    ParserMetaFile(target_path).updateMeta(
        {
            "name": event_title,
            "description": event_description,
            "rec_time": event_start_time,
            "service_reference": service_str,
            "length": event_length,
            "size": os.path.getsize(target_path)
        }
    )


def createXMetaFile(target_path, copy_begin_time, copy_end_time, event_start_time, event_duration):
    ParserMetaFile(target_path).updateXMeta(
        {
            "recording_start_time": copy_begin_time,
            "recording_stop_time": copy_end_time,
            "timer_start_time": event_start_time,
            "timer_stop_time": event_start_time + event_duration,
            "recording_margin_before": config.recording.margin_before.value * 60,
            "recording_margin_after": config.recording.margin_after.value * 60,
        }
    )


def createTXTFile(target_path, extended_event_description):
    logger.info("...")
    file_name = os.path.splitext(target_path)[0]
    writeFile(file_name + ".txt", extended_event_description)


def manageTimeshiftRecordings(session, plugin_id):
    plugin = getPlugin(WHERE_JOBCOCKPIT)
    if plugin:
        logger.debug("plugin.name: %s", plugin.name)
        plugin(session, plugin_id)
