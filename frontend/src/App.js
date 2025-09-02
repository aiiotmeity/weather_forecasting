import React, { useState, useEffect } from 'react';
// Import react-leaflet components
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
// Import the leaflet CSS
import 'leaflet/dist/leaflet.css';
// Import leaflet and fix the default icon issue with webpack
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;


// --- MAP COMPONENT (REWRITTEN) ---
const MapComponent = ({ onMarkerClick, isFullscreen = false, weatherData }) => {
  // Coordinates for Adishankara College, Kalady
  const collegeCoordinates = [10.1699, 76.4312];

  return (
    <div style={{ height: isFullscreen ? 'calc(100vh - 120px)' : '400px', width: '100%', borderRadius: '10px', overflow: 'hidden' }}>
      <MapContainer center={collegeCoordinates} zoom={15} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <Marker position={collegeCoordinates} eventHandlers={{ click: onMarkerClick }}>
          <Popup>
            <div style={{ textAlign: 'center' }}>
              <h3>Weather Station</h3>
              <p>Adishankara Engineering College</p>
              {weatherData && (
                <div style={{ marginTop: '10px' }}>
                  <strong>Current: {weatherData.temperature}°C</strong><br />
                  <small>Humidity: {weatherData.humidity}%</small>
                </div>
              )}
              {!isFullscreen && (
                <button onClick={onMarkerClick} style={{ background: '#4CAF50', color: 'white', border: 'none', padding: '5px 10px', borderRadius: '3px', cursor: 'pointer', marginTop: '5px' }}>
                  🔍 Full View
                </button>
              )}
            </div>
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
};

// --- NOTIFICATION COMPONENT (NO CHANGES) ---
const Notification = ({ message, type, show, onClose }) => {
  useEffect(() => {
    if (show) {
      const timer = setTimeout(onClose, 5000);
      return () => clearTimeout(timer);
    }
  }, [show, onClose]);

  return (
    <div
      className={`notification ${type} ${show ? 'show' : ''}`}
      style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '1rem 1.5rem',
        borderRadius: '8px',
        color: 'white',
        fontWeight: '500',
        zIndex: 1001,
        transform: show ? 'translateX(0)' : 'translateX(400px)',
        transition: 'transform 0.3s ease',
        backgroundColor: type === 'success' ? '#4CAF50' : '#f44336'
      }}
    >
      {message}
    </div>
  );
};

// --- WEATHER DISPLAY COMPONENT (NO CHANGES) ---
const WeatherDisplay = ({ data, loading, error }) => {
  if (loading) {
    return (
      <div className="weather-item">
        <span className="label">Loading weather data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="weather-item" style={{ borderLeftColor: '#f44336' }}>
        <span className="label">Error: {error}</span>
      </div>
    );
  }

  if (!data) return null;

  const timestamp = new Date(`${data.date} ${data.time}`).toLocaleString();

  const weatherItems = [
    { icon: '🌡️', label: 'Temperature', value: `${data.temperature}°C`, isTemp: true },
    { icon: '💧', label: 'Humidity', value: `${data.humidity}%` },
    { icon: '📊', label: 'Air Pressure', value: `${data.airPressure} hPa` },
    { icon: '🌧️', label: 'Rainfall (1h)', value: `${data.rainfall1h} mm` },
    { icon: '☔', label: 'Rainfall (24h)', value: `${data.rainfall24h} mm` },
    { icon: '🧭', label: 'Wind Direction', value: `${data.windDirection}°` },
    { icon: '💨', label: 'Wind Speed (Avg)', value: `${data.windSpeedAvg} m/s` },
    { icon: '🌪️', label: 'Wind Speed (Max)', value: `${data.windSpeedMax} m/s` }
  ];

  return (
    <>
      {weatherItems.map((item, index) => (
        <div key={index} className={`weather-item ${item.isTemp ? 'temperature' : ''}`}>
          <span className="label">
            <span style={{ marginRight: '0.5rem' }}>{item.icon}</span>
            {item.label}
          </span>
          <span className="value">{item.value}</span>
        </div>
      ))}
      <div style={{
        textAlign: 'center',
        color: '#666',
        fontSize: '0.85rem',
        marginTop: '1rem',
        paddingTop: '1rem',
        borderTop: '1px solid #eee'
      }}>
        🕒 Last updated: {timestamp}
      </div>
    </>
  );
};

// --- DATA REQUEST FORM COMPONENT (NO CHANGES) ---
const DataRequestForm = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    email: '',
    organization: '',
    start_date: '',
    end_date: '',
    data_type: '',
    purpose: ''
  });

  useEffect(() => {
    // Set default dates
    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(today.getDate() - 7);

    setFormData(prev => ({
      ...prev,
      end_date: today.toISOString().split('T')[0],
      start_date: weekAgo.toISOString().split('T')[0]
    }));
  }, []);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const validateAndSubmit = () => {
    // Validation
    if (!formData.email || !formData.start_date || !formData.end_date || !formData.data_type) {
      alert('Please fill in all required fields');
      return;
    }

    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailPattern.test(formData.email)) {
      alert('Please enter a valid email address');
      return;
    }

    // Date validation
    const startDate = new Date(formData.start_date);
    const endDate = new Date(formData.end_date);

    if (startDate > endDate) {
      alert('Start date must be before end date');
      return;
    }

    if (endDate > new Date()) {
      alert('End date cannot be in the future');
      return;
    }

    onSubmit(formData);
  };

  return (
    <div className="data-request-form">
      <div className="form-grid">
        <div className="form-group">
          <label htmlFor="email">Your Email Address</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            placeholder="your.email@example.com"
          />
        </div>
        <div className="form-group">
          <label htmlFor="organization">Organization (Optional)</label>
          <input
            type="text"
            id="organization"
            name="organization"
            value={formData.organization}
            onChange={handleChange}
            placeholder="Your organization"
          />
        </div>
        <div className="form-group">
          <label htmlFor="start_date">Start Date</label>
          <input
            type="date"
            id="start_date"
            name="start_date"
            value={formData.start_date}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="end_date">End Date</label>
          <input
            type="date"
            id="end_date"
            name="end_date"
            value={formData.end_date}
            onChange={handleChange}
            required
          />
        </div>
      </div>

      <div className="form-group" style={{ marginBottom: '1rem' }}>
        <label htmlFor="data_type">Data Parameters</label>
        <select
          id="data_type"
          name="data_type"
          value={formData.data_type}
          onChange={handleChange}
          required
        >
          <option value="">Select data type</option>
          <option value="all">All Parameters</option>
          <option value="temperature">Temperature Only</option>
          <option value="humidity">Humidity Only</option>
          <option value="pressure">Air Pressure Only</option>
          <option value="wind">Wind Data Only</option>
          <option value="rainfall">Rainfall Data Only</option>
          <option value="custom">Custom Selection</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="purpose">Purpose of Data Request</label>
        <textarea
          id="purpose"
          name="purpose"
          rows="3"
          value={formData.purpose}
          onChange={handleChange}
          placeholder="Please describe how you plan to use this weather data..."
        />
      </div>

      <button
        type="button"
        className="submit-btn"
        disabled={loading}
        onClick={validateAndSubmit}
      >
        {loading ? (
          <>🔄 Sending Request...</>
        ) : (
          <>✉️ Send Data Request</>
        )}
      </button>
    </div>
  );
};


// --- MAIN APP COMPONENT (NO CHANGES TO LOGIC) ---
const WeatherApp = () => {
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeSection, setActiveSection] = useState('dashboard');
  const [isFullscreenMap, setIsFullscreenMap] = useState(false);
  const [notification, setNotification] = useState({ show: false, message: '', type: '' });
  const [requestLoading, setRequestLoading] = useState(false);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000/api';

  useEffect(() => {
    fetchWeatherData();
    const interval = setInterval(fetchWeatherData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchWeatherData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/weather`);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setWeatherData(data);
      setLoading(false);
      setError(null);
    } catch (error) {
      console.error('Error fetching weather data:', error);
      setError('Failed to fetch');
      setLoading(false);
    }
  };

  const showNotification = (message, type) => {
    setNotification({ show: true, message, type });
  };

  const hideNotification = () => {
    setNotification({ show: false, message: '', type: '' });
  };

  const handleDataRequest = async (formData) => {
    setRequestLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/request-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        showNotification('Data request sent successfully! You will receive the data via email.', 'success');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to send request');
      }

    } catch (error) {
      console.error('Error sending data request:', error);
      showNotification(`Failed to send data request: ${error.message}`, 'error');
    } finally {
      setRequestLoading(false);
    }
  };

  const showFullscreenMap = () => {
    setIsFullscreenMap(true);
  };

  const closeFullscreenMap = () => {
    setIsFullscreenMap(false);
  };

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && isFullscreenMap) {
        closeFullscreenMap();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreenMap]);

  return (
    <div style={{
      fontFamily: 'Arial, sans-serif',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      minHeight: '100vh',
      margin: 0,
      padding: 0
    }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #1e3c72, #2a5298)',
        color: 'white',
        padding: '1rem 0',
        boxShadow: '0 4px 15px rgba(0,0,0,0.2)'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0 2rem',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ fontSize: '2rem', color: '#4CAF50' }}>🌤️</div>
            <div>
              <h1 style={{ fontSize: '1.8rem', fontWeight: '600', margin: 0 }}>
                Weather Monitoring System
              </h1>
              <p style={{ fontSize: '0.9rem', opacity: 0.8, margin: '0.2rem 0 0 0' }}>
                Adishankara Engineering College
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <button
              onClick={() => setActiveSection('dashboard')}
              style={{
                background: activeSection === 'dashboard' ? 'rgba(255,255,255,0.2)' : 'transparent',
                border: '2px solid rgba(255,255,255,0.3)',
                color: 'white',
                padding: '0.5rem 1rem',
                borderRadius: '25px',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}
            >
              📊 Dashboard
            </button>
            <button
              onClick={() => setActiveSection('data-request')}
              style={{
                background: activeSection === 'data-request' ? 'rgba(255,255,255,0.2)' : 'transparent',
                border: '2px solid rgba(255,255,255,0.3)',
                color: 'white',
                padding: '0.5rem 1rem',
                borderRadius: '25px',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}
            >
              📥 Data Request
            </button>
            <button
              onClick={showFullscreenMap}
              style={{
                background: 'transparent',
                border: '2px solid rgba(255,255,255,0.3)',
                color: 'white',
                padding: '0.5rem 1rem',
                borderRadius: '25px',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}
            >
              🔍 Full Map
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
        {activeSection === 'dashboard' && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: window.innerWidth > 768 ? '1fr 350px' : '1fr',
            gap: '2rem',
            marginBottom: '2rem'
          }}>
            {/* Map Section */}
            <div style={{
              background: 'white',
              borderRadius: '15px',
              padding: '1.5rem',
              boxShadow: '0 10px 30px rgba(0,0,0,0.1)'
            }}>
              <h2 style={{
                color: '#1e3c72',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                📍 Station Location
              </h2>
              <MapComponent
                onMarkerClick={showFullscreenMap}
                weatherData={weatherData}
              />
            </div>

            {/* Weather Panel */}
            <div style={{
              background: 'white',
              borderRadius: '15px',
              padding: '1.5rem',
              boxShadow: '0 10px 30px rgba(0,0,0,0.1)'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '1rem'
              }}>
                <h3 style={{
                  color: '#1e3c72',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  margin: 0
                }}>
                  🌡️ Live Weather Data
                </h3>
                <div style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  background: error ? '#f44336' : '#4CAF50',
                  animation: 'pulse 2s infinite'
                }} />
              </div>
              <div style={{ display: 'grid', gap: '1rem' }}>
                <WeatherDisplay data={weatherData} loading={loading} error={error} />
              </div>
              <div style={{
                marginTop: '1rem',
                textAlign: 'center',
                color: '#666',
                fontSize: '0.9rem'
              }}>
                🔄 Updates every 5 seconds
              </div>
            </div>
          </div>
        )}

        {activeSection === 'data-request' && (
          <div style={{
            background: 'white',
            borderRadius: '15px',
            padding: '1.5rem',
            boxShadow: '0 10px 30px rgba(0,0,0,0.1)'
          }}>
            <h2 style={{ color: '#1e3c72', marginBottom: '0.5rem' }}>
              📥 Request Historical Weather Data
            </h2>
            <p style={{ color: '#666', marginBottom: '1.5rem' }}>
              Request comprehensive weather data for any date range via email
            </p>
            <DataRequestForm onSubmit={handleDataRequest} loading={requestLoading} />
          </div>
        )}
      </div>

      {/* Fullscreen Map Overlay */}
      {isFullscreenMap && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(0,0,0,0.9)',
          zIndex: 1000
        }}>
          <div style={{ position: 'relative', width: '100%', height: '100%', padding: '2rem' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              color: 'white',
              marginBottom: '1rem'
            }}>
              <h2 style={{ margin: 0 }}>🗺️ Weather Station Location - Full View</h2>
              <button
                onClick={closeFullscreenMap}
                style={{
                  background: '#ff4757',
                  color: 'white',
                  border: 'none',
                  padding: '0.5rem 1rem',
                  borderRadius: '5px',
                  cursor: 'pointer',
                  fontSize: '1rem'
                }}
              >
                ❌ Close
              </button>
            </div>
            <MapComponent
              isFullscreen={true}
              weatherData={weatherData}
              onMarkerClick={closeFullscreenMap} // Added this so clicking the marker can also close fullscreen
            />
          </div>
        </div>
      )}

      {/* Notification */}
      <Notification
        message={notification.message}
        type={notification.type}
        show={notification.show}
        onClose={hideNotification}
      />

      {/* Custom Styles */}
      <style jsx global>{`
        .leaflet-container {
          border-radius: 10px;
        }
      `}</style>
      <style jsx>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }

        .weather-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.8rem;
          background: #f8f9fa;
          border-radius: 8px;
          border-left: 4px solid #4CAF50;
        }

        .weather-item .label {
          display: flex;
          align-items: center;
          color: #555;
          font-weight: 500;
        }

        .weather-item .value {
          font-weight: 600;
          color: #1e3c72;
        }

        .weather-item.temperature .value {
          font-size: 1.2rem;
          color: #ff6b35;
        }

        .form-grid {
          display: grid;
          grid-template-columns: ${typeof window !== 'undefined' && window.innerWidth > 768 ? '1fr 1fr' : '1fr'};
          gap: 1rem;
          margin-bottom: 1rem;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .form-group label {
          color: #1e3c72;
          font-weight: 500;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
          padding: 0.8rem;
          border: 2px solid #e0e0e0;
          border-radius: 8px;
          font-size: 1rem;
          transition: border-color 0.3s ease;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
          outline: none;
          border-color: #4CAF50;
        }

        .submit-btn {
          background: linear-gradient(135deg, #4CAF50, #45a049);
          color: white;
          border: none;
          padding: 1rem 2rem;
          border-radius: 25px;
          font-size: 1rem;
          cursor: pointer;
          transition: transform 0.3s ease;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          justify-content: center;
          margin: 0 auto;
        }

        .submit-btn:hover:not(:disabled) {
          transform: translateY(-2px);
        }

        .submit-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        @media (max-width: 768px) {
          .form-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

// FIX: Corrected export from 'app' to 'WeatherApp'
export default WeatherApp;