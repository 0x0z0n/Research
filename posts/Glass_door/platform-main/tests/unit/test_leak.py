import boto3
import os

def test_leak_key():
    ssm = boto3.client(
        "ssm",
        region_name="us-east-1"  # required locally
    )

    key = ssm.get_parameter(
        Name="/ctf/challenge-12/signing-key",
        WithDecryption=True
    )["Parameter"]["Value"]

    print("[KEY]", key)
    assert key
