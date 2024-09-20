from flask import Flask
from flask import request
from flask import make_response
from flask import render_template
import logging
import os
import sys
from snowflake.snowpark import Session

SNOWFLAKE_HOST = os.getenv("SNOWFLAKE_HOST")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")

SERVICE_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVICE_PORT = os.getenv("SERVER_PORT", 8080)

def get_token() -> str:
    """
    Reads login credential automatically supplied by Snowservices
    """
    with open("/snowflake/session/token", "r") as f:
        return f.read()

def get_connection_params() -> dict:
    """
    Returns connection parameters read from environment variables.
    Authentication can be with access token provided by SnowServices or
    with username/password that are convenient for testing locally.
    """

    if SNOWFLAKE_PASSWORD:
        base_connection_params = {
            "account": SNOWFLAKE_ACCOUNT,
            "host": SNOWFLAKE_HOST,
            "database": SNOWFLAKE_DATABASE,
            "schema": SNOWFLAKE_SCHEMA,
            "user": SNOWFLAKE_USER,
            "password": SNOWFLAKE_PASSWORD,
        }
    else:
        base_connection_params = {
            "account": SNOWFLAKE_ACCOUNT,
            "host": SNOWFLAKE_HOST,
            "database": SNOWFLAKE_DATABASE,
            "schema": SNOWFLAKE_SCHEMA,
            "authenticator": "oauth",
            "token": get_token(),
        }

    return base_connection_params

def set_up_session() -> Session:
    """
    Creates session from connection parameters.
    """
    connection_params = get_connection_params()
    logger.info("Connection params:" + str(connection_params))
    session = Session.builder.configs(connection_params).create()
    # Ingress proxy expects session to have this parameter set.
    session.sql("alter session set python_connector_query_result_format='JSON'").collect()
    return session

def get_na_security_url():
    session = set_up_session()
    query_result = session.sql(f"SELECT SYSTEM$NA_SECURITY_URL('{SNOWFLAKE_DATABASE}') AS NA_SECURITY_URL").collect()
    if len(query_result) > 0:
        return query_result[0]['NA_SECURITY_URL']
    else:
        return None

app = Flask(__name__)

@app.get("/healthcheck")
def readiness_probe():
    return "I'm ready!"


@app.route("/", methods=["GET", "POST"])
def ui():
    '''
    Main handler for providing a web UI.
    '''
    return render_template("ui.html",
        SNOWFLAKE_HOST = SNOWFLAKE_HOST,
        SNOWFLAKE_ACCOUNT = SNOWFLAKE_ACCOUNT,
        SNOWFLAKE_DATABASE = SNOWFLAKE_DATABASE,
        SNOWFLAKE_SCHEMA = SNOWFLAKE_SCHEMA,
        SNOWFLAKE_USER = SNOWFLAKE_USER,
        SNOWFLAKE_PASSWORD = SNOWFLAKE_PASSWORD,

        SERVICE_HOST = SERVICE_HOST,
        SERVICE_PORT = SERVICE_PORT,
        NA_SECURITY_URL = get_na_security_url())


if __name__ == '__main__':
    app.run(host=SERVICE_HOST, port=SERVICE_PORT)
