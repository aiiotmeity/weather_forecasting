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
    ENHANCED with debugging: Get historical weather data for visualization
    """
    try:
        days = int(request.args.get('days', 10))
        parameter = request.args.get('parameter', 'all')
        
        # Limit to prevent excessive data requests
        if days > 30:
            days = 30
        if days < 1:
            days = 1
            
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        print(f"DEBUG: Searching for data between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}")
        
        table = boto3.resource('dynamodb', region_name='us-east-1').Table('weather_station_data')
        
        # FIRST: Try to scan without filter to see what data exists
        print("DEBUG: Scanning table to see available data...")
        sample_scan = table.scan(Limit=5)
        sample_items = sample_scan.get('Items', [])
        
        print(f"DEBUG: Found {len(sample_items)} sample items")
        for i, item in enumerate(sample_items):
            print(f"DEBUG: Sample item {i+1} structure: {json.dumps(item, cls=DecimalEncoder, indent=2)}")
        
        # Check if the expected path exists
        if sample_items:
            first_item = sample_items[0]
            if 'data' in first_item:
                if 'decoded_payload' in first_item['data']:
                    if 'date' in first_item['data']['decoded_payload']:
                        print(f"DEBUG: Found date field with value: {first_item['data']['decoded_payload']['date']}")
                    else:
                        print("DEBUG: 'date' field not found in decoded_payload")
                        print(f"DEBUG: Available fields in decoded_payload: {list(first_item['data']['decoded_payload'].keys())}")
                else:
                    print("DEBUG: 'decoded_payload' not found in data")
                    print(f"DEBUG: Available fields in data: {list(first_item['data'].keys())}")
            else:
                print("DEBUG: 'data' field not found in item")
                print(f"DEBUG: Available top-level fields: {list(first_item.keys())}")
        
        # Now try the original query
        try:
            query_response = table.query(
                KeyConditionExpression=Key('device_id').eq('weather-v2') & Key('date').between(
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
            )
            items = query_response.get('Items', [])
            print(f"DEBUG: Filtered query returned {len(items)} items")
            
        except Exception as filter_error:
            print(f"DEBUG: Filter query failed: {str(filter_error)}")
            # Try alternative date formats
            date_formats = ['%Y/%m/%d', '%d-%m-%Y', '%m-%d-%Y']
            items = []
            
            for date_format in date_formats:
                try:
                    print(f"DEBUG: Trying date format: {date_format}")
                    
                    query_response = table.query(
                        KeyConditionExpression=Key('device_id').eq('weather-v2') & Key('date').between(
                            start_date.strftime('%Y-%m-%d'),
                            end_date.strftime('%Y-%m-%d')
                        )
                    )
                    items = query_response.get('Items', [])

                    if items:
                        print(f"DEBUG: Success with format {date_format}! Found {len(items)} items")
                        break
                except Exception as e:
                    print(f"DEBUG: Format {date_format} failed: {str(e)}")
                    continue
        
        if not items:
            # Try scanning all data and filtering in Python
            print("DEBUG: Trying client-side filtering...")
            all_scan = table.scan()
            all_items = all_scan.get('Items', [])
            print(f"DEBUG: Total items in table: {len(all_items)}")
            
            # Filter in Python
            items = []
            for item in all_items:
                try:
                    item_date_str = item['data']['decoded_payload'].get('date', '')
                    if item_date_str:
                        # Try parsing different date formats
                        item_date = None
                        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%m-%d-%Y']:
                            try:
                                item_date = datetime.strptime(item_date_str, fmt).date()
                                break
                            except ValueError:
                                continue
                        
                        if item_date and start_date <= item_date <= end_date:
                            items.append(item)
                except (KeyError, TypeError):
                    continue
            
            print(f"DEBUG: Client-side filtering found {len(items)} items")
        
        if not items:
            return jsonify({
                "error": "No historical data found for the specified range",
                "debug_info": {
                    "requested_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                    "total_records_in_table": len(sample_items) if 'sample_items' in locals() else 0,
                    "sample_date_formats_found": [item['data']['decoded_payload'].get('date', 'NO_DATE') for item in sample_items[:3]] if sample_items else []
                }
            }), 404
        
        # Rest of your existing code for processing items...
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
                    
                except ValueError as e:
                    print(f"DEBUG: Date parsing error for {timestamp}: {str(e)}")
                    continue
        
        print(f"DEBUG: Successfully formatted {len(formatted_data)} data points")
        
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
        print(f"ERROR: Exception in get_historical_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to fetch historical weather data: {str(e)}"}), 500

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
            FilterExpression=boto3.dynamodb.conditions.Attr('data.decoded_payload.date').between(start_date, end_date)
        )
        items = scan_response.get('Items', [])
        print("Scan items:", items)
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