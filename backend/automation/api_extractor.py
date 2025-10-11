# api_extractor.py - FULL AUTOMATION VERSION (Water Level + Rainfall)
import requests
import pandas as pd
import os
from datetime import datetime
import json

class NeeleLevelAPIExtractor:
    def __init__(self):
        # API URL for Water Level (Datatype: HHS) - WORKING
        self.water_level_url = "https://ffs.india-water.gov.in/iam/api/new-entry-data/specification/sorted-page?sort-criteria=%7B%22sortOrderDtos%22:%5B%7B%22sortDirection%22:%22DESC%22,%22field%22:%22id.dataTime%22%7D%5D%7D&page-number=0&page-size=2&specification=%7B%22where%22:%7B%22where%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22id.stationCode%22,%22operator%22:%22eq%22,%22value%22:%22012-SWRDKOCHI%22%7D%7D,%22and%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22id.datatypeCode%22,%22operator%22:%22eq%22,%22value%22:%22HHS%22%7D%7D%7D,%22and%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22dataValue%22,%22operator%22:%22null%22,%22value%22:%22false%22%7D%7D%7D%7D%7D"
        
        # API URL for Rainfall (Datatype: MPS) - FROM both.py (WORKING)
        self.rainfall_url = "https://ffs.india-water.gov.in/iam/api/new-entry-data/specification/sorted-page?sort-criteria=%7B%22sortOrderDtos%22:%5B%7B%22sortDirection%22:%22DESC%22,%22field%22:%22id.dataTime%22%7D%5D%7D&page-number=0&page-size=2&specification=%7B%22where%22:%7B%22where%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22id.stationCode%22,%22operator%22:%22eq%22,%22value%22:%22012-SWRDKOCHI%22%7D%7D,%22and%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22id.datatypeCode%22,%22operator%22:%22eq%22,%22value%22:%22MPS%22%7D%7D%7D%7D"

        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,ml;q=0.8",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Referer": "https://ffs.india-water.gov.in/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "class-name": "NewEntryDataDto",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\""
        }
        
        self.dataset_file = 'deploy1.csv'
    
    def extract_water_level(self):
        """Extract latest water level data from API"""
        try:
            print("🌊 Fetching water level data from API...")
            response = requests.get(self.water_level_url, headers=self.headers, timeout=20)
            response.raise_for_status()
            data_list = response.json()
            
            if not data_list:
                print("❌ No water level data available from API")
                return None
            
            # Get latest data (first in DESC sorted list)
            latest = data_list[0]
            data_value = latest.get("dataValue")
            data_time = latest.get("id", {}).get("dataTime")
            
            print(f"✅ Latest water level: {data_value}m at {data_time}")
            
            return {
                'neel_level': float(data_value) if data_value else None,
                'date_neel_level': self.convert_timestamp(data_time)
            }
            
        except requests.RequestException as e:
            print(f"❌ Error fetching water level data: {e}")
            return None
        except Exception as e:
            print(f"❌ Error processing water level data: {e}")
            return None

    def extract_rainfall(self):
        """Extract latest rainfall data from API"""
        try:
            print("🌧️ Fetching rainfall data from API...")
            response = requests.get(self.rainfall_url, headers=self.headers, timeout=20)
            response.raise_for_status()
            data_list = response.json()
            
            if not data_list:
                print("❌ No rainfall data available from API")
                return None

            # Get latest data (first in DESC sorted list)
            latest = data_list[0]
            data_value = latest.get("dataValue")
            data_time = latest.get("id", {}).get("dataTime")
            
            print(f"✅ Latest rainfall: {data_value}mm at {data_time}")
            
            return {
                'neel_rain': float(data_value) if data_value is not None else None,
                'date_neel_rain': self.convert_timestamp(data_time)
            }
            
        except requests.RequestException as e:
            print(f"❌ Error fetching rainfall data: {e}")
            return None
        except Exception as e:
            print(f"❌ Error processing rainfall data: {e}")
            return None
    
    def convert_timestamp(self, api_timestamp):
        """Convert API timestamp to our format"""
        try:
            if not api_timestamp:
                return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            
            # If it's already in our format
            if 'T' in str(api_timestamp) and len(str(api_timestamp)) > 15:
                return str(api_timestamp)[:19]  # Take first 19 chars
            
            # If it's epoch timestamp (milliseconds)
            if str(api_timestamp).isdigit() and len(str(api_timestamp)) > 10:
                timestamp = int(api_timestamp)
                if timestamp > 9999999999:  # Milliseconds
                    timestamp = timestamp / 1000
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Default: use current time
            return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            
        except Exception as e:
            print(f"⚠️ Timestamp conversion error: {e}")
            return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    
    def validate_new_data(self, water_data, rainfall_data):
        """Check if we have new data to add"""
        try:
            if not os.path.exists(self.dataset_file):
                return {'should_append': True, 'reason': 'New dataset file'}
            
            df = pd.read_csv(self.dataset_file)
            
            if len(df) == 0:
                return {'should_append': True, 'reason': 'Empty dataset'}
            
            has_new_data = False
            reasons = []
            
            # Check water level timestamp
            if water_data and water_data['neel_level'] is not None:
                new_timestamp = water_data['date_neel_level']
                existing_timestamps = df['date_neel_level'].dropna().tolist()
                
                if new_timestamp not in existing_timestamps:
                    print(f"✅ New water level timestamp: {new_timestamp}")
                    has_new_data = True
                    reasons.append("New water level timestamp")
                else:
                    print(f"➖ Water level timestamp already exists: {new_timestamp}")
            
            # Check rainfall timestamp
            if rainfall_data and rainfall_data['neel_rain'] is not None:
                new_timestamp = rainfall_data['date_neel_rain']
                existing_timestamps = df['date_neel_rain'].dropna().tolist()
                
                if new_timestamp not in existing_timestamps:
                    print(f"✅ New rainfall timestamp: {new_timestamp}")
                    has_new_data = True
                    reasons.append("New rainfall timestamp")
                else:
                    print(f"➖ Rainfall timestamp already exists: {new_timestamp}")
            
            if has_new_data:
                return {'should_append': True, 'reason': ', '.join(reasons)}
            else:
                return {'should_append': False, 'reason': 'No new timestamps found'}
                
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return {'should_append': True, 'reason': 'Validation error - proceeding'}
    
    def append_data(self, water_data, rainfall_data):
        """Append new data to CSV file - BOTH water level and rainfall"""
        try:
            # Prepare new row with BOTH data types
            new_row = {
                "neel_level": water_data.get('neel_level') if water_data else None,
                "date_neel_level": water_data.get('date_neel_level') if water_data else None,
                "neel_rain": rainfall_data.get('neel_rain') if rainfall_data else None,
                "date_neel_rain": rainfall_data.get('date_neel_rain') if rainfall_data else None
            }
            
            # Create DataFrame for new row
            new_row_df = pd.DataFrame([new_row])
            
            # Append to existing file or create new one
            if os.path.exists(self.dataset_file):
                new_row_df.to_csv(self.dataset_file, mode='a', header=False, index=False)
                print(f"✅ Data appended to existing {self.dataset_file}")
            else:
                new_row_df.to_csv(self.dataset_file, index=False)
                print(f"✅ New file {self.dataset_file} created with data")
            
            # Show summary
            self.show_summary()
            
            return True
            
        except Exception as e:
            print(f"❌ Error appending data: {e}")
            return False
    
    def show_summary(self):
        """Show summary of current dataset"""
        try:
            df = pd.read_csv(self.dataset_file)
            
            neel_level_count = df['neel_level'].notna().sum()
            neel_rain_count = df['neel_rain'].notna().sum()
            
            print(f"\n📊 DATASET SUMMARY:")
            print(f"   Total rows: {len(df)}")
            print(f"   Water level entries: {neel_level_count}")
            print(f"   Rainfall entries: {neel_rain_count}")
            
            if neel_level_count > 0:
                latest_level = df.loc[df['neel_level'].notna(), 'neel_level'].iloc[-1]
                latest_level_date = df.loc[df['neel_level'].notna(), 'date_neel_level'].iloc[-1]
                print(f"   Latest water level: {latest_level}m at {latest_level_date}")
            
            if neel_rain_count > 0:
                latest_rain = df.loc[df['neel_rain'].notna(), 'neel_rain'].iloc[-1]
                latest_rain_date = df.loc[df['neel_rain'].notna(), 'date_neel_rain'].iloc[-1]
                print(f"   Latest rainfall: {latest_rain}mm at {latest_rain_date}")
                
        except Exception as e:
            print(f"❌ Summary error: {e}")
    
    def run_extraction(self):
        """Main extraction method - FULLY AUTOMATED (Water Level + Rainfall)"""
        print("🚀 STARTING FULL API EXTRACTION")
        print("🌊 Water Level: API Automated")
        print("🌧️ Rainfall: API Automated") 
        print("="*50)
        
        # Extract both data types
        water_data = self.extract_water_level()
        rainfall_data = self.extract_rainfall()
        
        if not water_data and not rainfall_data:
            print("❌ No data extracted from any API")
            return False
        
        print(f"\n📋 EXTRACTED DATA:")
        if water_data:
            print(f"   neel_level: {water_data['neel_level']}m")
            print(f"   date_neel_level: {water_data['date_neel_level']}")
        else:
            print(f"   neel_level: No new data")
            
        if rainfall_data:
            print(f"   neel_rain: {rainfall_data['neel_rain']}mm")
            print(f"   date_neel_rain: {rainfall_data['date_neel_rain']}")
        else:
            print(f"   neel_rain: No new data")
        
        # Validate if we should append
        validation = self.validate_new_data(water_data, rainfall_data)
        
        if not validation['should_append']:
            print(f"\n➖ SKIPPED: {validation['reason']}")
            return False
        
        # Append to dataset
        success = self.append_data(water_data, rainfall_data)
        
        if success:
            print("\n✅ SUCCESS: FULL API EXTRACTION COMPLETED!")
            print("🌊 Water level: ✅ Automated")
            print("🌧️ Rainfall: ✅ Automated")
        else:
            print("\n❌ ERROR: Failed to save data")
        
        print("="*50)
        return success

def main():
    """Test the FULL API extractor"""
    extractor = NeeleLevelAPIExtractor()
    extractor.run_extraction()

if __name__ == "__main__":
    main()