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

import Evtx.Evtx as evtx
from Evtx.Nodes import *
from Evtx.Nodes import TemplateNode, TemplateInstanceNode, OpenStartElementNode, AttributeNode, EntityReferenceNode, \
    ProcessingInstructionTargetNode, RootNode, VariantTypeNode, BXmlTypeNode

from Workflow import CommonUtils, NodeUtils
from Workflow.NodeUtils import logger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def modify_value(src_evtx, new_value, value_node, element_node, root_node, record):
    if isinstance(value_node, ConditionalSubstitutionNode) or isinstance(value_node, NormalSubstitutionNode):
        subs = root_node.substitutions()  # substitution array for value
        value_offset = subs[value_node.index()].offset()  # offset to value in substition array
        old_value_length = subs[value_node.index()].length()  # length of old value
        old_value = subs[value_node.index()]  # old value
        old_value_cache = old_value.string()

        if isinstance(old_value, WstringTypeNode) or isinstance(old_value, StringTypeNode) or isinstance(old_value,
                                                                                                         SIDTypeNode):
            new_value_length = CommonUtils.get_new_value_length(old_value, new_value)  # calc new length
            # proactively change all offsets and sizes for integrity
            repair_offsets(src_evtx, new_value_length - old_value_length, value_offset, element_node, record)
            repair_sizes(new_value_length - old_value_length, value_offset, element_node, record)
            # get offset to substitution value
            sub_value_ofs = root_node.absolute_offset(root_node.tag_and_children_length()) + 4 + 4 * (
                value_node.index())
            src_evtx.get_file_header().pack_word(sub_value_ofs, new_value_length)
            if isinstance(old_value, SIDTypeNode):
                # move buffer for new length
                old_value.move_buffer(old_value_length, new_value_length)

        # write value to node
        old_value.set_value(new_value)
        return old_value_cache, new_value

    elif isinstance(value_node, ValueNode):
        old_value = value_node.value()
        old_value_cache = old_value.string()
        new_value_length = CommonUtils.get_new_value_length(old_value, new_value)  # calc new length
        if isinstance(old_value, WstringTypeNode):
            # string_length() * 2 because of size field in case of ValueNode
            repair_offsets(src_evtx, new_value_length - old_value.string_length() * 2, old_value.offset(), element_node,
                           record)
            repair_sizes(new_value_length - old_value.string_length() * 2, old_value.offset(), element_node, record)
            element_node.set_field("dword", "size",
                                   element_node.size() + new_value_length - old_value.string_length() * 2)
            old_value.set_value(new_value, old_value.string_length() * 2)
            return old_value_cache, new_value
        elif isinstance(old_value, StringTypeNode):
            # string_length() * 2 because of size field in case of ValueNode
            repair_offsets(src_evtx, new_value_length - old_value.string_length(), old_value.offset(), element_node,
                           record)
            repair_sizes(new_value_length - old_value.string_length(), old_value.offset(), element_node, record)
            element_node.set_field("dword", "size", element_node.size() + new_value_length - old_value.string_length())
            old_value.set_value(new_value, old_value.string_length())
            return old_value_cache, new_value
        else:
            old_value.set_value(new_value)
            return old_value_cache, new_value
    else:
        raise NotImplementedError("No modification of {0} implemented!".format(type(value_node)))


def repair_offsets(src_evtx, offset_diff, offset_change, element, record, repair_header=True,
                   repair_template_offset=None):
    logger.debug("Offset modification for change at ofs {0}, diff {1}".format(offset_change, offset_diff))
    # Repair chunk header offsets
    chunk = record.chunk()

    if repair_header:
        chunk.repair_header(ofs_change=offset_change, ofs_diff=offset_diff)
        # Repair chunk header string and template tables
        chunk.repair_tables(offset_change, offset_diff)

    # Repair
    def change_offsets(node):

        if isinstance(node, TemplateNode):
            if int(node.offset()) < offset_change < int(node.offset() + node.data_length()):
                node.set_field("dword", "data_length", node.data_length() + offset_diff)

        if isinstance(node, TemplateInstanceNode):
            # TODO: BinXmlTemplateDefinition template definition data offset, next template definition offset, data size
            if node.is_resident_template():
                change_offsets(node.template())
            if int(node.template_offset() + chunk.offset()) > offset_change:
                node.set_field("dword", "template_offset", node.template_offset() + offset_diff)
            # if resident template offsets in template definition has to be repaired

        # changes BinXMLNameString-Offsets in Elements, Attributes, Entities and PINodes
        if (isinstance(node, OpenStartElementNode)
            or isinstance(node, AttributeNode)
            or isinstance(node, EntityReferenceNode)
            or isinstance(node, ProcessingInstructionTargetNode)) \
                and int(node.string_offset() + chunk.offset()) > offset_change:
            node.set_field("dword", "string_offset", node.string_offset() + offset_diff)

        # iterate through all child elements
        for child in node.children():
            change_offsets(child)

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
                        # if change offset is in sub node, change length field in template instance table
                        if sub.offset() < offset_change < sub.offset() + sub.length():
                            struct.pack_into("<H", src_evtx._buf, sub_value_ofs, sub_length + offset_diff)
                        # change offsets in subnode itself
                        change_offsets(sub)
                        # change offsets in parent RootNode (Fragment) of BinXMLNode
                        change_offsets(sub._root)

    # iterate over all records
    for recordSub in chunk.records():
        logger.debug("Iterating over record {0}".format(recordSub.offset()))
        change_offsets(recordSub.root())


def repair_sizes(offset_diff, value_offset, element, record):
    # copy size field is shifted because of changed value
    for cur_record in record.chunk().records():
        old_size = cur_record.size()
        if cur_record.offset() < value_offset < cur_record.offset() + old_size:
            cur_record.set_field("dword", "size", old_size + offset_diff)
            cur_record.set_field("dword", "size2", old_size + offset_diff)


def prepare_resident_template_moving(src_evtx, old_record, resident_template_nodes):
    chunk = old_record.chunk()
    fh = src_evtx.get_file_header()
    # TODO update TemplateTable
    # TODO update record size
    # TODO update References to Template (Offsets)
    if not isinstance(src_evtx, evtx.Evtx):
        logger.error("No evtx provided. Aborting...")
        raise TypeError("No evtx provided. Aborting...")

    # for each resident template node in original record
    reference_template_nodes_per_template = {}
    for template_instance_node in resident_template_nodes:
        if isinstance(template_instance_node, TemplateInstanceNode):
            template_node = template_instance_node.template()
            template_id = template_node.template_id()
            template_length = template_node.data_length()

            # find templates referring to current resident template
            reference_template_nodes = {}
            for cur_record in chunk.records():
                if cur_record.record_num() > old_record.record_num():
                    tmp_reference_template_nodes = NodeUtils.has_resident_template(cur_record, find_residents=False,
                                                                                   find_non_residents=True,
                                                                                   template_id=template_id)
                    if len(tmp_reference_template_nodes) > 0:
                        reference_template_nodes[cur_record.record_num()] = tmp_reference_template_nodes

            reference_template_nodes_per_template[template_id] = reference_template_nodes

            # TODO copy from target to src
    for a, b in reference_template_nodes_per_template.items():
        # target record for resident template is first record referring to old resident template
        target_record = fh.get_record(min(b.keys()))
        target_template = b[target_record.record_num()][0]
        # TODO calculate new
        new_template_offset = target_template.offset() + target_template._off_template_offset + 4 - chunk.offset()
        for k, v in b.items():
            for ref_template_node in v:
                if isinstance(ref_template_node, TemplateInstanceNode):
                    ref_template_node.set_field("dword", "template_offset", new_template_offset)
                    continue

    pass
