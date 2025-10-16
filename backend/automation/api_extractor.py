# api_extractor.py - Water Level ONLY (No Rainfall)
import requests
import pandas as pd
import os
from datetime import datetime

class NeeleLevelAPIExtractor:
    def __init__(self):
        # API URL for Water Level ONLY
        self.water_level_url = "https://ffs.india-water.gov.in/iam/api/new-entry-data/specification/sorted-page?sort-criteria=%7B%22sortOrderDtos%22:%5B%7B%22sortDirection%22:%22DESC%22,%22field%22:%22id.dataTime%22%7D%5D%7D&page-number=0&page-size=2&specification=%7B%22where%22:%7B%22where%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22id.stationCode%22,%22operator%22:%22eq%22,%22value%22:%22012-SWRDKOCHI%22%7D%7D,%22and%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22id.datatypeCode%22,%22operator%22:%22eq%22,%22value%22:%22HHS%22%7D%7D%7D,%22and%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22dataValue%22,%22operator%22:%22null%22,%22value%22:%22false%22%7D%7D%7D%7D%7D"
        
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,ml;q=0.8",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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
            
            latest = data_list[0]
            data_value = latest.get("dataValue")
            data_time = latest.get("id", {}).get("dataTime")
            
            print(f"✅ Latest water level: {data_value}m at {data_time}")
            
            return {
                'neel_level': float(data_value) if data_value else None,
                'date_neel_level': self.convert_timestamp(data_time)
            }
            
        except Exception as e:
            print(f"❌ Error fetching water level: {e}")
            return None
    
    def convert_timestamp(self, api_timestamp):
        """Convert API timestamp to our format"""
        try:
            if not api_timestamp:
                return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            
            if 'T' in str(api_timestamp) and len(str(api_timestamp)) > 15:
                return str(api_timestamp)[:19]
            
            if str(api_timestamp).isdigit() and len(str(api_timestamp)) > 10:
                timestamp = int(api_timestamp)
                if timestamp > 9999999999:
                    timestamp = timestamp / 1000
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%Y-%m-%dT%H:%M:%S')
            
            return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            
        except Exception as e:
            print(f"⚠️ Timestamp conversion error: {e}")
            return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    
    def validate_new_data(self, water_data):
        """Check if we have new data to add"""
        try:
            if not os.path.exists(self.dataset_file):
                return {'should_append': True, 'reason': 'New dataset file'}
            
            df = pd.read_csv(self.dataset_file)
            
            if len(df) == 0:
                return {'should_append': True, 'reason': 'Empty dataset'}
            
            if water_data and water_data['neel_level'] is not None:
                new_timestamp = water_data['date_neel_level']
                existing_timestamps = df['date_neel_level'].dropna().tolist()
                
                if new_timestamp not in existing_timestamps:
                    print(f"✅ New water level timestamp: {new_timestamp}")
                    return {'should_append': True, 'reason': 'New timestamp'}
                else:
                    print(f"➖ Timestamp already exists: {new_timestamp}")
                    return {'should_append': False, 'reason': 'Duplicate timestamp'}
            
            return {'should_append': False, 'reason': 'No valid data'}
                
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return {'should_append': True, 'reason': 'Validation error - proceeding'}
    
    def append_data(self, water_data):
        """Append new data to CSV file - Water Level ONLY with retry logic"""
        import time
        
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                # Prepare new row with ONLY water level data
                new_row = {
                    "neel_level": water_data.get('neel_level'),
                    "date_neel_level": water_data.get('date_neel_level')
                }
                
                new_row_df = pd.DataFrame([new_row])
                
                # Append or create file
                if os.path.exists(self.dataset_file):
                    # Read existing with retry
                    try:
                        existing_df = pd.read_csv(self.dataset_file)
                    except PermissionError:
                        if attempt < max_retries - 1:
                            print(f"⚠️ CSV locked, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                            time.sleep(retry_delay)
                            continue
                        else:
                            raise
                    
                    # Keep only required columns if extra columns exist
                    if 'neel_level' in existing_df.columns and 'date_neel_level' in existing_df.columns:
                        existing_df = existing_df[['neel_level', 'date_neel_level']]
                        
                        # Append new row
                        updated_df = pd.concat([existing_df, new_row_df], ignore_index=True)
                        
                        # Remove duplicates
                        updated_df = updated_df.drop_duplicates(subset=['date_neel_level'], keep='last')
                        
                        # Save with retry
                        try:
                            updated_df.to_csv(self.dataset_file, index=False)
                            print(f"✅ Data appended to {self.dataset_file}")
                        except PermissionError:
                            if attempt < max_retries - 1:
                                print(f"⚠️ Can't write CSV, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                                time.sleep(retry_delay)
                                continue
                            else:
                                raise
                    else:
                        # File corrupted, recreate
                        new_row_df.to_csv(self.dataset_file, index=False)
                        print(f"✅ File recreated with correct columns")
                else:
                    new_row_df.to_csv(self.dataset_file, index=False)
                    print(f"✅ New file {self.dataset_file} created")
                
                self.show_summary()
                return True
                
            except PermissionError as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Permission error, attempt {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ Permission denied after {max_retries} attempts")
                    print(f"💡 SOLUTION: Close Excel/Notepad if deploy1.csv is open!")
                    return False
                    
            except Exception as e:
                print(f"❌ Error appending data: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        return False
    
    def show_summary(self):
        """Show summary of current dataset"""
        try:
            df = pd.read_csv(self.dataset_file)
            
            # Ensure only 2 columns
            if 'neel_level' in df.columns and 'date_neel_level' in df.columns:
                water_count = df['neel_level'].notna().sum()
                
                print(f"\n📊 DATASET SUMMARY:")
                print(f"   Total rows: {len(df)}")
                print(f"   Water level entries: {water_count}")
                print(f"   Columns: {df.columns.tolist()}")
                
                if water_count > 0:
                    latest_level = df.loc[df['neel_level'].notna(), 'neel_level'].iloc[-1]
                    latest_date = df.loc[df['neel_level'].notna(), 'date_neel_level'].iloc[-1]
                    print(f"   Latest: {latest_level}m at {latest_date}")
            else:
                print("⚠️ CSV has wrong columns!")
                
        except Exception as e:
            print(f"❌ Summary error: {e}")
    
    def run_extraction(self):
        """Main extraction method - Water Level ONLY"""
        print("🚀 STARTING API EXTRACTION")
        print("🌊 Water Level: API Automated")
        print("="*50)
        
        # Extract water level
        water_data = self.extract_water_level()
        
        if not water_data:
            print("❌ No data extracted from API")
            return False
        
        print(f"\n📋 EXTRACTED DATA:")
        print(f"   neel_level: {water_data['neel_level']}m")
        print(f"   date_neel_level: {water_data['date_neel_level']}")
        
        # Validate
        validation = self.validate_new_data(water_data)
        
        if not validation['should_append']:
            print(f"\n➖ SKIPPED: {validation['reason']}")
            return False
        
        # Append to dataset
        success = self.append_data(water_data)
        
        if success:
            print("\n✅ SUCCESS: API EXTRACTION COMPLETED!")
        else:
            print("\n❌ ERROR: Failed to save data")
        
        print("="*50)
        return success

def main():
    extractor = NeeleLevelAPIExtractor()
    extractor.run_extraction()

if __name__ == "__main__":
    main()