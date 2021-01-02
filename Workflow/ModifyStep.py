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

from Workflow import FilterUtils, NodeUtils, WriteUtils
from Workflow.Workflow import WorkflowStep

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ModifyElementValueStep(WorkflowStep):
    def __init__(self, evtx_filter, new_value, element_name=None, attribute_value=None, attribute_name=None):
        """
        This steps modies a value of one evtx element.

        :param evtx_filter: WorkflowStepFilter instance
        :param new_value: new value to write
        :param element_name: element name of target element
        :param attribute_value: attribute value of target element
        :param attribute_name: attribute name of target element
        """
        super().__init__(evtx_filter)

        self.new_value = new_value
        self.element_name = element_name
        self.attribute_name = attribute_name
        self.attribute_value = attribute_value

    def get_elements(self, record):
        """
        Gets elements from record, which will be manipulated by this step

        :param record: Record to be manipulated
        :return: Dictionary with BinXmlNode and RootNode
        """
        return FilterUtils.get_elements_from_record(record, self.attribute_name, self.attribute_value, self.element_name)

    def execute(self, record, element, root):
        """
        Executes the ModifyElementValueStep

        :param record: Record to be manipulated
        :param element: BinXmlNode to be manipulated
        :param root: RootNode of element
        """
        old_value_node = NodeUtils.get_element_value(element)
        old, new = WriteUtils.modify_value(self._dest_evtx, self.new_value, old_value_node, element, root, record)
        logger.info("Changed value of element <{0} {1}={2} from {3} to {4}".format(element.tag_name(), self.attribute_name, self.attribute_value, old, new))

    def check(self, dst_evtx, fast_check=True):
        """
        Validates the resulting evtx file

        :param dst_evtx: Resulting evtx file
        :param fast_check: Fast check ignores some resource intensive validating steps
        """
        super(ModifyElementValueStep, self).check(dst_evtx, fast_check)

    def __str__(self):
        return "{0}(new_value={1})".format(self.__class__.__name__, self.new_value)


class ModifyAttributeValueStep(ModifyElementValueStep):
    def __init__(self, evtx_filter, new_value, element_name=None, attribute_name=None):
        super(ModifyAttributeValueStep, self).__init__(evtx_filter, new_value, element_name=element_name, attribute_name=attribute_name)

    def execute(self, record, element, root):
        old_value_node = NodeUtils.get_attribute_value(element, attribute_name=self.attribute_name)
        old, new = WriteUtils.modify_value(self._dest_evtx, self.new_value, old_value_node, element, root, record)
        logger.info(
            "Changed value of element <{0} {1}={2} from {3} to {4}".format(element.tag_name(), self.attribute_name,
                                                                           self.attribute_value, old, new))


class ModifyEventdataStep(ModifyElementValueStep):
    def __init__(self, evtx_filter, new_value, eventdata_name):
        super(ModifyEventdataStep, self).__init__(evtx_filter, new_value, element_name="Data", attribute_name="Name", attribute_value=eventdata_name)


class ModifySystemdataStep(ModifyElementValueStep):
    def __init__(self, evtx_filter, new_value, systemdata_name):
        super(ModifySystemdataStep, self).__init__(evtx_filter, new_value, element_name=systemdata_name)


class ModifyTimestampStep(ModifyAttributeValueStep):
    def __init__(self, evtx_filter, new_value):
        super(ModifyTimestampStep, self).__init__(evtx_filter, new_value, element_name="TimeCreated", attribute_name="SystemTime")

class IncrementTimestampStep(ModifyTimestampStep):
    def __init__(self, evtx_filter, days=0, hours=0, minutes=0, seconds=0, microseconds=0):
        super(IncrementTimestampStep, self).__init__(evtx_filter, None)

        self.timedelta = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)

    def execute(self, record, element, root):
        old_value_node = NodeUtils.get_attribute_value(element, self.attribute_name)
        old_value = NodeUtils.get_readable_value(old_value_node, root)
        old_value_dt = datetime.datetime.strptime(old_value, "%Y-%m-%d %H:%M:%S.%f")
        self.new_value = old_value_dt + self.timedelta

        super(IncrementTimestampStep, self).execute(record, element, root)

class IncrementElementValueStep(ModifyElementValueStep):
    def __init__(self, evtx_filter, new_value, element_name=None, attribute_value=None, attribute_name=None):
        super(IncrementElementValueStep, self).__init__(evtx_filter, new_value, element_name=element_name, attribute_value=attribute_value, attribute_name=attribute_name)

    def execute(self, record, element, root):
        old_value_node = NodeUtils.get_element_value(element)
        old_value = NodeUtils.get_readable_value(old_value_node, root)

        try:
            new_value = int(old_value) + self.new_value
            self.new_value = new_value
        except:
            raise TypeError("Value could not be incremented.")

        super(IncrementElementValueStep, self).execute(record, element, root)


class IncrementAttributeValueStep(ModifyAttributeValueStep):
    def __init__(self, evtx_filter, new_value, element_name=None, attribute_name=None):
        super(IncrementAttributeValueStep, self).__init__(evtx_filter, new_value, element_name=element_name, attribute_name=attribute_name)

    def execute(self, record, element, root):
        old_value_node = NodeUtils.get_attribute_value(element, self.attribute_name)
        old_value = NodeUtils.get_readable_value(old_value_node, root)

        try:
            new_value = int(old_value) + self.new_value
            self.new_value = new_value
        except:
            raise TypeError("Value could not be incremented.")

        super(IncrementAttributeValueStep, self).execute(record, element, root)
