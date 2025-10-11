# lstm_forecast.py - Improved with dynamic retraining and proper timing
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from datetime import datetime, timedelta
import os
import json
import warnings
import pickle
warnings.filterwarnings('ignore')

class DynamicNeelLevelLSTM:
    def __init__(self, sequence_length=72, dataset_file='deploy1.csv', forecast_file='forecast.csv'):
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self.model = None
        self.feature_cols = None
        self.sequence_length = sequence_length
        self.dataset_file = dataset_file
        self.forecast_file = forecast_file
        
        # Model persistence files
        self.model_file = 'lstm_model.h5'
        self.scaler_x_file = 'scaler_x.pkl'
        self.scaler_y_file = 'scaler_y.pkl'
        self.features_file = 'features.json'
        self.last_training_file = 'last_training.json'
        
        # Training configuration
        self.retrain_interval_hours = 6  # Retrain every 6 hours
        self.min_new_data_for_retrain = 10  # Minimum new data points to trigger retrain
        
        # Alert thresholds
        self.ALERT_THRESHOLDS = {
            'NORMAL': 5.0,
            'WATCH': 6.0,
            'WARNING': 9.0
        }
        
    def should_retrain_model(self):
        """Check if __name__ == "__main__":
    main() model should be retrained based on new data and time"""
        try:
            # Check if enough time has passed
            if os.path.exists(self.last_training_file):
                with open(self.last_training_file, 'r') as f:
                    last_training_data = json.load(f)
                    last_training_time = datetime.fromisoformat(last_training_data['timestamp'])
                    hours_since_training = (datetime.now() - last_training_time).total_seconds() / 3600
                    
                    print(f"⏰ Hours since last training: {hours_since_training:.1f}")
                    
                    if hours_since_training < self.retrain_interval_hours:
                        print(f"⭕ Not enough time passed for retraining (need {self.retrain_interval_hours}h)")
                        return False
            
            # Check if we have enough new data
            if not os.path.exists(self.dataset_file):
                print("❌ Dataset file not found")
                return False
                
            df = pd.read_csv(self.dataset_file)
            water_level_data = df['neel_level'].dropna()
            
            if len(water_level_data) < self.sequence_length + 50:
                print(f"⚠️ Not enough data for training ({len(water_level_data)} points)")
                return False
            
            # Check for new data since last training
            if os.path.exists(self.last_training_file):
                with open(self.last_training_file, 'r') as f:
                    last_training_data = json.load(f)
                    last_data_count = last_training_data.get('data_count', 0)
                    new_data_points = len(water_level_data) - last_data_count
                    
                    print(f"📊 New data points since last training: {new_data_points}")
                    
                    if new_data_points < self.min_new_data_for_retrain:
                        print(f"⭕ Not enough new data for retraining (need {self.min_new_data_for_retrain})")
                        return False
            
            print("✅ Conditions met for model retraining")
            return True
            
        except Exception as e:
            print(f"⚠️ Error checking retrain conditions: {e}")
            return True  # Default to retrain if uncertain
    
    def load_existing_model(self):
        """Load previously trained model and scalers"""
        try:
            if (os.path.exists(self.model_file) and 
                os.path.exists(self.scaler_x_file) and 
                os.path.exists(self.scaler_y_file) and 
                os.path.exists(self.features_file)):
                
                print("📂 Loading existing model...")
                
                # Load model
                self.model = load_model(self.model_file)
                
                # Load scalers
                with open(self.scaler_x_file, 'rb') as f:
                    self.scaler_X = pickle.load(f)
                with open(self.scaler_y_file, 'rb') as f:
                    self.scaler_y = pickle.load(f)
                
                # Load feature columns
                with open(self.features_file, 'r') as f:
                    self.feature_cols = json.load(f)
                
                print("✅ Existing model loaded successfully")
                return True
                
        except Exception as e:
            print(f"⚠️ Error loading existing model: {e}")
            
        print("🔄 Will create new model")
        return False
    
    def save_model_and_scalers(self):
        """Save trained model and scalers for future use"""
        try:
            # Save model
            self.model.save(self.model_file)
            
            # Save scalers
            with open(self.scaler_x_file, 'wb') as f:
                pickle.dump(self.scaler_X, f)
            with open(self.scaler_y_file, 'wb') as f:
                pickle.dump(self.scaler_y, f)
            
            # Save feature columns
            with open(self.features_file, 'w') as f:
                json.dump(self.feature_cols, f)
            
            # Save training metadata
            df = pd.read_csv(self.dataset_file)
            training_metadata = {
                'timestamp': datetime.now().isoformat(),
                'data_count': len(df['neel_level'].dropna()),
                'sequence_length': self.sequence_length,
                'feature_count': len(self.feature_cols)
            }
            
            with open(self.last_training_file, 'w') as f:
                json.dump(training_metadata, f)
            
            print("💾 Model and scalers saved successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error saving model: {e}")
            return False
    
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
    
    def load_and_process_data(self, csv_path=None):
        """Load deploy1.csv data"""
        if csv_path is None:
            csv_path = self.dataset_file
            
        print("📊 Loading deploy1.csv data...")
        
        if not os.path.exists(csv_path):
            print(f"❌ Dataset file {csv_path} not found")
            return None
            
        try:
            df = pd.read_csv(csv_path)
            print(f"Dataset loaded: {len(df)} rows")
            
            # Check for required columns
            required_cols = ['date_neel_level', 'neel_level']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                print(f"❌ Missing required columns: {missing_cols}")
                return None
            
            # Convert dates and data types
            df['date_neel_level'] = pd.to_datetime(df['date_neel_level'])
            df['neel_level'] = pd.to_numeric(df['neel_level'], errors='coerce')
            
            # Handle rainfall data if available
            if 'neel_rain' in df.columns:
                df['neel_rain'] = pd.to_numeric(df['neel_rain'], errors='coerce').fillna(0)
            else:
                df['neel_rain'] = 0
            
            # Remove rows with missing critical data
            df = df.dropna(subset=['date_neel_level', 'neel_level'])
            df = df.sort_values('date_neel_level').reset_index(drop=True)
            
            print(f"Clean dataset: {len(df)} records")
            print(f"Time span: {df['date_neel_level'].min()} to {df['date_neel_level'].max()}")
            print(f"Level range: {df['neel_level'].min():.3f} to {df['neel_level'].max():.3f}m")
            
            # Current status
            latest_value = df['neel_level'].iloc[-1]
            latest_date = df['date_neel_level'].iloc[-1]
            current_alert = self.get_alert_level(latest_value)
            
            print(f"Latest reading: {latest_value:.2f}m at {latest_date}")
            print(f"Current alert: {current_alert.upper()}")
            
            return df
            
        except Exception as e:
            print(f"❌ Data loading failed: {e}")
            return None
    
    def create_essential_features(self, df):
        """Create essential features for LSTM"""
        print("🔧 Creating essential features...")
        
        df = df.copy()
        
        # Ensure proper data types
        df['neel_level'] = pd.to_numeric(df['neel_level'], errors='coerce')
        df['neel_rain'] = pd.to_numeric(df['neel_rain'], errors='coerce').fillna(0)
        
        # Water level features (autoregressive)
        for lag_hours in [1, 2, 3, 6, 12, 24]:
            df[f'level_lag_{lag_hours}h'] = df['neel_level'].shift(lag_hours).fillna(df['neel_level'].mean())
        
        # Rate of change
        df['level_change_1h'] = df['neel_level'].diff(1).fillna(0)
        df['level_change_6h'] = df['neel_level'].diff(6).fillna(0)
        df['level_change_24h'] = df['neel_level'].diff(24).fillna(0)
        
        # Moving averages
        df['level_mean_12h'] = df['neel_level'].rolling(12, min_periods=1).mean().fillna(df['neel_level'].mean())
        df['level_mean_24h'] = df['neel_level'].rolling(24, min_periods=1).mean().fillna(df['neel_level'].mean())
        
        # Rainfall features
        for lag_hours in [1, 3, 6, 12, 24]:
            df[f'rain_lag_{lag_hours}h'] = df['neel_rain'].shift(lag_hours).fillna(0)
        
        # Cumulative rainfall
        for window_hours in [6, 12, 24, 48]:
            df[f'rain_sum_{window_hours}h'] = df['neel_rain'].rolling(
                window=window_hours, min_periods=1).sum().fillna(0)
        
        # Time features
        df['hour'] = df['date_neel_level'].dt.hour.astype(int)
        df['month'] = df['date_neel_level'].dt.month.astype(int)
        df['is_monsoon'] = ((df['month'] >= 6) & (df['month'] <= 9)).astype(int)
        
        # High rain indicators
        df['is_heavy_rain'] = (df['neel_rain'] > 10).astype(int)
        df['is_extreme_rain'] = (df['neel_rain'] > 25).astype(int)
        
        # Interactions
        df['rain_when_high'] = df['neel_rain'] * (df['neel_level'] > 3.0).astype(int)
        df['heavy_rain_monsoon'] = df['is_heavy_rain'] * df['is_monsoon']
        
        # Alert features
        df['is_above_normal'] = (df['neel_level'] > self.ALERT_THRESHOLDS['NORMAL']).astype(int)
        df['is_above_watch'] = (df['neel_level'] > self.ALERT_THRESHOLDS['WATCH']).astype(int)
        
        # Define feature columns
        self.feature_cols = [
            # Water level features
            'level_lag_1h', 'level_lag_2h', 'level_lag_3h', 'level_lag_6h', 'level_lag_12h', 'level_lag_24h',
            'level_change_1h', 'level_change_6h', 'level_change_24h',
            'level_mean_12h', 'level_mean_24h',
            
            # Rainfall features
            'rain_lag_1h', 'rain_lag_3h', 'rain_lag_6h', 'rain_lag_12h', 'rain_lag_24h',
            'rain_sum_6h', 'rain_sum_12h', 'rain_sum_24h', 'rain_sum_48h',
            'is_heavy_rain', 'is_extreme_rain',
            
            # Time features
            'hour', 'month', 'is_monsoon',
            
            # Interaction features
            'rain_when_high', 'heavy_rain_monsoon',
            
            # Alert features
            'is_above_normal', 'is_above_watch'
        ]
        
        # Ensure all features are numeric
        for col in self.feature_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        print(f"✅ Created {len(self.feature_cols)} essential features")
        
        return df
    
    def prepare_features(self, df):
        """Prepare final feature matrix"""
        print("🔧 Preparing feature matrix...")
        
        # Create features
        df_features = self.create_essential_features(df)
        
        # Remove rows with NaN in critical columns
        critical_cols = ['neel_level'] + self.feature_cols
        df_clean = df_features.dropna(subset=critical_cols).reset_index(drop=True)
        
        print(f"Final dataset: {len(df_clean)} records")
        print(f"Features: {len(self.feature_cols)}")
        
        return df_clean
    
    def create_sequences(self, features, target):
        """Create sequences for LSTM"""
        X, y = [], []
        
        for i in range(self.sequence_length, len(features)):
            X.append(features[i-self.sequence_length:i])
            y.append(target[i])
        
        return np.array(X), np.array(y)
    
    def train_model(self, df, test_size=0.15, validation_size=0.15):
        """Train LSTM model"""
        print("🚀 Training LSTM model...")
        
        # Prepare data
        features = df[self.feature_cols].values
        target = df['neel_level'].values
        
        print(f"Feature matrix: {features.shape}")
        print(f"Target vector: {target.shape}")
        
        # Check data requirements
        min_required = self.sequence_length + 50
        if len(features) < min_required:
            print(f"❌ Need at least {min_required} points, got {len(features)}")
            return None, None
        
        # Scale data
        print("⚖️ Scaling features and targets...")
        features_scaled = self.scaler_X.fit_transform(features)
        target_scaled = self.scaler_y.fit_transform(target.reshape(-1, 1)).flatten()
        
        # Create sequences
        print("🔄 Creating LSTM sequences...")
        X, y = self.create_sequences(features_scaled, target_scaled)
        
        print(f"LSTM sequences: {X.shape}")
        
        # Split data chronologically
        n_samples = len(X)
        train_size = int(n_samples * (1 - test_size - validation_size))
        val_size = int(n_samples * validation_size)
        
        X_train = X[:train_size]
        y_train = y[:train_size]
        X_val = X[train_size:train_size + val_size]
        y_val = y[train_size:train_size + val_size]
        X_test = X[train_size + val_size:]
        y_test = y[train_size + val_size:]
        
        print(f"Data splits: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
        
        # Build LSTM model
        print("🏗️ Building LSTM architecture...")
        self.model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(self.sequence_length, len(self.feature_cols)),
                 dropout=0.2, recurrent_dropout=0.2),
            LSTM(32, return_sequences=False, dropout=0.2),
            Dense(32, activation='relu'),
            Dropout(0.3),
            Dense(16, activation='relu'),
            Dense(1)
        ])
        
        # Compile model
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        # Callbacks
        early_stop = EarlyStopping(
            monitor='val_loss', 
            patience=10,
            restore_best_weights=True,
            verbose=1
        )
        
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss', 
            factor=0.5, 
            patience=5, 
            min_lr=1e-6,
            verbose=1
        )
        
        # Train model
        print("🎯 Starting LSTM training...")
        try:
            history = self.model.fit(
                X_train, y_train,
                epochs=50,  # Increased epochs for better training
                batch_size=64,
                validation_data=(X_val, y_val),
                callbacks=[early_stop, reduce_lr],
                verbose=1
            )
            
            # Evaluate
            print("📈 Evaluating model...")
            test_pred_scaled = self.model.predict(X_test, verbose=0)
            test_pred = self.scaler_y.inverse_transform(test_pred_scaled).flatten()
            test_actual = self.scaler_y.inverse_transform(y_test.reshape(-1, 1)).flatten()
            
            # Calculate metrics
            rmse = np.sqrt(mean_squared_error(test_actual, test_pred))
            mae = mean_absolute_error(test_actual, test_pred)
            r2 = r2_score(test_actual, test_pred)
            
            print(f"\n📊 LSTM Training Results:")
            print(f"   RMSE: {rmse:.4f} meters")
            print(f"   MAE: {mae:.4f} meters")
            print(f"   R²: {r2:.4f}")
            
            # Quality assessment
            if r2 > 0.8:
                print("   Quality: ✅ EXCELLENT")
            elif r2 > 0.7:
                print("   Quality: ✅ GOOD")
            elif r2 > 0.6:
                print("   Quality: ⚠️ ACCEPTABLE")
            else:
                print("   Quality: ❌ NEEDS IMPROVEMENT")
            
            # Save model and scalers
            self.save_model_and_scalers()
            
            return history, (test_actual, test_pred)
            
        except Exception as e:
            print(f"❌ LSTM training failed: {e}")
            return None, None
    
    def generate_forecast(self, df, forecast_hours=6):
        """Generate dynamic 6-hour forecast with correct timing"""
        print(f"\n🔮 Generating {forecast_hours}-hour forecast...")
        
        if self.model is None:
            print("❌ No trained model available")
            return None
            
        try:
            # Get latest data point
            latest_value = df['neel_level'].iloc[-1]
            latest_date_str = df['date_neel_level'].iloc[-1]
            latest_date = pd.to_datetime(latest_date_str)
            
            print(f"📍 Latest data: {latest_value:.2f}m at {latest_date}")
            current_alert = self.get_alert_level(latest_value)
            
            # Prepare features for forecasting
            features = df[self.feature_cols].values
            features_scaled = self.scaler_X.transform(features)
            
            # Get last sequence
            if len(features_scaled) < self.sequence_length:
                print("❌ Not enough data for prediction")
                return None
            
            forecasts = []
            forecast_dates = []
            forecast_alerts = []
            
            print("🕐 Generating hourly predictions:")
            
            # Generate predictions with rolling forecast
            forecast_df = df.tail(self.sequence_length).copy()
            
            for hour in range(1, forecast_hours + 1):
                # Get current features for prediction
                current_features = forecast_df[self.feature_cols].values
                current_features_scaled = self.scaler_X.transform(current_features)
                input_sequence = current_features_scaled.reshape(1, self.sequence_length, len(self.feature_cols))
                
                # Predict next value
                prediction_scaled = self.model.predict(input_sequence, verbose=0)[0][0]
                prediction_original = self.scaler_y.inverse_transform([[prediction_scaled]])[0][0]
                prediction_original = max(0.1, min(12.0, prediction_original))  # Reasonable bounds
                
                forecasts.append(prediction_original)
                
                # Calculate forecast time based on latest data time + hour
                forecast_time = latest_date + timedelta(hours=hour)
                forecast_dates.append(forecast_time)
                alert_level = self.get_alert_level(prediction_original)
                forecast_alerts.append(alert_level)
                
                # Display prediction
                alert_emoji = {'normal': '🟢', 'watch': '🟡', 'warning': '🟠', 'critical': '🔴'}
                print(f"   Hour +{hour}: {prediction_original:.2f}m {alert_emoji[alert_level]} ({alert_level.upper()}) at {forecast_time.strftime('%H:%M')}")
                
                # Update forecast dataframe for rolling prediction
                if hour < forecast_hours:
                    # Create new row with predicted data
                    new_row = forecast_df.iloc[-1].copy()
                    new_row['date_neel_level'] = forecast_time
                    new_row['neel_level'] = prediction_original
                    # Keep rainfall as is or set to 0 for future
                    if 'neel_rain' in new_row:
                        new_row['neel_rain'] = 0  # Assume no future rainfall
                    
                    # Add new row and recreate features
                    forecast_df = pd.concat([forecast_df, pd.DataFrame([new_row])], ignore_index=True)
                    forecast_df = self.create_essential_features(forecast_df)
                    
                    # Keep only the sequence length
                    forecast_df = forecast_df.tail(self.sequence_length).reset_index(drop=True)
            
            # Create forecast result
            forecast_result = {
                'forecasts': forecasts,
                'forecast_dates': forecast_dates,
                'forecast_alerts': forecast_alerts,
                'model_type': 'Dynamic LSTM',
                'generated_at': datetime.now(),
                'confidence': 'High',
                'latest_value': latest_value,
                'latest_date': latest_date,
                'current_alert': current_alert,
                'forecast_base_time': latest_date.isoformat()
            }
            
            return forecast_result
            
        except Exception as e:
            print(f"❌ Forecast generation failed: {e}")
            return None
    
    def save_forecast_to_csv(self, forecast_dict):
        """Save forecast to CSV for dashboard with correct timing"""
        print(f"\n💾 Saving forecast to {self.forecast_file}...")
        
        try:
            forecast_data = {
                'hour_ahead': list(range(1, 7)),
                'forecast_value': forecast_dict['forecasts'],
                'forecast_datetime': forecast_dict['forecast_dates'],
                'alert_level': forecast_dict.get('forecast_alerts', ['normal'] * 6),
                'model_type': [forecast_dict['model_type']] * 6,
                'confidence': [forecast_dict.get('confidence', 'High')] * 6,
                'generated_at': [forecast_dict['generated_at']] * 6,
                'based_on_latest': [forecast_dict['latest_date']] * 6,
                'latest_actual': [forecast_dict['latest_value']] * 6,
                'current_alert': [forecast_dict.get('current_alert', 'normal')] * 6,
                'forecast_base_time': [forecast_dict.get('forecast_base_time')] * 6
            }
            
            forecast_df = pd.DataFrame(forecast_data)
            forecast_df.to_csv(self.forecast_file, index=False)
            
            print(f"✅ Forecast saved to {self.forecast_file}")
            print(f"📊 Range: {min(forecast_dict['forecasts']):.2f}m to {max(forecast_dict['forecasts']):.2f}m")
            print(f"⏰ Base time: {forecast_dict['latest_date']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to save forecast: {e}")
            return False
    
    def run_production_forecasting(self):
        """Main production forecasting pipeline with dynamic retraining"""
        print("🚀 DYNAMIC LSTM FORECASTING SYSTEM")
        print("=" * 60)
        
        # Load data
        df = self.load_and_process_data()
        if df is None:
            print("❌ Data loading failed")
            return False
        
        # Check if model should be retrained
        should_retrain = self.should_retrain_model()
        model_loaded = False
        
        if not should_retrain:
            # Try to load existing model
            model_loaded = self.load_existing_model()
        
        if should_retrain or not model_loaded:
            print("\n🔄 RETRAINING MODEL...")
            
            # Feature engineering
            final_df = self.prepare_features(df)
            
            # Train model
            min_data_for_lstm = self.sequence_length + 100
            
            if len(final_df) >= min_data_for_lstm:
                history, test_results = self.train_model(final_df)
                
                if history is None:
                    print("❌ Training failed")
                    return False
            else:
                print(f"❌ Insufficient data ({len(final_df)} points, need >= {min_data_for_lstm})")
                return False
        else:
            print("\n♻️ USING EXISTING MODEL...")
            final_df = self.prepare_features(df)
        
        # Generate forecast
        print("\n🔮 GENERATING FORECAST...")
        forecast_dict = self.generate_forecast(final_df)
        
        if not forecast_dict:
            print("❌ Forecast generation failed")
            return False
        
        # Save results
        csv_success = self.save_forecast_to_csv(forecast_dict)
        
        if csv_success:
            print("\n✅ SUCCESS: DYNAMIC FORECASTING COMPLETED!")
            print("=" * 60)
            print(f"Model: {forecast_dict['model_type']}")
            print(f"Current: {forecast_dict['latest_value']:.2f}m ({forecast_dict.get('current_alert', 'normal').upper()})")
            print(f"Next hour: {forecast_dict['forecasts'][0]:.2f}m")
            print(f"6-hour range: {min(forecast_dict['forecasts']):.2f}m to {max(forecast_dict['forecasts']):.2f}m")
            print(f"Base time: {forecast_dict['latest_date']}")
        
        return csv_success

# Backward compatibility
SimplifiedNeelLevelLSTM = DynamicNeelLevelLSTM

def main():
    """Main execution function"""
    print("🔮 Dynamic LSTM Forecasting System")
    print("=" * 50)
    
    # Create dynamic forecaster
    forecaster = DynamicNeelLevelLSTM(
        sequence_length=72,
        dataset_file='deploy1.csv',
        forecast_file='forecast.csv'
    )
    
    try:
        success = forecaster.run_production_forecasting()
        
        if success:
            print(f"\n✅ Forecast saved to: {forecaster.forecast_file}")
            print(f"🔄 Model automatically retrained when needed")
            print(f"⏰ Forecast times based on latest data timestamp")
        else:
            print(f"\n❌ Forecasting failed")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

