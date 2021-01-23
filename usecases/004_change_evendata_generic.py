from Workflow.ModifyStep import ModifyTimestampStep, IncrementTimestampStep, ModifyEventdataStep
from Workflow.Workflow import *


def main(src, dest, field, old_value, new_value):
    # initialize Workflow
    workflow = Workflow()

    # create filter
    filter = WorkflowStepFilter()
    filter.add_eventdata_filter(eventdata_name=field, element_value=old_value)
    # create and add step to workflow
    step = ModifyEventdataStep(filter, new_value, field)
    workflow.add_step(step)

    # start workflow
    workflow.run(src, dest)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Replace all old values in a specific eventdata field")
    parser.add_argument("src", type=str, help="Path to the source Windows EVTX event log file")
    parser.add_argument("dest", type=str, help="Path to the destination Windows EVTX event log file")
    parser.add_argument("field", type=str, help="Name of the Eventdata field (e.g. SubjectUserName)")
    parser.add_argument("old_value", type=str, help="old value")
    parser.add_argument("new_value", type=str, help="new value")


    args = parser.parse_args()
    main(args.src, args.dest, args.field, args.old_value, args.new_value)
