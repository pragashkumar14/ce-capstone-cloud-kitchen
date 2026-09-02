import json
import os
import boto3
import psycopg2
from psycopg2.extras import RealDictCursor

_SECRET_ARN = os.environ.get("DB_SECRET_ARN")
_DB_HOST = os.environ.get("DB_HOST")
_cached_creds = None


def _get_credentials():
    global _cached_creds
    if _cached_creds is None:
        client = boto3.client("secretsmanager", region_name=os.environ.get("AWS_REGION", "eu-west-3"))
        response = client.get_secret_value(SecretId=_SECRET_ARN)
        _cached_creds = json.loads(response["SecretString"])
    return _cached_creds


def get_connection():
    creds = _get_credentials()
    return psycopg2.connect(
        host=_DB_HOST,
        dbname=creds["dbname"],
        user=creds["username"],
        password=creds["password"],
        cursor_factory=RealDictCursor,
        connect_timeout=5,
    )


def get_admin_credentials():
    creds = _get_credentials()
    return creds["admin_username"], creds["admin_password"]
