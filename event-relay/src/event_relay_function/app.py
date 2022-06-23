import os
import json
import requests
import boto3
from botocore.exceptions import ClientError

eventbridge_client = boto3.client('events', region_name=os.environ['AWS_REGION'])
secrets_manager_client = boto3.client('secretsmanager', region_name=os.environ['AWS_REGION'])

secret_response = None

def lambda_handler(event, context):
    global secret_response
    print('event: ', event)

    # Retrieve secret from Secrets Manager
    # First check if the function is warm and the global variable secret value is already set
    # to reduce the number of calls to Secrets Manager
    if secret_response is None:
        try:
            secret_response = get_secret()
        except ClientError as e:
            print(e)
            raise Exception(f'Failed to retrieve secret. Error: {e}.')

    # Append secret to event headers
    event['headers']['api-key'] = secret_response['SecretString']
    print('headers: ', event['headers'])

    # Make an HTTP POST request with event URL and headers
    try:
        response = send_request(event)
    except Exception as e:
        print(e)
        raise Exception(f'Failed to make HTTP request to application. Event id: {event["event"]["detail"]["event-id"]}. Error: {e}')
    response_body = response.json()
    print('http call response: ', response_body)
    if response_body['success'] == False:
        raise Exception(f'Application unable to process event. Event id: {event["event"]["detail"]["event-id"]}. Error: {response_body["message"]}')

    # If the HTTP call was successful and the inbound event had a 'return-response-event' flag,
    # put a response event on the EventBridge bus
    if event['event']['detail']['return-response-event'] == True:
        try:
            eventbridge_response = send_event(response_body)
            print('eventbridge response: ', eventbridge_response)
        except ClientError as e:
            print(e)
            raise Exception(f'Failed to put response event. Event id: {event["event"]["detail"]["event-id"]}. Error: {e}')

    return {
        'statusCode': 200
    }

def get_secret():
    secret_response = secrets_manager_client.get_secret_value(
        SecretId = os.environ['SECRET_ID']
    )
    return secret_response

def send_request(event):
    response = requests.post(event['url'], headers=event['headers'], json=event['event'])
    return response

def send_event(response_body):
    eventbridge_response = eventbridge_client.put_events(
        Entries=[
            {
                'EventBusName': os.environ['EVENT_BUS_NAME'],
                'Detail': json.dumps({'response': response_body}),
                'DetailType': 'outbound-event-sent',
                'Source': 'vpcApp'
            }
        ]
    )
    return eventbridge_response