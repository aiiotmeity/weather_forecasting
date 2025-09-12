from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import boto3
from datetime import datetime, timezone, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import csv
import io
import os
from decimal import Decimal
import json
import uuid
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"])

EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': os.getenv('SENDER_EMAIL'),
    'sender_password': os.getenv('SENDER_PASSWORD'),
    'admin_email': os.getenv('ADMIN_EMAIL'),
    'sender_name': 'Weather Station - Adishankara Engineering College'
}

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal): return float(o)
        return super(DecimalEncoder, self).default(o)

def send_email(message):
    """Helper function to send an email."""
    server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
    server.starttls()
    server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
    server.send_message(message)
    server.quit()

@app.route('/api/historical-data', methods=['GET'])
def get_historical_data():
    """
    NEW ENDPOINT: Get historical weather data for visualization
    Parameters:
    - days: number of days to fetch (default: 5, max: 30)
    - parameter: specific parameter to fetch (optional, default: all)
    """
    try:
        days = int(request.args.get('days', 5))
        parameter = request.args.get('parameter', 'all')
        
        # Limit to prevent excessive data requests
        if days > 30:
            days = 30
        if days < 1:
            days = 1
            
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        table = boto3.resource('dynamodb', region_name='us-east-1').Table('weather_station_data')
        
        # Query data within date range
        scan_response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('data.decoded_payload.date').between(
                start_date.strftime('%Y-%m-%d'), 
                end_date.strftime('%Y-%m-%d')
            )
        )
        
        items = scan_response.get('Items', [])
        
        if not items:
            return jsonify({"error": "No historical data found for the specified range"}), 404
        
        # Sort by date and time
        sorted_items = sorted(items, key=lambda x: (
            x['data']['decoded_payload'].get('date', ''),
            x['data']['decoded_payload'].get('time', '')
        ))
        
        # Format data for charts
        formatted_data = []
        for item in sorted_items:
            payload = item['data']['decoded_payload']
            
            # Create timestamp for chart
            date_str = payload.get('date', '')
            time_str = payload.get('time', '')
            if date_str and time_str:
                try:
                    timestamp = f"{date_str} {time_str}"
                    datetime_obj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    
                    data_point = {
                        'timestamp': timestamp,
                        'date': date_str,
                        'time': time_str,
                        'datetime': datetime_obj.isoformat()
                    }
                    
                    # Add all weather parameters
                    weather_params = [
                        'temperature', 'humidity', 'airPressure', 
                        'rainfall1h', 'rainfall24h', 'windDirection', 
                        'WindSpeedAvg', 'windSpeedMax'
                    ]
                    
                    for param in weather_params:
                        value = payload.get(param)
                        if value is not None:
                            data_point[param] = float(value) if isinstance(value, Decimal) else value
                    
                    formatted_data.append(data_point)
                    
                except ValueError:
                    continue  # Skip invalid date/time entries
        
        return jsonify({
            'data': formatted_data,
            'total_records': len(formatted_data),
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
                'days': days
            }
        })
        
    except Exception as e:
        print(f"Error fetching historical data: {str(e)}")
        return jsonify({"error": "Failed to fetch historical weather data"}), 500

@app.route('/api/request-data', methods=['POST'])
def request_data():
    """
    STEP 1: USER SUBMITS REQUEST
    This function now saves the request with a 'pending' status
    and sends a notification email to the ADMIN for approval.
    """
    if not all([EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'], EMAIL_CONFIG['admin_email']]):
        return jsonify({"error": "Server email configuration is incomplete."}), 500

    data = request.get_json()
    request_id = str(uuid.uuid4())
    
    try:
        requests_table = boto3.resource('dynamodb', region_name='us-east-1').Table('data_requests')
        request_details = {
            'request_id': request_id,
            'email': data['email'],
            'organization': data.get('organization', 'N/A'),
            'start_date': data['start_date'],
            'end_date': data['end_date'],
            'data_parameters': data.get('data_type'),
            'purpose': data.get('purpose', 'N/A'),
            'request_timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'pending'
        }
        requests_table.put_item(Item=request_details)
        print(f"Successfully logged pending request {request_id} for {data['email']}")

        # Send notification email to admin
        approval_link = f"http://localhost:5000/api/approve-request?request_id={request_id}"
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg['To'] = EMAIL_CONFIG['admin_email']
        msg['Subject'] = "New Weather Data Request Awaiting Approval"
        body = f"""
        A new data request has been submitted.

        Request Details:
        - User Email: {data['email']}
        - Organization: {data.get('organization', 'N/A')}
        - Date Range: {data['start_date']} to {data['end_date']}
        - Purpose: {data.get('purpose', 'N/A')}

        To approve this request and send the data, click the link below:
        {approval_link}

        If you do not approve, simply ignore this email.
        """
        msg.attach(MIMEText(body, 'plain'))
        send_email(msg)
        
        return jsonify({"message": "Your request has been submitted and is pending approval."})

    except Exception as e:
        print(f"Error processing new data request: {str(e)}")
        return jsonify({"error": "Failed to submit data request."}), 500

@app.route('/api/approve-request', methods=['GET'])
def approve_request():
    """
    STEP 2: ADMIN APPROVES REQUEST
    This new endpoint is triggered when the admin clicks the approval link.
    It fetches the data and sends it to the original user.
    """
    request_id = request.args.get('request_id')
    if not request_id:
        return "Error: No request ID provided.", 400

    try:
        requests_table = boto3.resource('dynamodb', region_name='us-east-1').Table('data_requests')
        response = requests_table.get_item(Key={'request_id': request_id})
        
        if 'Item' not in response:
            return "Error: Request not found.", 404
        
        request_details = response['Item']

        if request_details.get('status') == 'approved':
            return "This request has already been approved and data has been sent.", 200

        # Fetch weather data
        weather_table = boto3.resource('dynamodb', region_name='us-east-1').Table('weather_station_data')
        scan_response = weather_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('data.decoded_payload.date').between(
                request_details['start_date'], request_details['end_date']
            )
        )
        items = scan_response.get('Items', [])
        
        if not items:
            # Update status to approved even if no data, to prevent re-runs
            requests_table.update_item(
                Key={'request_id': request_id},
                UpdateExpression="set #s = :s",
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':s': 'approved'}
            )
            return "Request approved, but no weather data was found for the specified date range. The user has been notified.", 200

        # Create CSV and send email to the user
        output = io.StringIO()
        writer = csv.writer(output)
        header = ['date', 'time', 'temperature', 'humidity', 'airPressure', 'rainfall1h', 'rainfall24h', 'windDirection', 'windSpeedAvg', 'windSpeedMax']
        writer.writerow(header)
        for item in items:
            payload = item['data']['decoded_payload']
            writer.writerow([
                payload.get(k) for k in ['date', 'time', 'temperature', 'humidity', 'airPressure', 'rainfall1h', 'rainfall24h', 'windDirection', 'WindSpeedAvg', 'windSpeedMax']
            ])
        csv_data = output.getvalue()
        
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg['To'] = request_details['email']
        msg['Subject'] = f"Your Approved Weather Data from {request_details['start_date']} to {request_details['end_date']}"
        body = "Hello,\n\nYour request for historical weather data has been approved. Please find the data attached as a CSV file.\n\nRegards,\nWeather Station Team"
        msg.attach(MIMEText(body, 'plain'))
        
        part = MIMEBase('application', "octet-stream")
        part.set_payload(csv_data.encode())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="weather_data.csv"')
        msg.attach(part)
        
        send_email(msg)

        # Update the request status to 'approved' in DynamoDB
        requests_table.update_item(
            Key={'request_id': request_id},
            UpdateExpression="set #s = :s",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'approved'}
        )
        
        print(f"Request {request_id} approved. Sent {len(items)} records to {request_details['email']}")
        return "Request approved successfully! The data has been sent to the user.", 200

    except Exception as e:
        print(f"Error approving request {request_id}: {str(e)}")
        return "An error occurred while processing the approval.", 500

@app.route('/api/weather')
def get_weather_data():
    try:
        table = boto3.resource('dynamodb', region_name='us-east-1').Table('weather_station_data')
        response = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('device_id').eq(' weather-v2'), ScanIndexForward=False, Limit=1)
        items = response.get('Items', [])
        if not items: return jsonify({"error": "No data found"}), 404
        latest = items[0]['data']['decoded_payload']
        return jsonify({k: float(v) if isinstance(v, Decimal) else v for k, v in latest.items()})
    except Exception as e:
        return jsonify({"error": "Failed to fetch weather data"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)