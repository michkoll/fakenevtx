import hashlib
import datetime

from fixtures import *
import Evtx.Evtx as evtx

from Workflow.DeleteRecordStep import DeleteRecordStep
from Workflow.ModifyStep import *
from Workflow.Workflow import *
from Workflow.FilterUtils import *

def test_ModifyElementValueStep(src_evtx_001, filter_single_record):
    wf = Workflow()
    element_name = "Data"
    attribute_value = "SubjectUserName"
    new_value = "Evil"
    step = ModifyElementValueStep(filter_single_record, new_value, element_name=element_name, attribute_value=attribute_value)
    wf.add_step(step)
    wf.run(src_evtx_001[0], src_evtx_001[1])

    with evtx.Evtx(src_evtx_001[1]) as output:
        fh = output.get_file_header()

        # check header
        assert fh.verify() is True

        # check new value
        assert helper_get_value(output, filter_single_record.element_filter, filter_single_record.eventdata_filter,
                                element_name=element_name, attribute_value=attribute_value) == new_value


def test_ModifyEventdataStep(src_evtx_001, filter_single_record):
    wf = Workflow()
    eventdata_name = "SubjectDomainName"
    new_value = "EvilDomain"
    step = ModifyEventdataStep(filter_single_record, new_value, eventdata_name)
    wf.add_step(step)
    wf.run(src_evtx_001[0], src_evtx_001[1])

    with evtx.Evtx(src_evtx_001[1]) as output:
        fh = output.get_file_header()

        # check header
        assert fh.verify() is True

        # check new value
        assert helper_get_value(output, filter_single_record.element_filter, filter_single_record.eventdata_filter,
                                element_name="Data", attribute_value=eventdata_name) == new_value

def test_ModifyAttributeValueStep(src_evtx_001, filter_single_record):
    wf = Workflow()
    element_name = "Execution"
    attribute_name = "ProcessID"
    new_value = "666"
    step = ModifyAttributeValueStep(filter_single_record, new_value,element_name=element_name, attribute_name=attribute_name)
    wf.add_step(step)
    wf.run(src_evtx_001[0], src_evtx_001[1])

    with evtx.Evtx(src_evtx_001[1]) as output:
        fh = output.get_file_header()

        # check header
        assert fh.verify() is True

        # check new value
        assert helper_get_value(output, filter_single_record.element_filter, filter_single_record.eventdata_filter,
                                element_name=element_name, attribute_name=attribute_name, attribute=True) == new_value

def test_ModifyEventdataStep(src_evtx_001, filter_single_record):
    wf = Workflow()
    systemdata_name = "EventID"
    new_value = "9999"
    step = ModifySystemdataStep(filter_single_record, new_value, systemdata_name=systemdata_name)
    wf.add_step(step)
    wf.run(src_evtx_001[0], src_evtx_001[1])

    with evtx.Evtx(src_evtx_001[1]) as output:
        fh = output.get_file_header()

        # check header
        assert fh.verify() is True

        # check new value
        assert helper_get_value(output, filter_single_record.element_filter, filter_single_record.eventdata_filter,
                                element_name=systemdata_name) == new_value

def test_ModifyTimestampStep(src_evtx_001, filter_single_record):
    wf = Workflow()
    new_value = datetime.datetime(1900,11,11,11,11,11,11, tzinfo=datetime.timezone.utc)
    step = ModifyTimestampStep(filter_single_record, new_value)
    wf.add_step(step)
    wf.run(src_evtx_001[0], src_evtx_001[1])

    with evtx.Evtx(src_evtx_001[1]) as output:
        fh = output.get_file_header()

        # check header
        assert fh.verify() is True

        # check new value
        assert helper_get_value(output, filter_single_record.element_filter, filter_single_record.eventdata_filter,
                                element_name="TimeCreated", attribute_name="SystemTime", attribute=True) == "1900-11-11 11:11:11.000011"

def test_IncrementElementValueStep(src_evtx_001, filter_single_record):
    wf = Workflow()
    element_name = "EventID"
    new_value = -1
    step = IncrementElementValueStep(filter_single_record, new_value, element_name=element_name)
    wf.add_step(step)
    wf.run(src_evtx_001[0], src_evtx_001[1])

    with evtx.Evtx(src_evtx_001[1]) as output:
        fh = output.get_file_header()

        # check header
        assert fh.verify() is True

        # check new value
        assert helper_get_value(output, filter_single_record.element_filter, filter_single_record.eventdata_filter,
                                element_name="EventID") == "4687"


def test_IncrementAttributeValueStep(src_evtx_001, filter_single_record):
    wf = Workflow()
    element_name = "Execution"
    attribute_name = "ProcessID"
    new_value = 1
    step = IncrementAttributeValueStep(filter_single_record, new_value, element_name=element_name, attribute_name=attribute_name)
    wf.add_step(step)
    wf.run(src_evtx_001[0], src_evtx_001[1])

    with evtx.Evtx(src_evtx_001[1]) as output:
        fh = output.get_file_header()

        # check header
        assert fh.verify() is True

        # check new value
        assert helper_get_value(output, filter_single_record.element_filter, filter_single_record.eventdata_filter,
                                element_name=element_name, attribute_name=attribute_name, attribute=True) == "5"

def test_DeleteRecordStep(src_evtx_001, filter_single_record_without_res_template):
    wf = Workflow()
    step = DeleteRecordStep(filter_single_record_without_res_template)
    wf.add_step(step)
    wf.run(src_evtx_001[0], src_evtx_001[1])

    with evtx.Evtx(src_evtx_001[1]) as output:
        fh = output.get_file_header()

        # check header
        assert fh.verify() is True

        # check new value
        #TODO check



def helper_get_value(test_evtx, element_filter, eventdata_filter, element_name = None, attribute_name = None, attribute_value = None, attribute=False):
    records = FilterUtils.find_records(test_evtx, element_filter=element_filter,
                                       eventdata_filter=eventdata_filter)
    fh = test_evtx.get_file_header()
    nodes = FilterUtils.get_elements_from_record(fh.get_record(records[0]), elementName=element_name,
                                                 attributeValue=attribute_value, attributeName=attribute_name)
    if attribute is True:
        element = NodeUtils.get_attribute_value(nodes[0][0], attribute_name=attribute_name)
    else:
        element = NodeUtils.get_element_value(nodes[0][0])
    value = NodeUtils.get_readable_value(element, nodes[0][1])
    return value



