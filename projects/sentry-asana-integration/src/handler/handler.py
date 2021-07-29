"""A dummy handler"""
import json


def hello(event, _):
    """A hello world function for proving a deployment worked"""
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response
