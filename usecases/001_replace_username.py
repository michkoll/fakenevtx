from Workflow.ModifyStep import ModifyElementValueStep, ModifyEventdataStep
from Workflow.Workflow import *


def main(src, dest, old_username, new_username, new_sid):
    # initialize Workflow
    workflow = Workflow()

    # create subject username filter
    filter_subj = WorkflowStepFilter()
    filter_subj.add_eventdata_filter("SubjectUserName", old_username)
    # create and add step to workflow
    step_subj_sid = ModifyEventdataStep(filter_subj, new_value=new_sid, eventdata_name="SubjectUserSid")
    step_subj = ModifyEventdataStep(filter_subj, new_value=new_username, eventdata_name="SubjectUserName")
    workflow.add_step(step_subj_sid)
    workflow.add_step(step_subj)

    # create target username filter
    filter_target = WorkflowStepFilter()
    filter_target.add_eventdata_filter("TargetUserName", old_username)
    # create and add step to workflow
    step_target = ModifyEventdataStep(filter_target, new_value=new_username, eventdata_name="TargetUserName")
    step_target_sid = ModifyEventdataStep(filter_target, new_value=new_sid, eventdata_name="TargetUserSid")
    workflow.add_step(step_target_sid)
    workflow.add_step(step_target)

    # start workflow
    workflow.run(src, dest)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Replace a given username with new value.")
    parser.add_argument("src", type=str, help="Path to the source Windows EVTX event log file")
    parser.add_argument("dest", type=str, help="Path to the source Windows EVTX event log file")
    parser.add_argument("old_username", type=str, help="Old username")
    parser.add_argument("new_username", type=str, help="New username")
    parser.add_argument("new_sid", type=str, help="SID of new user")
    args = parser.parse_args()
    main(args.src, args.dest, args.old_username, args.new_username, args.new_sid)
