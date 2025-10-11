from flask import Flask, jsonify, request, make_response, send_from_directory
from flask_cors import CORS
import boto3
from datetime import datetime, timezone, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
import csv
import io
from decimal import Decimal
import json
import uuid
from dotenv import load_dotenv
import os
from boto3.dynamodb.conditions import Attr

# ### NEW SECTION: Imports for background tasks and river data ###
import threading
import pandas as pd
# This line is crucial: it imports your automation class from its new location
from automation.run_dashboard import DashboardAutomation


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

# In app.py

# In app.py

@app.route('/api/historical-data', methods=['GET'])
def get_historical_data():
    try:
        days = int(request.args.get('days', 3))
        station_id_from_request = request.args.get('station_id', 'weather-v2')

        # --- FIX: Hardcode the device_id with the leading space to match the database ---
        # This ensures we find the data. The long-term solution is to fix the data in DynamoDB.
        actual_device_id_in_db = ' ' + station_id_from_request.strip()

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        table = boto3.resource('dynamodb', region_name='us-east-1').Table('weather_station_data')

        # --- FIX: Use Attr() for all scan filters and use the corrected device_id ---
        filter_expression = Attr('device_id').eq(actual_device_id_in_db) & Attr('data.decoded_payload.date').between(start_date_str, end_date_str)

        response = table.scan(FilterExpression=filter_expression)
        items = response.get('Items', [])

        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=filter_expression,
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))

        if not items:
            return jsonify({"error": f"No data found for station '{station_id_from_request}' in the last {days} days."}), 404
        
        # Sort items by combining date and time into a comparable string
        sorted_items = sorted(
            items, 
            key=lambda x: f"{x.get('data', {}).get('decoded_payload', {}).get('date', '')} {x.get('data', {}).get('decoded_payload', {}).get('time', '')}"
        )

        formatted_data = []
        for item in sorted_items:
            payload = item.get('data', {}).get('decoded_payload', {})
            if payload and 'date' in payload and 'time' in payload:
                # Using ISO 8601 format is best practice for charts
                timestamp = f"{payload['date']}T{payload['time']}" 
                data_point = {'timestamp': timestamp}
                for key, value in payload.items():
                    if isinstance(value, Decimal):
                        data_point[key] = float(value)
                formatted_data.append(data_point)
        
        return jsonify({'data': formatted_data})
    except Exception as e:
        print(f"Error in /api/historical-data: {str(e)}")
        return jsonify({"error": "An unexpected server error occurred"}), 500
    
# In app.py

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
            'station_id': data['stationId'], # <-- FIX: Save the station ID with the request
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
        - Station: {data['stationId']}
        - Date Range: {data['start_date']} to {data['end_date']}

        To approve this request and send the data, click the link below:
        {approval_link}
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

        # <-- FIX: Load start_date, end_date, and station_id from the stored request
        start_date = request_details['start_date']
        end_date = request_details['end_date']
        station_id = request_details['station_id']
        
        # <-- FIX: Handle the leading space in the device_id to match the database
        actual_device_id_in_db = ' ' + station_id.strip()

        # Fetch weather data
        weather_table = boto3.resource('dynamodb', region_name='us-east-1').Table('weather_station_data')
        
        # <-- FIX: Update the filter to use the loaded variables and filter by station
        filter_expression = Attr('device_id').eq(actual_device_id_in_db) & Attr('data.decoded_payload.date').between(start_date, end_date)
        
        scan_response = weather_table.scan(FilterExpression=filter_expression)
        items = scan_response.get('Items', [])

        if not items:
            requests_table.update_item(
                Key={'request_id': request_id},
                UpdateExpression="set #s = :s",
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':s': 'approved'}
            )
            # You might want to notify the user that no data was found
            return "Request approved, but no weather data was found for the specified date range. The user has been notified.", 200

        # Create CSV and send email to the user
        output = io.StringIO()
        writer = csv.writer(output)
        # Corrected the header to match the payload keys
        header = ['date', 'time', 'temperature', 'humidity', 'airPressure', 'rainfall1h', 'rainfall24h', 'windDirection', 'WindSpeedAvg', 'windSpeedMax']
        writer.writerow(header)
        for item in items:
            payload = item['data']['decoded_payload']
            writer.writerow([payload.get(k) for k in header])
        csv_data = output.getvalue()
        
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg['To'] = request_details['email']
        msg['Subject'] = f"Your Approved Weather Data from {start_date} to {end_date}"
        body = "Hello,\n\nYour request for historical weather data has been approved. Please find the data attached as a CSV file.\n\nRegards,\nWeather Station Team"
        msg.attach(MIMEText(body, 'plain'))
        
        part = MIMEBase('application', "octet-stream")
        part.set_payload(csv_data.encode())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="weather_data_{start_date}_to_{end_date}.csv"')
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
        import traceback
        traceback.print_exc()
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


### NEW SECTION 1: API Endpoint for the River Dashboard ###
# This new function replaces the old `server.py`
### CORRECTED SECTION for fetching river data ###

@app.route('/api/river-data')
def get_river_data():
    """
    Provides the latest water level, rainfall, and forecast data
    by reading the CSV files generated by your automation script.
    This version safely handles missing rainfall data.
    """
    ALERT_THRESHOLDS = {'NORMAL': 3.0, 'WATCH': 4.0, 'WARNING': 5.0}

    def get_alert_level(water_level):
        if water_level < ALERT_THRESHOLDS['NORMAL']: return 'normal'
        if water_level < ALERT_THRESHOLDS['WATCH']: return 'watch'
        if water_level < ALERT_THRESHOLDS['WARNING']: return 'warning'
        return 'critical'

    try:
        current_data_path = os.path.join(os.path.dirname(__file__), 'automation', 'deploy1.csv')
        forecast_data_path = os.path.join(os.path.dirname(__file__), 'automation', 'forecast.csv')

        # Read current data
        df_current = pd.read_csv(current_data_path)
        
        # Safely get the latest water level data
        latest_water = df_current[df_current['neel_level'].notna()].iloc[-1]
        water_level = float(latest_water['neel_level'])
        
        # --- START OF FIX ---
        # Safely get the latest rainfall data
        # Initialize with default values
        latest_rain_value = 0.0
        latest_rain_time = latest_water['date_neel_level'] # Default to water time if no rain time

        # Check if the rain data columns exist before trying to access them
        if 'neel_rain' in df_current.columns and 'date_neel_rain' in df_current.columns:
            # Find the last row that actually has a rainfall measurement
            df_rain_only = df_current[df_current['neel_rain'].notna()]
            if not df_rain_only.empty:
                latest_rain = df_rain_only.iloc[-1]
                latest_rain_value = float(latest_rain['neel_rain'])
                latest_rain_time = latest_rain['date_neel_rain']
        # --- END OF FIX ---

        # Read forecast data
        df_forecast = pd.read_csv(forecast_data_path)
        forecast_values = df_forecast['forecast_value'].head(6).tolist()

        response_data = {
            'currentWaterLevel': water_level,
            'currentRainfall': latest_rain_value,
            'waterLevelTime': latest_water['date_neel_level'],
            'rainfallTime': latest_rain_time,
            'forecast': forecast_values,
            'currentAlert': get_alert_level(water_level),
            'serverTime': datetime.now().isoformat()
        }
        return jsonify(response_data)
    except Exception as e:
        print(f"Error serving river data: {e}")
        return jsonify({ 'error': str(e) }), 500


### NEW SECTION 2: Serving the React Frontend ###
# This function will serve your built React app in production
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


### NEW SECTION 3: Running the Automation in the Background ###
### CORRECTED SECTION FOR BACKGROUND AUTOMATION ###

def run_automation_service():
    """
    This function runs your automation script. We will start it in a
    separate thread so it doesn't block the web server.
    """
    # Define the full path to the automation directory
    # os.path.dirname(__file__) gets the directory where app.py is located
    automation_dir = os.path.join(os.path.dirname(__file__), 'automation')
    
    # CRITICAL FIX: Change the current working directory FOR THIS THREAD
    # This ensures the script can find its local files (deploy1.csv, etc.)
    os.chdir(automation_dir)
    
    print(f"--- Starting Automation Service in Background Thread (working directory: {os.getcwd()}) ---")
    automation = DashboardAutomation()
    automation.run()


if __name__ == '__main__':
    # Start the automation script in a background thread
    automation_thread = threading.Thread(target=run_automation_service, daemon=True)
    automation_thread.start()
    
    # Start the Flask web server
    # use_reloader=False is important to prevent the background thread from starting twice
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)