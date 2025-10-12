import os, boto3
print("PROFILE:", os.getenv("AWS_PROFILE"), "REGION:", os.getenv("AWS_REGION"))
print("STS:", boto3.client("sts").get_caller_identity())
print("Models:", len(boto3.client("bedrock", region_name=os.getenv("AWS_REGION","us-west-2")).list_foundation_models()["modelSummaries"]))
