from Workflow.ModifyStep import ModifyTimestampStep
from Workflow.Workflow import *

def main(src, dest, eventrecordid, new_timestamp):
    # initialize Workflow
    workflow = Workflow()

    # create eventrecordid filter
    filter_subj = WorkflowStepFilter()
    filter_subj.add_system_filter("EventRecordID", eventrecordid)
    # create and add step to workflow
    step = ModifyTimestampStep(filter_subj, datetime.datetime.strptime(new_timestamp, "%Y-%m-%d %H:%M:%S"))
    workflow.add_step(step)

    # start workflow
    workflow.run(src, dest)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Changes the time generated of a given record")
    parser.add_argument("src", type=str, help="Path to the source Windows EVTX event log file")
    parser.add_argument("dest", type=str, help="Path to the source Windows EVTX event log file")
    parser.add_argument("eventrecordid", type=str, help="Event record id")
    parser.add_argument("new_timestamp", type=str, help="new timestamp for record in format YYYY-mm-dd HH:MM:SS")
    args = parser.parse_args()
    main(args.src, args.dest, args.eventrecordid, args.new_timestamp)
