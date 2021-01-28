#!/usr/bin/python
#    This file is part of syntheticevtx.
#
#   Copyright 2020 Michael Koll
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#   Version v. 1.0.0
#
import datetime
import logging
import os
import shutil
from abc import ABCMeta, abstractmethod

import Evtx.Evtx as evtx

from Workflow import FilterUtils

logPath = "./"
fileName = "workflow"

logging.basicConfig(
    format="%(asctime)s [%(name)-20.20s (%(funcName)-20.20s)] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.FileHandler("{0}/{1}.log".format(logPath, fileName)),
        logging.StreamHandler()
    ])

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Workflow(object):
    """
    Base workflow object for workflow execution. Manages prerequisites and controls step execution.
    """
    def __init__(self):
        self.steps = []

    def run(self, source_evtx_path, dest_evtx_path, fast_check=True, ignore_errors=True):
        """
        Executes all steps, which were added to the workflow.

        :param source_evtx_path: path to source (original) evtx file
        :param dest_evtx_path: path to result evtx file
        :param fast_check: Fast check steps over some inefficient validating steps
        :param ignore_errors: Ignores unhandled exceptions and tries to continue the workflow
        :return: True if successful, False if error
        """
        # check if source_evtx_path exists, copy source_evtx_path to dest_evtx_path
        if not os.path.isfile(source_evtx_path):
            raise FileNotFoundError(source_evtx_path)
        shutil.copy(source_evtx_path, dest_evtx_path)

        try:
            if self._validate(dest_evtx_path):
                for step in self.steps:
                    step.run(dest_evtx_path, fast_check=fast_check, ignore_errors=ignore_errors)
                return True
        except NotImplementedError as e:
            logger.error("NotImplementedError: " + e.args[0])
            return False

    def add_step(self, step):
        """
        Add step to workflow.

        :param step: WorkflowStep object
        :return: None
        """
        if not isinstance(step, WorkflowStep):
            raise TypeError("Must be of type WorkflowStep!")
        else:
            self.steps.append(step)

    def _validate(self, dest_evtx_path):
        with evtx.Evtx(dest_evtx_path) as evtx_to_check:
            fh = evtx_to_check.get_file_header()
            # check file header checksum
            if not fh.verify():
                logger.error("File header corrupt, processing not possible. Aborting ...")
                return False
            else:
                logger.debug("File header valid.")
            # check chunk header checksum
            for chunk in fh.chunks():
                if not chunk.verify():
                    logger.error(
                        "Chunk header @ofs={0} corrupt, processing not possible. Aborting ...".format(chunk.offset()))
                    return False
                else:
                    logger.debug("Chunk header @ofs={0} valid.".format(chunk.offset()))

            logger.info("Evtx file verified successfully.")
            return True


class WorkflowStep(metaclass=ABCMeta):

    def __init__(self, evtx_filter):
        """
        Initializes WorkflowStep.

        :param evtx_filter: WorkflowStepFilter object. The step ist executed to all records, that match this filter.
        """
        self._filter = evtx_filter
        self._source_evtx = None
        self._dest_evtx = None

    def run(self, dest_evtx, fast_check=True, record_id=None, ignore_errors=True):
        """
        Executes WorkflowStep. Begins with filtering the records and afterwards executes the step to all found records.

        :param dest_evtx: path to result evtx file
        :param fast_check: Fast check steps over some inefficient validating steps
        :param record_id: List of record ids. If provided, this list is used for execution and no filtering is done.
        :param ignore_errors: Ignores unhandled exceptions and tries to continue the workflow step
        :return:
        """
        logger.info("Starting step {0}".format(self.__class__.__name__))
        # search for records
        with evtx.Evtx(dest_evtx, readonly=False) as self._dest_evtx:
            if record_id is None:
                found_records = self.filter_records()
            else:
                found_records = [record_id]

        for record_id in found_records:
            # new initialization because of changes to mmap in last run
            with evtx.Evtx(dest_evtx, readonly=False) as self._dest_evtx:
                record = self._dest_evtx.get_record(record_id)
                try:
                    nodes = self.get_elements(record)

                    logger.info("Execute {1} for record {0}".format(record_id, self))
                    # executes steps based on manipulating concrete nodes
                    if nodes is not None:
                        for element, root in nodes:
                            self.execute(record, element, root)
                            self.repair_hash()
                    # executes steps based on records
                    else:
                        self.execute(record)
                except KeyError as e:
                    # ignore some specific parsing errors (e.g. EventID 4798) until error is fixed
                    logger.warning("Template {0} could not be found. Skipping record {1} and trying to continue ...".format(str(e), record_id))
                    logger.debug(e, exc_info=True)
                except Exception as e:
                    # quick and dirty error handling for unexcepted parsing or format errors
                    # activate DEBUG level logging for details
                    if ignore_errors:
                        logger.warning("An unhandled exception occured. Skipping record {0} and trying to continue ...".format(record_id))
                        logger.debug(e, exc_info=True)
                    else:
                        logger.warning("An unhandled exception occured at record {0}. Aborting ...".format(record_id))
                        raise

        # validates the result evtx file
        with evtx.Evtx(dest_evtx, readonly=False) as self._dest_evtx:
            self.check(self._dest_evtx, fast_check)

    def filter_records(self):
        logger.debug("Starting search for filter \n{0}".format(self._filter))
        return FilterUtils.find_records(self._dest_evtx, element_filter=self._filter.element_filter,
                                        eventdata_filter=self._filter.eventdata_filter,
                                        minTime=self._filter.min_time, maxTime=self._filter.max_time)

    @abstractmethod
    def get_elements(self, record):
        """
        Search elements, that will be manipulated.

        :param record: Evtx.Record object
        :return:
        """
        pass

    @abstractmethod
    def execute(self, record):
        """
        Executes the step

        :param record: Evtx.Record object
        :return:
        """
        pass

    @abstractmethod
    def check(self, dst_evtx, fast_check=True):
        """
        Validates the result evtx file and the successful manipulation.

        :param dst_evtx: Evtx object
        :param fast_check: Fast check steps over some inefficient validating steps
        :return:
        """
        fh = dst_evtx.get_file_header()
        # check file header checksum
        if not fh.verify():
            logger.error("file header checksum NOT valid")
        else:
            logger.info("file header checksum valid")

        if fast_check is not True:
            # check chunk header
            for chunk in fh.chunks():
                if not chunk.verify():
                    logger.error("chunk (ofs={0}) checksum failed".format(chunk.offset()))

    def repair_hash(self):
        for chunk in self._dest_evtx.chunks():
            chunk.repair_header()


class WorkflowStepFilter(object):
    def __init__(self):
        self.min_time = None
        self.max_time = None
        self.eventdata_filter = {}
        self.element_filter = {}

    def add_eventdata_filter(self, eventdata_name, element_value=None):
        """
        Adds a filter parameter for EventData fields.

        Args:
            eventdata_name: EventData field name (e.g. TargetUserName)
            element_value: Optional, if no value is given all records, which include a field with the name given, will be returned
        """
        self.eventdata_filter[eventdata_name] = element_value

    def add_system_filter(self, element_name, element_value):
        """
        Adds a filter parameter for SystemData fields
        Args:
            element_name: SystemData field name
            element_value: SystemData field value
        """
        self.element_filter[element_name] = element_value

    def set_min_time_filter(self, min_time):
        """
        Sets a minimum timestamp in the filter.

        Args:
            min_time: datetime object
        """
        if isinstance(min_time, datetime):
            self.min_time = min_time

    def set_max_time_filter(self, max_time):
        """
        Set a maximum timestamp in the filter

        Args:
            max_time: datetime object
        """
        if isinstance(max_time, datetime):
            self.max_time = max_time

    def __str__(self):
        filter_str = "Filter entries:\n"
        i = 0
        for k, v in self.element_filter.items():
            filter_str += "\t[{0}]: Element: {1} ==  {2}\n".format(i, k, v)
            i += 1
        for k, v in self.eventdata_filter.items():
            filter_str += "\t[{0}]: Eventdata: {1} == {2}\n".format(i, k, v)
            i += 1
        filter_str += "\tMin_time: {0} || Max_time: {1}\n".format(self.min_time, self.max_time)

        return filter_str
