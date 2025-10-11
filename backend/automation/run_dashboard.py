# run_dashboard.py - API-based version (NO BROWSER AUTOMATION!)
import subprocess
import time
import os
import threading
import schedule
from datetime import datetime, timedelta
import json
import sys


# Import our API extractor
from automation.api_extractor import NeeleLevelAPIExtractor

class DashboardAutomation:
    def __init__(self):
        self.server_process = None
        self.running = True
        self.last_forecast_time = None
        self.forecast_interval_hours = 6
        self.api_extractor = NeeleLevelAPIExtractor()
        
    def load_last_forecast_time(self):
        """Load the last forecast time from file"""
        try:
            if os.path.exists('last_forecast.json'):
                with open('last_forecast.json', 'r') as f:
                    data = json.load(f)
                    self.last_forecast_time = datetime.fromisoformat(data['last_forecast_time'])
                    print(f"Last forecast was at: {self.last_forecast_time}")
            else:
                print("No previous forecast time found - will run initial forecast")
        except Exception as e:
            print(f"Error loading last forecast time: {e}")
    
    def save_last_forecast_time(self):
        """Save the current forecast time to file"""
        try:
            data = {
                'last_forecast_time': datetime.now().isoformat(),
                'forecast_interval_hours': self.forecast_interval_hours
            }
            with open('last_forecast.json', 'w') as f:
                json.dump(data, f)
            print(f"Forecast time saved: {data['last_forecast_time']}")
        except Exception as e:
            print(f"Error saving forecast time: {e}")
    
    def should_run_forecast(self):
        """Check if 6 hours have passed since last forecast"""
        if self.last_forecast_time is None:
            return True  # First run
        
        time_since_last = datetime.now() - self.last_forecast_time
        hours_since_last = time_since_last.total_seconds() / 3600
        
        return hours_since_last >= self.forecast_interval_hours
    
    def run_extraction(self):
        """Run API-based data extraction - NO BROWSER NEEDED!"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 API DATA EXTRACTION...")
        print("📡 Fetching data directly from CWC API...")
        
        try:
            # Use our API extractor instead of browser automation
            success = self.api_extractor.run_extraction()
            
            if success:
                print("✅ API DATA EXTRACTION COMPLETED!")
                return True
            else:
                print("⭐ No new data available from API")
                return False
                
        except Exception as e:
            print(f"❌ API extraction error: {e}")
            return False
    
    def run_forecasting(self, force=False):
        """Run LSTM forecasting only every 6 hours"""
        if not force and not self.should_run_forecast():
            hours_remaining = self.forecast_interval_hours - ((datetime.now() - self.last_forecast_time).total_seconds() / 3600)
            print(f"⏰ Forecasting not due yet. Next forecast in {hours_remaining:.1f} hours")
            return False
            
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔮 RUNNING 6-HOUR LSTM FORECASTING...")
        try:
            # Import directly instead of subprocess to avoid TensorFlow DLL issues
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            
            # Import the LSTM class directly
            from lstm_forecast import SimplifiedNeelLevelLSTM
            
            print("📊 Using direct import method for LSTM")
            
            # Create and run forecaster
            forecaster = SimplifiedNeelLevelLSTM(
                sequence_length=72,
                dataset_file='deploy1.csv',
                forecast_file='forecast.csv'
            )
            
            success = forecaster.run_production_forecasting()
            
            if success:
                print("✅ 6-HOUR LSTM FORECASTING COMPLETED")
                self.last_forecast_time = datetime.now()
                self.save_last_forecast_time()
                return True
            else:
                print("❌ LSTM forecasting failed")
                return False
                
        except Exception as e:
            print(f"❌ LSTM forecasting error: {e}")
            print("🔄 Trying subprocess fallback...")
            
            # Fallback to subprocess
            try:
                result = subprocess.run(['python', 'lstm_forecast.py'], timeout=900)
                if result.returncode == 0:
                    print("✅ LSTM forecasting completed (subprocess)")
                    self.last_forecast_time = datetime.now()
                    self.save_last_forecast_time()
                    return True
                else:
                    print("❌ LSTM forecasting failed (subprocess)")
                    return False
            except Exception as subprocess_error:
                print(f"❌ Subprocess fallback failed: {subprocess_error}")
                return False
    
    def start_server(self):
        """Start the web server in background"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🌐 STARTING WEB SERVER...")
        try:
            self.server_process = subprocess.Popen(['python', 'server.py'])
            time.sleep(3)  # Give server time to start
            print("✅ Web server started successfully")
            print("📱 Dashboard available at: http://localhost:8000")
            return True
        except Exception as e:
            print(f"❌ Web server error: {e}")
            return False
    
    def stop_server(self):
        """Stop the web server"""
        if self.server_process:
            self.server_process.terminate()
            print("🛑 Web server stopped")
    
    def hourly_data_check(self):
        """Hourly API data extraction - FULLY AUTOMATED!"""
        print("\n" + "="*60)
        print(f"🔄 HOURLY API CHECK - {datetime.now().strftime('%H:%M:%S')}")
        print("📡 NO BROWSER - DIRECT API EXTRACTION")
        print("="*60)
        
        # Run API extraction - completely automated!
        extraction_success = self.run_extraction()
        
        if extraction_success:
            print("✅ ✅ ✅ NEW DATA EXTRACTED FROM API!")
        else:
            print("⭐ ⭐ ⭐ NO NEW DATA - CWC HASN'T UPDATED YET")
        
        print("="*60)
        return extraction_success
    
    def six_hour_forecast_check(self):
        """Check if 6-hour forecast is due"""
        if self.should_run_forecast():
            print("\n" + "="*60)
            print("🔮 6-HOUR FORECAST DUE")
            print("="*60)
            
            forecasting_success = self.run_forecasting()
            if forecasting_success:
                print("✅ 6-HOUR FORECAST COMPLETED")
            else:
                print("❌ 6-hour forecast failed")
                
            print("="*60)
        else:
            hours_remaining = self.forecast_interval_hours - ((datetime.now() - self.last_forecast_time).total_seconds() / 3600)
            print(f"⏰ Next 6-hour forecast in {hours_remaining:.1f} hours")
    
    def schedule_tasks(self):
        """Schedule fully automated tasks"""
        print("📅 SETTING UP FULLY AUTOMATED SCHEDULE...")
        
        # Every 60 minutes - FULLY AUTOMATED!
        schedule.every(15).minutes.do(self.hourly_data_check)
        schedule.every(60).minutes.do(self.six_hour_forecast_check)
        
        print("✅ Automation schedule configured:")
        print("   📡 API data extraction: Every 60 minutes (FULLY AUTOMATED)")
        print("   🔮 Forecasting checks: Every 60 minutes (runs only every 6 hours)")

        
        # Show when next extraction will happen
        next_extraction = datetime.now() + timedelta(minutes=60)
        print(f"   ⏰ Next API extraction: {next_extraction.strftime('%H:%M:%S')}")
    
    def run_scheduler(self):
        """Run the fully automated scheduler"""
        print("🚀 AUTOMATED SCHEDULER STARTED")
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                time.sleep(60)
        print("🛑 SCHEDULER STOPPED")
    
    def check_files(self):
        """Check if all required files exist"""
        required_files = ['api_extractor.py', 'server.py']
        optional_files = ['dashboard.html', 'deploy1.csv', 'lstm_forecast.py']
        
        missing_required = [f for f in required_files if not os.path.exists(f)]
        missing_optional = [f for f in optional_files if not os.path.exists(f)]
        
        if missing_required:
            print(f"❌ Missing required files: {missing_required}")
            return False
        
        if missing_optional:
            print(f"⚠️ Missing optional files: {missing_optional}")
        
        print("✅ Essential files found")
        return True
    
    def run(self):
        """Main automation - FULLY AUTOMATED API VERSION"""
        print("🚀 NEELESWARAM API DASHBOARD AUTOMATION")
        print("🎉 FULLY AUTOMATED - NO BROWSER - NO MANUAL CLICKING!")
        print("="*60)
        
        # Check files
        if not self.check_files():
            print("❌ Cannot start - missing essential files")
            return
        
        # Load previous forecast time
        self.load_last_forecast_time()
        
        # Initial setup
        print("🔧 INITIAL SETUP...")
        
        # Run initial API extraction
        print("\n1️⃣ INITIAL API EXTRACTION...")
        extraction_success = self.run_extraction()
        if extraction_success:
            print("✅ Initial API extraction completed")
        else:
            print("⭐ No new data from initial API call")
        
        # Run initial forecasting if 6+ hours have passed
        print("\n2️⃣ CHECKING 6-HOUR FORECAST STATUS...")
        if self.should_run_forecast():
            print("🔮 Running initial 6-hour forecast...")
            forecast_success = self.run_forecasting(force=True)
            if forecast_success:
                print("✅ Initial 6-hour forecast completed")
            else:
                print("⚠️ Initial forecasting failed, continuing anyway...")
        else:
            hours_remaining = self.forecast_interval_hours - ((datetime.now() - self.last_forecast_time).total_seconds() / 3600)
            print(f"⏰ 6-hour forecast not due yet (next in {hours_remaining:.1f} hours)")
        
        # Start web server
        print("\n3️⃣ STARTING WEB SERVER...")
        if not self.start_server():
            print("❌ Cannot start web server")
            return
        
        # Setup automation scheduling
        print("\n4️⃣ SETTING UP FULL AUTOMATION...")
        self.schedule_tasks()
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        
        print("\n🎉 FULLY AUTOMATED DASHBOARD STARTED!")
        print("="*60)
        print("📱 Dashboard URL: http://localhost:8000")
        print("📡 API extraction: Every 60 minutes (AUTOMATIC)")
        print("🔮 Forecasting: Every 6 hours (AUTOMATIC)")

  

        print("\nPress Ctrl+C to stop automation...")
        print("="*60)
        
        try:
            # Keep main thread alive with status updates
            while True:
                time.sleep(300)  # Every 5 minutes
                next_run = schedule.next_run()
                if next_run:
                    time_until = next_run - datetime.now()
                    hours = int(time_until.total_seconds() // 3600)
                    minutes = int((time_until.total_seconds() % 3600) // 60)
                    print(f"🤖 Automation running - Next API call in: {hours}h {minutes}m")
                
        except KeyboardInterrupt:
            print("\n\n🛑 STOPPING AUTOMATION...")
            self.running = False
            self.stop_server()
            print("✅ Automation stopped successfully")

def main():
    """Main function - DIRECT START WITH API"""
    # Install required packages if not available
    try:
        import schedule
        import requests
    except ImportError:
        print("Installing required packages...")
        subprocess.run(['pip', 'install', 'schedule', 'requests'])
    
    automation = DashboardAutomation()
    automation.run()

if __name__ == "__main__":
    main()