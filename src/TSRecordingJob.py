# pylint: disable=no-member
# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0

from Components.Task import Job
from Plugins.SystemPlugins.JobCockpit.JobSupervisor import JobSupervisor
from .Debug import logger
from .TSRecordingTask import TSRecordingTask
from .Version import ID
from .__init__ import _


class TSRecordingJob():

    def __init__(self):
        self.job_manager = JobSupervisor.getInstance().getJobManager(ID)

    def addTSRecordingJob(self, event_data, service_ref):
        logger.info("Adding timeshift recording job...")
        logger.debug("event_data: %s", event_data)
        logger.debug("timeshift_file_path: %s", self.timeshift_file_path)
        logger.debug("service_ref_str: %s", service_ref.toString())
        job = Job(f"{_('TS recording')} - {event_data[2]}")
        job.keep = True
        TSRecordingTask(job, self.infobar_instance, service_ref,
                        self.timeshift_file_path, self.timeshift_start_time, event_data)
        self.job_manager.AddJob(job)
