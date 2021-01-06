from Workflow.DeleteRecordStep import DeleteRecordStep
from Workflow.Workflow import *

def main(src, dest, username):
    # initialize Workflow
    workflow = Workflow()

    # create target username and eventid filter
    filter_subj = WorkflowStepFilter()
    filter_subj.add_eventdata_filter("TargetUserName", username)
    filter_subj.add_system_filter("EventID", "4624")
    # create and add step to workflow
    step = DeleteRecordStep(filter_subj)
    workflow.add_step(step)

    # start workflow
    workflow.run(src, dest)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Deletes logon events for specified account")
    parser.add_argument("src", type=str, help="Path to the source Windows EVTX event log file")
    parser.add_argument("dest", type=str, help="Path to the destination Windows EVTX event log file")
    parser.add_argument("username", type=str, help="Account name of user")
    args = parser.parse_args()
    main(args.src, args.dest, args.username)
