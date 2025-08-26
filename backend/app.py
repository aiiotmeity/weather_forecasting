# app.py - Flask Backend for Weather Station System

from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
from decimal import Decimal
import json
from datetime import datetime, timezone
import os
from botocore.exceptions import ClientError

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# AWS DynamoDB configuration
# Make sure to set these environment variables or configure AWS credentials
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

# DynamoDB table name
WEATHER_TABLE = 'weather_stations'

# Helper function to convert Decimal to float for JSON serialization
def decimal_to_float(obj):
    if isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

class WeatherStationService:
    def __init__(self):
        self.table = dynamodb.Table(WEATHER_TABLE)
    
    def get_all_stations(self):
        """Retrieve all weather stations data"""
        try:
            response = self.table.scan()
            stations = response.get('Items', [])
            return decimal_to_float(stations)
        except ClientError as e:
            print(f"Error retrieving stations: {e}")
            return []
    
    def get_station_by_id(self, station_id):
        """Retrieve specific weather station data"""
        try:
            response = self.table.get_item(
                Key={'station_id': str(station_id)}
            )
            item = response.get('Item')
            if item:
                return decimal_to_float(item)
            return None
        except ClientError as e:
            print(f"Error retrieving station {station_id}: {e}")
            return None
    
    def update_station_data(self, station_id, weather_data):
        """Update weather station data"""
        try:
            # Add timestamp
            weather_data['last_updated'] = datetime.now(timezone.utc).isoformat()
            
            response = self.table.update_item(
                Key={'station_id': str(station_id)},
                UpdateExpression='SET #temp = :temp, #humidity = :humidity, #wind_speed = :wind_speed, #visibility = :visibility, #pressure = :pressure, #condition = :condition, #last_updated = :last_updated',
                ExpressionAttributeNames={
                    '#temp': 'temperature',
                    '#humidity': 'humidity',
                    '#wind_speed': 'wind_speed',
                    '#visibility': 'visibility',
                    '#pressure': 'pressure',
                    '#condition': 'condition',
                    '#last_updated': 'last_updated'
                },
                ExpressionAttributeValues={
                    ':temp': Decimal(str(weather_data['temperature'])),
                    ':humidity': Decimal(str(weather_data['humidity'])),
                    ':wind_speed': Decimal(str(weather_data['wind_speed'])),
                    ':visibility': Decimal(str(weather_data['visibility'])),
                    ':pressure': Decimal(str(weather_data['pressure'])),
                    ':condition': weather_data['condition'],
                    ':last_updated': weather_data['last_updated']
                },
                ReturnValues='UPDATED_NEW'
            )
            return True
        except ClientError as e:
            print(f"Error updating station {station_id}: {e}")
            return False
    
    def create_station(self, station_data):
        """Create a new weather station"""
        try:
            station_data['created_at'] = datetime.now(timezone.utc).isoformat()
            station_data['last_updated'] = datetime.now(timezone.utc).isoformat()
            
            # Convert float values to Decimal for DynamoDB
            for key in ['temperature', 'humidity', 'wind_speed', 'visibility', 'pressure']:
                if key in station_data:
                    station_data[key] = Decimal(str(station_data[key]))
            
            # Convert coordinates to Decimal
            if 'coordinates' in station_data:
                station_data['coordinates'] = [Decimal(str(coord)) for coord in station_data['coordinates']]
            
            response = self.table.put_item(Item=station_data)
            return True
        except ClientError as e:
            print(f"Error creating station: {e}")
            return False

# Initialize service
weather_service = WeatherStationService()

# API Routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'Kerala Weather Station API'
    })

@app.route('/api/weather-stations', methods=['GET'])
def get_all_weather_stations():
    """Get all weather stations data"""
    try:
        stations = weather_service.get_all_stations()
        return jsonify({
            'success': True,
            'data': stations,
            'count': len(stations)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weather-stations/<station_id>', methods=['GET'])
def get_weather_station(station_id):
    """Get specific weather station data"""
    try:
        station = weather_service.get_station_by_id(station_id)
        if station:
            return jsonify({
                'success': True,
                'data': station
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Station not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weather-stations/<station_id>', methods=['PUT'])
def update_weather_station(station_id):
    """Update weather station data"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['temperature', 'humidity', 'wind_speed', 'visibility', 'pressure', 'condition']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        success = weather_service.update_station_data(station_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Station updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update station'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weather-stations', methods=['POST'])
def create_weather_station():
    """Create a new weather station"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['station_id', 'name', 'coordinates', 'temperature', 'humidity', 'wind_speed', 'visibility', 'pressure', 'condition']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        success = weather_service.create_station(data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Station created successfully'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create station'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weather-stations/<station_id>/history', methods=['GET'])
def get_station_history(station_id):
    """Get historical data for a weather station (placeholder for future implementation)"""
    # This would require a separate table for historical data
    return jsonify({
        'success': True,
        'message': 'Historical data endpoint - to be implemented',
        'station_id': station_id
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# Initialize sample data (run once)
def initialize_sample_data():
    """Initialize DynamoDB with sample Kerala weather stations data"""
    sample_stations = [
        {
            'station_id': '1',
            'name': 'Thiruvananthapuram',
            'coordinates': [8.5241, 76.9366],
            'temperature': 28.5,
            'humidity': 75,
            'wind_speed': 12,
            'visibility': 8,
            'pressure': 1013.2,
            'condition': 'Partly Cloudy'
        },
        {
            'station_id': '2',
            'name': 'Kochi',
            'coordinates': [9.9312, 76.2673],
            'temperature': 30.2,
            'humidity': 82,
            'wind_speed': 8,
            'visibility': 6,
            'pressure': 1011.8,
            'condition': 'Cloudy'
        },
        {
            'station_id': '3',
            'name': 'Kozhikode',
            'coordinates': [11.2588, 75.7804],
            'temperature': 29.1,
            'humidity': 78,
            'wind_speed': 10,
            'visibility': 7,
            'pressure': 1012.5,
            'condition': 'Light Rain'
        }
    ]
    
    for station in sample_stations:
        weather_service.create_station(station)
    
    print("Sample data initialized!")

if __name__ == '__main__':
    # Uncomment the line below to initialize sample data (run once)
    # initialize_sample_data()
    
    app.run(debug=True, host='0.0.0.0', port=5000)