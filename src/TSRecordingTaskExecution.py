# pylint: disable=no-member
# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


import os
from time import time
from shlex import quote
from pathlib import Path
from enigma import eTimer
from Components.config import config
try:
    from Plugins.SystemPlugins.CacheCockpit.FileManager import FileManager
except Exception:
    FileManager = None
from .Debug import logger
from .TimeshiftUtils import calcRecordingTimes, createTXTFile, createMetaFile, createXMetaFile, createEitFile
from .MovieCoverDownloadUtils import downloadCover
from .Shell import Shell
from .ParserMetaFile import ParserMetaFile
from .TimeshiftUtils import formatTime


POLL_TIMEOUT = 1000 * 10


class TSRecordingTaskExecution(Shell):

    def __init__(self):
        logger.info("...")
        Shell.__init__(self)
        self.copy_begin_time = 0
        self.copy_end_time = 0
        self.poll_timer = eTimer()
        self.poll_timer.callback.append(self.waitTSRecording)

    def abortTSRecording(self):
        logger.info("...")
        self.poll_timer.stop()
        self.job.tasks[self.job.current_task].setProgress(0)
        self.abortShell()

    def stopTSRecording(self):
        logger.info("...")
        self.poll_timer.stop()
        self.copy_end_time = int(time())
        self.waitTSRecording(stop=True)

    def execTSRecording(self):
        logger.info("event_data: %s", self.event_data)
        Path(self.target_path).touch()  # create empty target file to avoid "file not found"
        self.copy_begin_time, self.copy_end_time = calcRecordingTimes(
            self.timeshift_start_time, self.event_start_time, self.event_duration)
        createMetaFile(self.service_ref.toString(), self.target_path, self.copy_begin_time,
                       self.event_title, self.event_description, self.copy_end_time - self.copy_begin_time)
        createXMetaFile(self.target_path, self.copy_begin_time,
                        self.copy_end_time, self.event_start_time, self.event_duration)
        createEitFile(self.service_ref.toString(),
                      self.target_path, self.event_id)
        if not os.path.exists(os.path.splitext(self.target_path)[0] + ".eit"):
            createTXTFile(self.target_path, self.event_extended_description)
        downloadCover(self.target_path, self.service_ref.toString(), self.event_start_time,
                      self.event_duration, config.plugins.timeshiftcockpit.cover_source.value, self.startTSRecording)

    def startTSRecording(self, target_path):
        logger.info("target_path: %s", target_path)
        if FileManager:
            FileManager.getInstance("MVC").loadDatabaseFile(target_path)
        logger.debug("timeshift recording starts...")
        self.poll_timer.start(POLL_TIMEOUT)
        self.waitTSRecording()

    def waitTSRecording(self, stop=False):
        logger.info("target_path: %s", self.target_path)
        logger.debug("copy_end_time: %s", formatTime(self.copy_end_time))
        logger.debug("now: %s", formatTime(int(time())))
        if stop or self.copy_end_time <= int(time()):
            logger.debug("timeshift recording ends...")
            self.poll_timer.stop()
            if not stop:
                self.updateProgress()
            self.copyTSRecording(
                self.timeshift_file_path, self.target_path, self.copy_begin_time, self.copy_end_time)
        else:
            logger.debug("timeshift recording still in progress...")
            self.updateProgress()

    def copyTSRecording(self, src, dst, begin_time, end_time):
        duration = end_time - begin_time
        begin = begin_time - self.timeshift_start_time
        logger.debug("begin: %s, duration: %s", begin, duration)
        cmds = []
        # Add -fflags +discardcorrupt before the input to try and skip corrupted parts
        cmds.append(f"ffmpeg -fflags +discardcorrupt -ss {begin} -i {quote(src)} -t {duration} -map 0 -y -c copy {quote(dst)} -ignore_unknown")
        createapscfiles = "/usr/lib/enigma2/python/Plugins/Extensions/TimeshiftCockpit/createapscfiles"
        cmds.append(f"{createapscfiles} {quote(dst)}")
        logger.debug("cmds: %s", cmds)
        self.execShell(cmds, src, dst)

    def execShellCallback(self, _path, target_path, error):
        logger.info("...")
        ParserMetaFile(target_path).updateMeta(
            {"size": os.path.getsize(self.target_path)})
        logger.debug("progress: %s", self.progress)
        self.execTSRecordingCallback(error)

    def updateProgress(self):
        self.progress = 0
        if self.copy_end_time and self.copy_begin_time:
            self.progress = min(int(round(float((time() - self.copy_begin_time)) / float((self.copy_end_time - self.copy_begin_time)) * 100)), 100)
        logger.debug("timeshift_file_path: %s, target_path: %s, progress: %d",
                     self.timeshift_file_path, self.target_path, self.progress)
        self.job.tasks[self.job.current_task].setProgress(self.progress)
