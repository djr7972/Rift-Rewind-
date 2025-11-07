import aws_cdk as core
import aws_cdk.assertions as assertions

from lol_ai_recap.lol_ai_recap_stack import LolAiRecapStack

# example tests. To run these tests, uncomment this file along with the example
# resource in lol_ai_recap/lol_ai_recap_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = LolAiRecapStack(app, "lol-ai-recap")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
