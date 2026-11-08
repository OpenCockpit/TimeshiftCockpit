# Copyright (C) 2018-2026 by xcentaurix
# License: GNU General Public License v3.0


from shlex import quote
from enigma import eConsoleAppContainer
from .Debug import logger
from .TimeshiftUtils import ERROR_NONE, ERROR_ABORT


class Shell():

    def __init__(self):
        logger.info("...")
        self.container = eConsoleAppContainer()
        self.container.appClosed.append(self.finished)
        self.__abort = False

    def execShellCallback(self, _path, _target_path, _error):
        logger.error("should be overridden in child class")

    def execShell(self, scripts, path, target_path):
        logger.info("path: %s, target_path: %s, scripts: %s",
                    path, target_path, scripts)
        self.path = path
        self.target_path = target_path
        self.__abort = False
        script = '; '.join(scripts)
        self.container.execute("sh -c " + quote(script))

    def finished(self, retval=None):
        logger.info("retval = %s, __abort: %s", retval, self.__abort)
        if not self.__abort:
            self.execShellCallback(self.path, self.target_path, ERROR_NONE)
        else:
            logger.error("container finished despite abort")

    def abortShell(self):
        logger.info("...")
        self.__abort = True
        if self.container and self.container.running():
            self.container.kill()
            self.container = None
        else:
            logger.debug("aborting before container has started execution...")
        self.execShellCallback(self.path, self.target_path, ERROR_ABORT)
