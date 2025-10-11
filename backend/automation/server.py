# server.py - Fixed version with proper API endpoint
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import pandas as pd
import os
import socket
from datetime import datetime

class DashboardServer(BaseHTTPRequestHandler):
    
    # Alert thresholds in meters
    ALERT_THRESHOLDS = {
        'NORMAL': 3.0,
        'WATCH': 4.0,
        'WARNING': 5.0
    }
    
    def do_GET(self):
        """Handle GET requests"""
        
        print(f"🔗 Request: {self.path}")  # Debug log
        
        if self.path == '/' or self.path == '/dashboard.html':
            self.serve_file('dashboard.html', 'text/html')
        elif self.path.startswith('/api/data'):
            self.serve_csv_data()
        elif self.path.endswith('.html'):
            self.serve_file(self.path[1:], 'text/html')
        elif self.path.endswith('.css'):
            self.serve_file(self.path[1:], 'text/css')
        elif self.path.endswith('.js'):
            self.serve_file(self.path[1:], 'application/javascript')
        else:
            print(f"❌ 404 for: {self.path}")
            self.send_error(404, f"File not found: {self.path}")
    
    def serve_file(self, filename, content_type):
        """Serve a file from disk"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
                print(f"✅ Served: {filename}")
            else:
                print(f"❌ File not found: {filename}")
                self.send_error(404, f"File {filename} not found")
        except Exception as e:
            print(f"❌ Error serving file {filename}: {e}")
            self.send_error(500, f"Server error: {e}")
    
    def get_alert_level(self, water_level):
        """Determine alert level based on water level"""
        if water_level < self.ALERT_THRESHOLDS['NORMAL']:
            return 'normal'
        elif water_level < self.ALERT_THRESHOLDS['WATCH']:
            return 'watch'
        elif water_level < self.ALERT_THRESHOLDS['WARNING']:
            return 'warning'
        else:
            return 'critical'
    
    def serve_csv_data(self):
        """Read CSV data and serve as JSON with alert info"""
        try:
            print("📊 Serving API data...")
            
            # Read current data from deploy1.csv
            current_data = self.read_current_data()
            
            # Read forecast data from forecast.csv
            forecast_data = self.read_forecast_data()
            
            # Calculate current alert level
            current_alert = self.get_alert_level(current_data['water_level'])
            
            # Combine data for dashboard
            response_data = {
                'currentWaterLevel': current_data['water_level'],
                'currentRainfall': current_data['rainfall'],
                'waterLevelTime': current_data['water_level_time'],
                'rainfallTime': current_data['rainfall_time'],
                'forecast': forecast_data,
                'currentAlert': current_alert,
                'serverTime': datetime.now().isoformat()
            }
            
            print(f"📊 API Response: Water={response_data['currentWaterLevel']}m, Rain={response_data['currentRainfall']}mm")
            
            # Send JSON response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            json_data = json.dumps(response_data, indent=2)
            self.wfile.write(json_data.encode('utf-8'))
            
            # Log alert status
            if current_alert != 'normal':
                print(f"🚨 ALERT: {current_alert.upper()} - Water Level: {current_data['water_level']:.2f}m")
            else:
                print(f"✅ Normal - Water Level: {current_data['water_level']:.2f}m")
            
        except Exception as e:
            print(f"❌ Error serving CSV data: {e}")
            
            # Send error response with fallback data
            error_data = {
                'currentWaterLevel': 2.45,
                'currentRainfall': 0.0,
                'waterLevelTime': datetime.now().isoformat(),
                'rainfallTime': datetime.now().isoformat(),
                'forecast': [2.45, 2.46, 2.47, 2.48, 2.49, 2.50],
                'currentAlert': 'normal',
                'error': str(e)
            }
            
            self.send_response(200)  # Send 200 instead of 500 for fallback data
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            json_data = json.dumps(error_data, indent=2)
            self.wfile.write(json_data.encode('utf-8'))
    
    def read_current_data(self):
        """Read latest current data from deploy1.csv"""
        try:
            if not os.path.exists('deploy1.csv'):
                print("⚠️ deploy1.csv not found, using demo values")
                return {
                    'water_level': 2.42,
                    'rainfall': 0.0,
                    'water_level_time': '2025-08-19T13:00:00',
                    'rainfall_time': '2025-08-19T11:30:00'
                }
            
            df = pd.read_csv('deploy1.csv')
            print(f"📋 CSV loaded: {len(df)} rows")
            
            # Get latest water level
            water_data = df[['neel_level', 'date_neel_level']].dropna()
            if len(water_data) > 0:
                latest_water_level = water_data['neel_level'].iloc[-1]
                latest_water_time = water_data['date_neel_level'].iloc[-1]
                print(f"🌊 Latest water: {latest_water_level}m at {latest_water_time}")
            else:
                latest_water_level = 0.0
                latest_water_time = datetime.now().isoformat()
            
            # Get latest rainfall
            rainfall_data = df[['neel_rain', 'date_neel_rain']].dropna()
            if len(rainfall_data) > 0:
                latest_rainfall = rainfall_data['neel_rain'].iloc[-1]
                latest_rain_time = rainfall_data['date_neel_rain'].iloc[-1]
                print(f"🌧️ Latest rain: {latest_rainfall}mm at {latest_rain_time}")
            else:
                latest_rainfall = 0.0
                latest_rain_time = datetime.now().isoformat()
            
            return {
                'water_level': float(latest_water_level),
                'rainfall': float(latest_rainfall),
                'water_level_time': latest_water_time,
                'rainfall_time': latest_rain_time
            }
            
        except Exception as e:
            print(f"❌ Error reading deploy1.csv: {e}")
            return {
                'water_level': 2.42,
                'rainfall': 0.0,
                'water_level_time': '2025-08-19T13:00:00',
                'rainfall_time': '2025-08-19T11:30:00'
            }
    
    def read_forecast_data(self):
        """Read forecast data from forecast.csv"""
        try:
            if not os.path.exists('forecast.csv'):
                print("⚠️ forecast.csv not found, using demo forecast")
                return [2.42, 2.43, 2.44, 2.45, 2.46, 2.47]
            
            df = pd.read_csv('forecast.csv')
            
            # Get the 6 forecast values
            if 'forecast_value' in df.columns and len(df) >= 6:
                forecast_values = df['forecast_value'].head(6).tolist()
                print(f"🔮 Forecast loaded: {forecast_values}")
                return [float(val) for val in forecast_values]
            else:
                print("⚠️ Invalid forecast.csv format")
                return [2.42, 2.43, 2.44, 2.45, 2.46, 2.47]
                
        except Exception as e:
            print(f"❌ Error reading forecast.csv: {e}")
            return [2.42, 2.43, 2.44, 2.45, 2.46, 2.47]
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        return "Unable to determine IP"

def start_server(port=8000):
    """Start the web server accessible from network"""
    
    print("=" * 60)
    print("🌊 KALADY PERIYAR RIVER LEVEL MONITORING")
    print("🌐 NETWORK ACCESSIBLE VERSION")
    print("=" * 60)
    
    # Check for files
    if os.path.exists('dashboard.html'):
        print("✅ Found: dashboard.html")
    else:
        print("⚠️ Missing: dashboard.html")
        
    if os.path.exists('deploy1.csv'):
        print("✅ Found: deploy1.csv")
    else:
        print("⚠️ Missing: deploy1.csv (will use demo data)")

    if os.path.exists('forecast.csv'):
        print("✅ Found: forecast.csv")
    else:
        print("⚠️ Missing: forecast.csv (will use demo data)")
    
    # Display alert thresholds
    server = DashboardServer
    print(f"\n🚦 Alert Thresholds:")
    print(f"   🟢 Normal: < {server.ALERT_THRESHOLDS['NORMAL']}m")
    print(f"   🟡 Watch: {server.ALERT_THRESHOLDS['NORMAL']}m - {server.ALERT_THRESHOLDS['WATCH']}m")
    print(f"   🟠 Warning: {server.ALERT_THRESHOLDS['WATCH']}m - {server.ALERT_THRESHOLDS['WARNING']}m")
    print(f"   🔴 Critical: > {server.ALERT_THRESHOLDS['WARNING']}m")
    
    # Get local IP address
    local_ip = get_local_ip()
    
    print(f"\n🚀 Starting server on port {port}...")
    print(f"📱 Local access: http://localhost:{port}")
    print(f"🌐 Network access: http://{local_ip}:{port}")
    print(f"📡 API endpoint: http://{local_ip}:{port}/api/data")
    
    print(f"\n📋 TO ACCESS FROM OTHER DEVICES:")
    print(f"   1. Make sure devices are on the same WiFi/network")
    print(f"   2. Open browser on other device")
    print(f"   3. Go to: http://{local_ip}:{port}")
    print(f"   4. Bookmark it for easy access!")
    
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    try:
        # CRITICAL: Listen on all interfaces (0.0.0.0) instead of localhost
        httpd = HTTPServer(('0.0.0.0', port), DashboardServer)
        print(f"\n🟢 Server running on all network interfaces!")
        print(f"🔗 Share this URL with others: http://{local_ip}:{port}")
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Server stopped")
        httpd.shutdown()
        
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    start_server()