def test_env():
    import subprocess

    subprocess.run([
        "python",
        "-c",
        "import boto3; print('boto3 present')"
    ])
