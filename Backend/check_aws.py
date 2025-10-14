import os, boto3
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).with_name(".env"))
except Exception as e:
    print(f"Note: .env not loaded: {e}")

print("PROFILE:", os.getenv("AWS_PROFILE"), "REGION:", os.getenv("AWS_REGION"))
print("\n" + "=" * 60)
print("Checking AWS Bedrock Access")
print("=" * 60 + "\n")

try:
    # STS Identity
    sts = boto3.client("sts")
    identity = sts.get_caller_identity()
    print(f"✓ Authenticated as: {identity['Arn']}")
    print(f"  Account: {identity['Account']}\n")

    # Bedrock Models
    region = os.getenv("AWS_REGION", "us-west-2")
    bedrock = boto3.client("bedrock", region_name=region)

    all_models = bedrock.list_foundation_models()["modelSummaries"]
    print(f"✓ Total models in {region}: {len(all_models)}\n")

    # Filter Claude models
    claude_models = [m for m in all_models if "claude" in m.get("modelId", "").lower()]

    print(f"Available Claude Models ({len(claude_models)}):")
    print("-" * 60)
    for model in sorted(claude_models, key=lambda x: x['modelId']):
        model_id = model['modelId']
        print(f"  {model_id}")

    print("\n" + "=" * 60)
    print("Copy one of the above model IDs to your .env file")
    print("=" * 60)

except Exception as e:
    print(f"✗ Error: {e}")