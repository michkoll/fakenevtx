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
import logging
from datetime import date

import Evtx.Evtx as evtx
from Evtx.Nodes import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def find_records(src_evtx, element_filter=None, eventdata_filter=None, minTime: date = None,
                 maxTime: date = None):
    found_records = []
    if isinstance(src_evtx, evtx.Evtx):
        for record in src_evtx.records():
            if find_elements(record, element_filter, eventdata_filter, minTime, maxTime):
                logger.debug("Found record {0} at ofs {1}".format(record.record_num(), record.offset()))
                found_records.append(record.record_num())

        logger.info("Found {0} records".format(len(found_records)))
    return found_records


def find_elements(record, element_filter, eventdata_filter, minTime, maxTime):
    def get_node(node):
        if isinstance(node, TemplateInstanceNode):
            if not get_node(node.template()):
                return False

        if isinstance(node, OpenStartElementNode):
            if node.tag_name() == "System":
                if not check_element_filter(element_filter, eventdata_filter, minTime, maxTime, node, record):
                    return False
            elif node.tag_name() == "EventData":
                if not check_eventdata_filter(element_filter, eventdata_filter, node, record):
                    return False

        for child in node.children():
            if not get_node(child):
                return False

        if isinstance(node, RootNode):
            for sub in node.substitutions():
                if isinstance(sub, VariantTypeNode):
                    if isinstance(sub, BXmlTypeNode):
                        # iterate through full BXmlTypeNode childs
                        if not find_elements(sub, element_filter, eventdata_filter, minTime, maxTime):
                            return False

        return True

    return get_node(record.root())


def check_element_filter(element_filter, eventdata_filter, minTime, maxTime, node, record):
    filter_count = 0

    if len(element_filter) == 0:
        return True

    for systemChild in node.children():
        if isinstance(systemChild, OpenStartElementNode) and systemChild.tag_name() in element_filter \
                and check_value(element_filter, eventdata_filter, systemChild, systemChild.tag_name(), record):
            filter_count += 1
        if isinstance(systemChild, OpenStartElementNode) and systemChild.tag_name() == "TimeCreated":
            if not check_timestamp_filter(minTime, maxTime, systemChild, record):
                return False

    if filter_count == len(element_filter):
        return True
    else:
        return False


def check_eventdata_filter(element_filter, eventdata_filter, node, record):
    subs = record.root().substitutions()
    filter_count = 0

    if eventdata_filter is None or len(eventdata_filter) == 0:
        return True

    for eventdataChild in node.children():  # data-tag
        for elementChild in eventdataChild.children():  # attributes
            if isinstance(elementChild, AttributeNode) and elementChild.attribute_name().string() == "Name":
                for attributeValueChild in elementChild.children():
                    if isinstance(attributeValueChild, ValueNode) and \
                            attributeValueChild.value().string() in eventdata_filter \
                            and check_value(element_filter, eventdata_filter, eventdataChild,
                                            attributeValueChild.value().string(), record):
                        filter_count += 1
                    elif (isinstance(attributeValueChild, ConditionalSubstitutionNode)
                          or isinstance(attributeValueChild, NormalSubstitutionNode)) \
                            and subs[attributeValueChild.index()].string() in eventdata_filter \
                            and check_value(element_filter, eventdata_filter, eventdataChild,
                                            subs[attributeValueChild.index()].string(),
                                            record):
                        filter_count += 1

    if filter_count == len(eventdata_filter):
        return True
    else:
        return False


def check_timestamp_filter(minTime, maxTime, node, record):
    subs = record.root().substitutions()

    for attributeChild in node.children():
        if isinstance(attributeChild, AttributeNode) and attributeChild.attribute_name().string() == "SystemTime":
            attribute_value = attributeChild.attribute_value()
            if isinstance(attribute_value, ConditionalSubstitutionNode) or isinstance(attribute_value,
                                                                                      NormalSubstitutionNode):
                time_created = subs[attribute_value.index()].filetime()
            elif isinstance(attribute_value, ValueNode):
                time_created = attribute_value.value().string().filetime()

    if (minTime is None or time_created > minTime) and \
            (maxTime is None or time_created < maxTime):
        # logger.debug("Record {3} IN time: minTime={0} timeCreated={1} maxTime={2}".format(minTime, time_created,maxTime, record.record_num()))
        return True
    else:
        logger.debug(
            "Record {3} NOT IN time: minTime={0} timeCreated={1} maxTime={2}".format(minTime, time_created, maxTime,
                                                                                     record.record_num()))
        return False


def check_value(element_filter, eventdata_filter, node, filter_value, record):
    subs = record.root().substitutions()

    for child in node.children():
        if isinstance(child, ConditionalSubstitutionNode) or isinstance(child, NormalSubstitutionNode):
            value = subs[child.index()]
        elif isinstance(child, ValueNode):
            value = child.value()

    if filter_value in element_filter and str(element_filter[filter_value]) == value.string():
        # logger.debug("Found System[{0}]={1} in Record (Offset {2})".format(filter_value, value.string(), record.offset()))
        return True
    elif filter_value in eventdata_filter and str(eventdata_filter[filter_value]) == value.string():
        # logger.debug("Found EventData[{0}]={1} in Record (Offset {2})".format(filter_value, value.string(), record.offset()))
        return True
    else:
        return False


def get_elements_from_record(record, attributeName=None, attributeValue=None, elementName=None):
    root = record.root()

    subs = root.substitutions()
    nodes = []

    def get_node(node):
        if isinstance(node, TemplateInstanceNode):
            # if node.is_resident_template():
            get_node(node.template())

        if isinstance(node, OpenStartElementNode):
            if node.tag_name() == elementName or elementName is None:
                if attributeName is None and attributeValue is None:
                    nodes.append([node, root])
                    logger.debug("Found node at ofs {0}".format(node.offset()))
                else:
                    for elementChild in node.children():
                        if isinstance(elementChild, AttributeNode):
                            if elementChild.attribute_name().string() == attributeName or attributeName is None:
                                for attributeValueChild in elementChild.children():
                                    if isinstance(attributeValueChild,
                                                  ValueNode) and attributeValueChild.value().string() == attributeValue or attributeValue is None:
                                        nodes.append([node, root])
                                        logger.debug("Found node at ofs {0}".format(node.offset()))
                                    if (isinstance(attributeValueChild, ConditionalSubstitutionNode) or isinstance(
                                            attributeValueChild, NormalSubstitutionNode)) and subs[
                                            attributeValueChild.index()].string() == attributeValue:
                                        nodes.append([node, root])
                                        logger.debug("Found node at ofs {0}".format(node.offset()))

        for child in node.children():
            get_node(child)

        if isinstance(node, RootNode):
            for sub in node.substitutions():
                if isinstance(sub, VariantTypeNode):
                    if isinstance(sub, BXmlTypeNode):
                        nodes.extend(get_elements_from_record(sub, attributeName, attributeValue,
                                                              elementName))

    get_node(root)
    return nodes
