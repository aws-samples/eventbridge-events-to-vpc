import json
import unittest
from unittest import mock

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'SECRET_ID': 'mock-secret-id', 'EVENT_BUS_NAME': 'mock-event-bus-name'}):
    from event_relay_function.app import lambda_handler

def mocked_get_secret():
    return {'SecretString': 'valid_secret'}

def mocked_send_request(event):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    return MockResponse({
            "message": f"Event id {event['event']['detail']['event-id']} received.", 
            "success": True
        }, 200)

def mocked_send_request_failure(event):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    return MockResponse({
            "message": "Bad request", 
            "success": False
        }, 400)

def mocked_send_event(response_body):
    return {
        "FailedEntryCount":0,
        "Entries":[
            {
                "EventId":"02e8acd0-b361-e8ac-409f-795d1edf384e"
            }
        ],
        "ResponseMetadata":{
            "RequestId":"c6eff815-0374-4835-a82c-7bb8f445091b",
            "HTTPStatusCode":200,
            "HTTPHeaders":{
                "x-amzn-requestid":"c6eff815-0374-4835-a82c-7bb8f445091b",
                "content-type":"application/x-amz-json-1.1",
                "content-length":"85",
                "date":"Tue, 14 Jun 2022 11:40:40 GMT"
            },
            "RetryAttempts":0
        }
    }

class TestRelayLambda(unittest.TestCase):

    @mock.patch('event_relay_function.app.get_secret', side_effect=mocked_get_secret)
    @mock.patch('event_relay_function.app.send_request', side_effect=mocked_send_request)
    @mock.patch('event_relay_function.app.send_event', side_effect=mocked_send_event)
    def test_build(self, get_secret_mock, send_request_mock, send_event_mock):

        response = lambda_handler(self.invoke_event(), "")
        print('response: ', response)

        self.assertEqual(get_secret_mock.call_count, 1)
        self.assertEqual(send_request_mock.call_count, 1)
        self.assertEqual(send_event_mock.call_count, 1)
        self.assertEqual(response['statusCode'], 200)
    
    @mock.patch('event_relay_function.app.get_secret', side_effect=mocked_get_secret)
    @mock.patch('event_relay_function.app.send_request', side_effect=mocked_send_request_failure)
    @mock.patch('event_relay_function.app.send_event', side_effect=mocked_send_event)
    def test_fail_to_process_event(self, get_secret_mock, send_request_failure_mock, send_event_mock):

        with self.assertRaises(Exception):
            response = lambda_handler(self.invoke_event(), "")
            print('response: ', response)

        self.assertEqual(send_request_failure_mock.call_count, 1)
        self.assertEqual(send_event_mock.call_count, 0)

    def invoke_event(self):
        return {
            "url":"http://internal-k8s-vpcexamp-vpcexamp-83bd367bda-997025966.us-east-1.elb.amazonaws.com",
            "method":"POST",
            "headers":{
            "user-agent":"Amazon/EventBridge/CustomEvent"
            },
            "return-response-event":True,
            "event":{
            "version":"0",
            "id":"36542e1e-8a29-b98c-ac88-940101a96baa",
            "detail-type":"inbound-event-sent",
            "source":"eventProducerApp",
            "account":"123456789012",
            "time":"2021-05-10T01:02:03Z",
            "region":"us-east-1",
            "resources":[
                
            ],
            "detail":{
                "event-id":"123",
                "return-response-event":True
            }
            }
        }