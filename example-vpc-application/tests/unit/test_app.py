import json
import unittest
from app import app
from unittest import mock
from botocore.exceptions import ClientError

app.testing = True

def mocked_get_secret():
    return {'SecretString': 'valid_secret'}

def mocked_get_secret_failure():
    raise ClientError(operation_name='', error_response={})

class TestFlaskApp(unittest.TestCase):

    def example_event(self):
        return {
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
            "return-response-event": True
            }
        }

    def test_get(self):
        with app.test_client() as client:
            result = client.get('/')
            self.assertEqual(
                result.json,
                {'message': 'Hello from my container!'}
            )

    @mock.patch('app.get_secret', side_effect=mocked_get_secret)
    def test_post(self, get_secret_mock):
        with app.test_client() as client:
            result = client.post(
                '/',
                data=json.dumps(self.example_event()),
                headers={'user-agent': 'Amazon/EventBridge/CustomEvent', 'api-key': 'valid_secret'},
                content_type='application/json'
            )
            self.assertEqual(result.json['success'], True)
            self.assertEqual(get_secret_mock.call_count, 1)
    
    @mock.patch('app.get_secret', side_effect=mocked_get_secret)
    def test_post_invalid_secret(self, get_secret_mock):
        with app.test_client() as client:
            result = client.post(
                '/',
                data=json.dumps(self.example_event()),
                headers={'user-agent': 'Amazon/EventBridge/CustomEvent', 'api-key': 'invalid_secret'},
                content_type='application/json'
            )
            self.assertIn(result.json['message'], 'Failed to validate request API key.')
            self.assertEqual(get_secret_mock.call_count, 1)
    
    @mock.patch('app.get_secret', side_effect=mocked_get_secret_failure)
    def test_post_get_secret_failure(self, get_secret_failure_mock):
        with app.test_client() as client:
            result = client.post(
                '/',
                data=json.dumps(self.example_event()),
                headers={'user-agent': 'Amazon/EventBridge/CustomEvent', 'api-key': 'valid_secret'},
                content_type='application/json'
            )
            self.assertIn('Failed to call Secrets Manager', result.json['message'])
            self.assertEqual(get_secret_failure_mock.call_count, 1)