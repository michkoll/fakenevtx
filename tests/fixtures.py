import os
import os.path
import contextlib

import pytest

from Workflow.Workflow import WorkflowStepFilter


@pytest.fixture
def filter_single_record():
    filter = WorkflowStepFilter()
    filter.add_system_filter("EventRecordID", "27240")
    return filter

@pytest.fixture
def filter_single_record_without_res_template():
    filter = WorkflowStepFilter()
    filter.add_system_filter("EventRecordID", "27256")
    return filter


@pytest.fixture
def src_evtx_001():
    cd = os.path.dirname(__file__)
    datadir = os.path.join(cd, 'data')
    evtxPath = os.path.join(datadir, 'ex_001.evtx')
    outputPath = os.path.join(datadir, 'output.evtx')
    return evtxPath, outputPath

