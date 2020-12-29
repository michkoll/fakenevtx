from Workflow.DeleteRecordStep import DeleteRecordStep
from Workflow.ModifyStep import ModifyElementValueStep, ModifyAttributeValueStep
from Workflow.Workflow import *

def main():
    workflow = Workflow()

    filter = WorkflowStepFilter()
    filter.add_system_filter("EventID", 4688)

    delfilter = WorkflowStepFilter()
    delfilter.add_system_filter("EventRecordID", "27240")



    step_one = ModifyElementValueStep(filter, "Evil", element_name="Data", attribute_name="Name", attribute_value="SubjectUserName")
    #workflow.add_step(step_one)

    step_two = ModifyAttributeValueStep(filter, "999", element_name="Execution", attribute_name="ProcessID")
    #workflow.add_step(step_two)

    step_three = DeleteRecordStep(delfilter)
    workflow.add_step(step_three)

    workflow.run("../tests/data/ex_001.evtx", "../tests/data/output.evtx")

if __name__ == "__main__":

    main()
