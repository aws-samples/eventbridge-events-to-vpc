import boto3
import logging
from botocore.exceptions import ClientError
from flask import Flask, request, jsonify

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

secrets_manager_client = boto3.client('secretsmanager')

@app.route('/',methods = ['POST', 'GET'])
def flask_app():

   # Verify app is running
   if request.method == 'GET':
      app.logger.info('Hello from my container!')
      return jsonify({'message': 'Hello from my container!'})

   # Process event and return response
   if request.method == 'POST':

      request_body = request.get_json()
      app.logger.info('Processing event')
      app.logger.info(request_body)

      # Retrieve Secrets Manager secret
      try:
         secret_response = get_secret()
      except ClientError as e:
         response = {
            'success': False,
            'message': f"Failed to call Secrets Manager - {e}."
         }
         return jsonify(response)
      # Validate api-key in request header against Secrets Manager secret
      if 'api-key' in request.headers and request.headers['api-key'] == secret_response['SecretString']:
         
         # Extract event content from request and process event
         request_body = request.get_json()
         
         response = {
            'success': True,
            'message': f"Event id {request_body['detail']['event-id']} received."
         }
      else:
         response = {
            'success': False,
            'message': "Failed to validate request API key."
         }
      print(response)
      return jsonify(response)

def get_secret():
   secret_response = secrets_manager_client.get_secret_value(
      SecretId = 'EventsToVpcSecret'
   )
   return secret_response