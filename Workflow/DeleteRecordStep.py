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

from Workflow import FilterUtils, NodeUtils, WriteUtils
from Workflow.Workflow import WorkflowStep

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DeleteRecordStep(WorkflowStep):

    def __init__(self, evtx_filter, repair_eventrecord_id=True):
        super(DeleteRecordStep, self).__init__(evtx_filter)

        self.repair_eventrecord_id = repair_eventrecord_id

    def get_elements(self, record):
        pass

    def execute(self, record):

        record_size = record.length()
        chunk = record.chunk()
        fh = self._dest_evtx.get_file_header()

        move_template = False

        # TODO Removing of residents templates
        resident_templates = NodeUtils.has_resident_template(record)
        if len(resident_templates) > 0:
            # TODO implement resident template steps
            # read EventID from record to be deleted
            #WriteUtils.prepare_resident_template_moving(self._dest_evtx, record, resident_templates)

            # TODO copy template to new position
            # TODO reload EVTX?

            raise NotImplementedError("Records with resident templates cannot be deleted.")

        for cur_chunk in fh.chunks():
            for cur_record in cur_chunk.records():
                if cur_record.record_num() > record.record_num():
                    # repair field EventRecordId
                    if self.repair_eventrecord_id:
                        element, root = FilterUtils.get_elements_from_record(record, elementName="EventRecordID")[0]
                        old_value_node = NodeUtils.get_element_value(element)
                        old_value = NodeUtils.get_readable_value(old_value_node, root)
                        old, new = WriteUtils.modify_value(self._dest_evtx, int(old_value) - 1, old_value_node, element, root, record)

                    # repair internal record number
                    cur_record.set_field("qword", "record_num", cur_record.record_num() - 1)

            if cur_chunk.file_last_record_number() > record.record_num():
                cur_chunk.set_field("qword", "file_last_record_number", cur_chunk.file_last_record_number() - 1)
            if cur_chunk.file_first_record_number() > record.record_num():
                cur_chunk.set_field("qword", "file_first_record_number", cur_chunk.file_first_record_number() - 1)
            if cur_chunk.log_last_record_number() > record.record_num():
                cur_chunk.set_field("qword", "log_last_record_number", cur_chunk.log_last_record_number() - 1)
            if cur_chunk.log_first_record_number() > record.record_num():
                cur_chunk.set_field("qword", "log_first_record_number", cur_chunk.log_first_record_number() - 1)
            cur_chunk.repair_header()

        WriteUtils.repair_offsets(self._dest_evtx, record_size * -1, record.offset(), None, record, repair_header=False)

        # delete record
        record.move_buffer(record_size, 0, max_offset=chunk.offset() + 65536, fill_zero=True)

        # repair chunk header
        chunk.repair_tables(record.offset(), record_size * -1)
        chunk.repair_header(record.offset(), record_size * -1)
        fh.set_field("qword", "next_record_number", fh.next_record_number() - 1)
        fh.repair_checksum()

    def check(self, dst_evtx, fast_check=True):
        super(DeleteRecordStep, self).check(dst_evtx, fast_check)

