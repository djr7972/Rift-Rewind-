import os, json, time
import boto3
import httpx
from aws_lambda_powertools import Logger

logger = Logger()
s3 = boto3.client("s3")
secrets = boto3.client("secretsmanager")

BUCKET = os.environ["BUCKET_NAME"]
SECRET_ID = os.environ["RIOT_SECRET_ID"]
RIOT_REGION = os.environ.get("RIOT_REGION", "americas")  # routing region for Match-V5

def _get_riot_token():
    resp = secrets.get_secret_value(SecretId=SECRET_ID)
    secret = resp.get("SecretString")
    return json.loads(secret)["RIOT_API_KEY"] if secret and secret.startswith("{") else secret

def _riot_headers(token): 
    return {"X-Riot-Token": token}

def handler(event, context):
    # API Gateway -> Lambda (query: ?puuid=...)
    puuid = (event.get("queryStringParameters") or {}).get("puuid")
    if not puuid:
        return {"statusCode": 400, "body": "Missing puuid"}

    token = _get_riot_token()
    base = f"https://{RIOT_REGION}.api.riotgames.com/lol/match/v5"
    # last 20 matches
    with httpx.Client(timeout=15.0) as client:
        ids = client.get(f"{base}/matches/by-puuid/{puuid}/ids?start=0&count=20",
                         headers=_riot_headers(token)).json()
        out = []
        for mid in ids:
            r = client.get(f"{base}/matches/{mid}", headers=_riot_headers(token))
            if r.status_code == 200:
                match = r.json()
                out.append(match)
                key = f"raw/puuid={puuid}/dt={time.strftime('%Y-%m-%d')}/{mid}.json"
                s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(match).encode("utf-8"))
            else:
                logger.warning(f"match {mid} failed: {r.status_code} {r.text}")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"fetched": len(out)})
    }
