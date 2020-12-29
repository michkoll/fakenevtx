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
import struct

from Evtx.Nodes import OpenStartElementNode, ValueNode, NormalSubstitutionNode, ConditionalSubstitutionNode, \
    AttributeNode, RootNode, VariantTypeNode, BXmlTypeNode, TemplateInstanceNode

from Workflow import FilterUtils

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_element_value(node):
    if isinstance(node, OpenStartElementNode):
        for child in node.children():
            if isinstance(child, ValueNode):
                return child
            if isinstance(child, NormalSubstitutionNode) or isinstance(child, ConditionalSubstitutionNode):
                return child
    else:
        raise TypeError("Wrong type. OpenStartElementNode needed")


def get_attribute_value(node, attribute_name):
    if isinstance(node, OpenStartElementNode):
        for child in node.children():
            if isinstance(child, AttributeNode) and child.attribute_name().string() == attribute_name:
                return child.attribute_value()
    else:
        raise TypeError("Wrong type. OpenStartElementNode needed")


def get_readable_value(variant_node, root_node):
    if isinstance(variant_node, ConditionalSubstitutionNode) or isinstance(variant_node, NormalSubstitutionNode):
        subs = root_node.substitutions()
        return subs[variant_node.index()].string()
    if isinstance(variant_node, ValueNode):
        return variant_node.value().string()


def get_readable_element_value_from_record(record, element_name):
    elements = FilterUtils.get_elements_from_record(record, elementName=element_name)
    # reads only first entry
    element = elements[0][0]
    root_node = elements[0][1]
    if isinstance(element, OpenStartElementNode):
        eventid_valuenode = get_element_value(element)
        return get_readable_value(eventid_valuenode, root_node)


def has_resident_template(record, find_residents=True, find_non_residents=False, template_id=0):
    """
    Check if record has resident template.

    :param template_id:
    :param find_non_residents:
    :param find_residents:
    :param record: Event record
    :return: True if resident template in record, otherwise False.
    """
    chunk = record._chunk
    template_instance_nodes = []

    def find_template(node):
        if isinstance(node, TemplateInstanceNode):
            if node.is_resident_template():
                if find_residents and (node.template_id() == template_id or template_id == 0):
                    template_instance_nodes.append(node)
            else:
                if find_non_residents and (node.template_id() == template_id or template_id == 0):
                    template_instance_nodes.append(node)
        # iterate through all child elements
        for child in node.children():
            find_template(child)

        # if node is RootNode check substitution table for necessary offset changes
        if isinstance(node, RootNode):
            sub_value_ofs_length = 0
            # iterate over all sub nodes in table
            for sub in node.substitutions():
                sub_index = node.substitutions().index(sub)
                # offset of substitution value
                sub_value_ofs = node.absolute_offset(node.tag_and_children_length()) + 4 + 4 * (
                    sub_index)
                # length of substitution value
                sub_length = struct.unpack_from("<H", node._buf, sub_value_ofs)[0]
                sub_value_ofs_length += sub_length
                if isinstance(sub, VariantTypeNode):
                    if isinstance(sub, BXmlTypeNode):
                        # change offsets in subnode itself
                        template_instance_nodes.extend(has_resident_template(sub, find_residents=find_residents,
                                                                             find_non_residents=find_non_residents,
                                                                             template_id=template_id))

    # iterate over all records
    find_template(record.root())
    return template_instance_nodes
