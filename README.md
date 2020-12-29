# FakeNevtx

[![Build Status](https://travis-ci.com/michkoll/fakenevtx.png?branch=main)](https://travis-ci.com/michkoll/fakenevtx)

FakeNevtx is a Python package for manipulating Windows Event Logs (EVTX files). It offers the possibility to change entries in EVTX records and to delete whole records.

The project was created as part of a master thesis. The purpose of this project was to remove unwanted artifacts from forensic training samples. 

## Features

* Manipulate values in evtx records (e.g. replace text values or change timestamps)
* Delete records from evtx files without leaving any artifacts
* workflow based configuration and execution of manipulation
* evtx files are sanitized after manipulation, the result is always a valid evtx file

## Installation

For installation clone this repo with its submodule, install all requirements and start producing FakeNevtx.

```shell
# clone repository
git clone clone --recurse-submodules https://github.com/michkoll/fakenevtx.git

# create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# install requirements
pip install requirements.txt
```

## Using

The listing below is a short example of how to implement and use FakeNevtx. The example shows a workflow which replaces all ```SubjectUserName``` values in ```4688``` events (Process Creation) with the value ```Evil```.


```python
from Workflow.ModifyStep import ModifyElementValueStep
from Workflow.Workflow import *

def main():
    # initialize Workflow
    workflow = Workflow()

    # create filter
    filter = WorkflowStepFilter()
    filter.add_system_filter("EventID", 4688)

    # create and add step to workflow
    step = ModifyElementValueStep(filter, new_value="Evil", element_name="Data", attribute_name="Name", attribute_value="SubjectUserName")
    workflow.add_step(step)

    # start workflow
    workflow.run("../tests/data/ex_001.evtx", "../tests/data/output.evtx")

if __name__ == "__main__":
    main()

```

You can find more examples and use cases here: [Use Cases](usecases/)

## Restrictions

As of now there are some restrictions for manipulation:
* records with resident templates (typicalle at the beginning of chunks) cannot be deleted. The handling of resident templates will be implemented in future versions
* when changing timestamps or EventRecordIDs, the records are not reordered because of the difficult handling of resident templates. Hopefully another future feature

## License

FakeNevtx is licensed under the Apache License, Version 2.0. This means it is freely available for use and modification in a personal and professional capacity.

Special thanks to
* Willi Ballenthin, the author of [python-evtx](https://github.com/williballenthin/python-evtx)
* Joachim Metz, for reversing and documenting the evtx structure and data types (see [here](https://github.com/libyal/libevtx/blob/main/documentation/Windows%20XML%20Event%20Log%20(EVTX).asciidoc))
