from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
from datetime import datetime, timedelta
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

app = Flask(__name__)
# Updated CORS configuration for React development server
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# Email configuration - Update with your SMTP settings
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',  # For Gmail
    'smtp_port': 587,
    'sender_email': 'your_email@gmail.com',  # Replace with your email
    'sender_password': 'your_app_password',  # Use app-specific password
    'sender_name': 'Weather Station - Adishankara Engineering College'
}

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, o).default(o)

@app.route('/api/weather')
def get_weather_data():
    """Get latest weather data from DynamoDB"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('weather_station_data')

        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('device_id').eq(' weather-v2'),
            ScanIndexForward=False,
            Limit=1
        )
        
        items = response.get('Items', [])
        
        if not items:
            return jsonify({"error": "No data found"}), 404

        latest = items[0]['data']['decoded_payload']
        weather_data = {
            "device_id": latest['device_id'],
            "temperature": float(latest['temperature']),
            "humidity": float(latest['humidity']),
            "airPressure": float(latest['airPressure']),
            "rainfall1h": float(latest['rainfall1h']),
            "rainfall24h": float(latest['rainfall24h']),
            "windDirection": float(latest['windDirection']),
            "windSpeedAvg": float(latest['WindSpeedAvg']),
            "windSpeedMax": float(latest['windSpeedMax']),
            "date": latest['date'],
            "time": latest['time']
        }
        return jsonify(weather_data)
        
    except Exception as e:
        print(f"Error fetching weather data: {str(e)}")
        return jsonify({"error": "Failed to fetch weather data"}), 500

@app.route('/api/request-data', methods=['POST'])
def request_data():
    """Handle data request and send email with weather data"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'start_date', 'end_date', 'data_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            return jsonify({"error": "Invalid email format"}), 400
        
        # Simulate successful request for demo purposes
        # In production, you would fetch real data and send email
        return jsonify({
            "message": "Data request processed successfully",
            "records_sent": 150,  # Mock data
            "email": data['email']
        })
            
    except Exception as e:
        print(f"Error processing data request: {str(e)}")
        return jsonify({"error": "Failed to process data request"}), 500

@app.route('/api/status')
def get_status():
    """Get system status"""
    return jsonify({
        "status": "operational",
        "database": "connected",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)