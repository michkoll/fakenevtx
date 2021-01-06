from Workflow.ModifyStep import ModifyTimestampStep, IncrementTimestampStep
from Workflow.Workflow import *

def main(src, dest, eventrecordid, days, hours, minutes, seconds, microseconds):
    # initialize Workflow
    workflow = Workflow()

    # create eventrecordid filter
    filter_subj = WorkflowStepFilter()
    filter_subj.add_system_filter("EventRecordID", eventrecordid)
    # create and add step to workflow
    step = IncrementTimestampStep(filter_subj, days=days, hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)
    workflow.add_step(step)

    # start workflow
    workflow.run(src, dest)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Changes the time generated of a given record")
    parser.add_argument("src", type=str, help="Path to the source Windows EVTX event log file")
    parser.add_argument("dest", type=str, help="Path to the destination Windows EVTX event log file")
    parser.add_argument("eventrecordid", type=str, help="Event record id")
    parser.add_argument("--days", type=int, default=0, help="Increment/Decrement days")
    parser.add_argument("--hours", type=int, default=0, help="Increment/Decrement days")
    parser.add_argument("--minutes", type=int, default=0, help="Increment/Decrement days")
    parser.add_argument("--seconds", type=int, default=0, help="Increment/Decrement days")
    parser.add_argument("--microseconds", type=int, default=0, help="Increment/Decrement days")
    args = parser.parse_args()
    main(args.src, args.dest, args.eventrecordid, args.days, args.hours, args.minutes, args.seconds, args.microseconds)
