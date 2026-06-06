import hashlib
import hmac
import json
import os
import re
import time
import uuid

import boto3

s3 = boto3.client("s3")
sns = boto3.client("sns")
PRIVATE_BUCKET = os.environ.get("PRIVATE_BUCKET")
PUBLIC_BUCKET = os.environ.get("PUBLIC_BUCKET")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
TOKEN_SECRET = os.environ.get("TOKEN_SECRET")
TOKEN_TTL = 3600  # 1 hour
ALLOWED_DOMAIN = "@cloudsecuritychampionship.com"
API_BASE_URL = os.environ.get("API_BASE_URL")

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

SNS_TOPIC_NAME = SNS_TOPIC_ARN.split(":")[-1] if SNS_TOPIC_ARN else ""


def _make_token():
    ts = str(int(time.time()))
    sig = hmac.new(TOKEN_SECRET.encode(), ts.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{ts}:{sig}"


def _verify_token(token):
    try:
        ts, sig = token.split(":", 1)
        expected = hmac.new(
            TOKEN_SECRET.encode(), ts.encode(), hashlib.sha256
        ).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected):
            return False
        if time.time() - int(ts) > TOKEN_TTL:
            return False
        return True
    except Exception:
        return False


def _read_template(template):
    if ".." in template:
        return None, "Invalid template name."

    template_key = os.path.join("templates", f"{template}.txt")

    try:
        obj = s3.get_object(Bucket=PRIVATE_BUCKET, Key=template_key)
        return obj["Body"].read().decode(), None
    except Exception:
        return None, "Template not found."


def handler(event, context):
    is_apigw = "requestContext" in event

    if is_apigw:
        body = json.loads(event.get("body") or "{}")
        resource_path = event.get("resource", "")

        if resource_path == "/register":
            token = body.get("token", "")
            template = body.get("template", "default_balloon")

            if not token or not _verify_token(token):
                return _response(
                    403,
                    {
                        "status": "error",
                        "message": "Invalid or expired invitation token.",
                    },
                )

            content, err = _read_template(template)
            if err:
                return _response(400, {"status": "error", "message": err})

            name = body.get("name", "Guest")
            card_content = content.replace("{{name}}", name)

            card_id = str(uuid.uuid4())
            card_key = f"cards/{card_id}.html"

            try:
                s3.put_object(
                    Bucket=PUBLIC_BUCKET,
                    Key=card_key,
                    Body=card_content,
                    ContentType="text/html",
                )
            except Exception:
                pass

            card_url = f"https://{PUBLIC_BUCKET}.s3.amazonaws.com/{card_key}"

            return _response(
                200,
                {
                    "status": "success",
                    "message": "Registration complete! Here is your birthday card.",
                    "card_url": card_url,
                },
            )

        # /generate endpoint
        email = body.get("email", "")

        if not email:
            return _response(400, {"status": "error", "message": "Email is required."})

        if not EMAIL_RE.match(email):
            return _response(
                400,
                {"status": "error", "message": "Please enter a valid email address."},
            )

        if not email.endswith(ALLOWED_DOMAIN):
            return _response(
                403,
                {
                    "status": "error",
                    "message": (
                        f"Only {ALLOWED_DOMAIN} email addresses are eligible."
                        f" Invitations are delivered via the {SNS_TOPIC_NAME}"
                        f" notification channel."
                    ),
                },
            )

        try:
            sns.subscribe(
                TopicArn=SNS_TOPIC_ARN,
                Protocol="email",
                Endpoint=email,
            )
        except Exception as e:
            return _response(
                500,
                {"status": "error", "message": f"Failed to send invitation: {str(e)}"},
            )

        token = _make_token()
        register_url = f"{API_BASE_URL}/register.html?token={token}"

        try:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="Your Birthday Party Invitation!",
                Message=json.dumps(
                    {
                        "message": "You're invited to the S3 Birthday Party!",
                        "action": "Complete your registration to get your personalized birthday card.",
                        "registration_url": register_url,
                        "token": token,
                        "expires_in": "1 hour",
                        "generated_by": context.function_name,
                    }
                ),
            )
        except Exception:
            pass

        return _response(
            200,
            {
                "status": "success",
                "message": "Invitation sent! Check your email.",
            },
        )

    # Direct invocation path: requires valid token
    token = event.get("token", "")
    template = event.get("template", "default_balloon")

    if not token or not _verify_token(token):
        return {"status": "error", "message": "Invalid or expired invitation token."}

    content, err = _read_template(template)
    if err:
        return {"status": "error", "message": err}

    card_content = content.replace("{{name}}", event.get("name", "Friend"))

    return {
        "status": "success",
        "data": {
            "card_content": card_content,
        },
    }


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(body),
    }
