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
