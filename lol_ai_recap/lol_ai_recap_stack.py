from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_secretsmanager as secrets,
)
from constructs import Construct
from aws_cdk.aws_lambda_python_alpha import PythonFunction, PythonLayerVersion

class LolAiRecapStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self, "RawBucket",
            versioned=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=Stack.of(self).removal_policy.DESTROY,
            auto_delete_objects=True,
        )

        riot_secret = secrets.Secret(self, "RiotApiKey")

        ingest_fn = PythonFunction(
            self, "IngestFn",
            entry="src/ingest_lambda",
            index="app.py",
            handler="handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "RIOT_SECRET_ID": riot_secret.secret_name,
                "RIOT_REGION": "americas",
            }
        )

        bucket.grant_write(ingest_fn)
        riot_secret.grant_read(ingest_fn)

        api = apigw.LambdaRestApi(self, "HttpApi", handler=ingest_fn, proxy=False)
        ingest = api.root.add_resource("ingest")
        ingest.add_method("GET")  # GET /ingest?puuid=...

        # Least-privilege add-ons for logs
        ingest_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
            resources=["*"]
        ))
