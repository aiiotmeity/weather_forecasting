import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from 'recharts';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import Homepage from './Homepage';
import './App.css';

// --- LEAFLET ICON FIX ---
let DefaultIcon = L.icon({
    iconUrl: icon, 
    shadowUrl: iconShadow, 
    iconSize: [25, 41], 
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

// --- ENHANCED HEADER COMPONENT ---
const Header = ({ onLiveDataClick, onRequestDataClick, onHistoricalChartsClick, onHomeClick, isConnected, weatherData }) => {
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setCurrentTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    const getConnectionStatus = () => {
        if (isConnected && weatherData) {
            return {
                status: 'connected',
                text: 'Live',
                icon: '●'
            };
        } else {
            return {
                status: 'disconnected',
                text: 'Offline',
                icon: '●'
            };
        }
    };

    const connectionInfo = getConnectionStatus();

    return (
        <header className="app-header">
            <div className="breadcrumb-nav" style={{
                position: 'absolute',
                top: '10px',
                left: '24px',
                fontSize: '0.8rem',
                opacity: '0.8'
            }}>
                <span 
                    onClick={onHomeClick}
                    style={{ cursor: 'pointer', textDecoration: 'underline' }}
                >
                    Home
                </span>
                <span style={{ margin: '0 8px' }}>›</span>
                <span>Weather Dashboard</span>
            </div>

            <div className="header-logo" onClick={onHomeClick} style={{ cursor: 'pointer' }}>
                <img 
                    src="/api/placeholder/48/48" 
                    alt="Weather Station Logo" 
                    onError={(e) => {
                        e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDgiIGhlaWdodD0iNDgiIHZpZXdCb3g9IjAgMCA0OCA0OCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjQiIGN5PSIyNCIgcj0iMjQiIGZpbGw9InVybCgjZ3JhZGllbnQwX2xpbmVhcl8xXzEpIi8+CjxwYXRoIGQ9Ik0yNCA4QzE1LjE2IDggOCAxNS4xNiA4IDI0UzE1LjE2IDQwIDI0IDQwUzQwIDMyLjg0IDQwIDI0UzMyLjg0IDggMjQgOFpNMjQgMzZDMTcuMzcgMzYgMTIgMzAuNjMgMTIgMjRTMTcuMzcgMTIgMjQgMTJTMzYgMTcuMzcgMzYgMjRTMzAuNjMgMzYgMjQgMzZaIiBmaWxsPSJ3aGl0ZSIvPgo8cGF0aCBkPSJNMjQgMTZDMTkuNTggMTYgMTYgMTkuNTggMTYgMjRTMTkuNTggMzIgMjQgMzJTMzIgMjguNDIgMzIgMjRTMjguNDIgMTYgMjQgMTZaIiBmaWxsPSJ3aGl0ZSIvPgo8ZGVmcz4KPGxpbmVhckdyYWRpZW50IGlkPSJncmFkaWVudDBfbGluZWFyXzFfMSIgeDE9IjAiIHkxPSIwIiB4Mj0iNDgiIHkyPSI0OCIgZ3JhZGllbnRVbml0cz0idXNlclNwYWNlT25Vc2UiPgo8c3RvcCBzdG9wLWNvbG9yPSIjNjY3RUVBIi8+CjxzdG9wIG9mZnNldD0iMSIgc3RvcC1jb2xvcj0iIzc2NEJBMiIvPgo8L2xpbmVhckdyYWRpZW50Pgo8L2RlZnM+Cjwvc3ZnPgo=';
                    }}
                />
                <div className="header-title">
                    <h3>Weather Monitoring Hub</h3>
                    <p>Adishankara Engineering College • {currentTime.toLocaleTimeString()}</p>
                </div>
            </div>
            
            <div className="header-nav">
                <div className={`header-status ${connectionInfo.status}`}>
                    <span className="status-dot"></span>
                    {connectionInfo.text}
                    {weatherData && (
                        <span style={{ marginLeft: '8px', fontSize: '0.8rem' }}>
                            {weatherData.temperature}°C
                        </span>
                    )}
                </div>
                
                <button onClick={onLiveDataClick} className="nav-btn live-data-btn">
                    <span>📊</span>
                    <span>Live Data</span>
                </button>

                <button onClick={onHistoricalChartsClick} className="nav-btn historical-btn">
                    <span>📈</span>
                    <span>Historical Data</span>
                </button>
                
                <button onClick={onRequestDataClick} className="nav-btn request-data-btn">
                    <span>📥</span>
                    <span>Request Data</span>
                </button>
                
                <button onClick={onHomeClick} className="nav-btn home-btn">
                    <span>🏠</span>
                    <span>Home</span>
                </button>
                
                <button onClick={() => window.location.reload()} className="nav-btn refresh-btn">
                    <span>🔄</span>
                    <span>Refresh</span>
                </button>
            </div>
        </header>
    );
};

// --- MAP COMPONENT ---
const MapComponent = ({ onMarkerClick, weatherData }) => {
    const collegeCoordinates = [10.1699, 76.4312];
    
    return (
        <div className="map-container">
            <MapContainer 
                center={collegeCoordinates} 
                zoom={13} 
                style={{ height: '100%', width: '100%' }}
                zoomControl={true}
                scrollWheelZoom={true}
            >
                <TileLayer 
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" 
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                <Marker 
                    position={collegeCoordinates} 
                    eventHandlers={{ click: onMarkerClick }}
                >
                    <Popup>
                        <div style={{ textAlign: 'center', minWidth: '200px' }}>
                            <b>🌦️ Adishankara Weather Station</b>
                            <br />
                            <small>Click to view live data</small>
                            {weatherData && (
                                <div style={{ marginTop: '8px', fontSize: '14px' }}>
                                    <div>🌡️ {weatherData.temperature}°C</div>
                                    <div>💧 {weatherData.humidity}%</div>
                                </div>
                            )}
                        </div>
                    </Popup>
                </Marker>
            </MapContainer>
        </div>
    );
};

// --- NOTIFICATION COMPONENT ---
const Notification = ({ message, type, show, onClose }) => {
    useEffect(() => {
        if (show) {
            const timer = setTimeout(onClose, 6000);
            return () => clearTimeout(timer);
        }
    }, [show, onClose]);

    const getNotificationIcon = () => {
        switch (type) {
            case 'success': return '✅';
            case 'error': return '❌';
            case 'warning': return '⚠️';
            default: return 'ℹ️';
        }
    };

    return (
        <div className={`notification ${type} ${show ? 'show' : ''}`}>
            <span style={{ marginRight: '8px', fontSize: '1.2rem' }}>
                {getNotificationIcon()}
            </span>
            {message}
        </div>
    );
};

// --- WEATHER DISPLAY COMPONENT ---
const WeatherDisplay = ({ data, loading, error }) => {
    if (loading) {
        return (
            <div className="weather-item">
                <span className="label">
                    <div className="loading-spinner"></div>
                    Loading weather data...
                </span>
            </div>
        );
    }
    
    if (error || !data) {
        return (
            <div className="weather-item error">
                <span className="label">❌ {error || 'No data available'}</span>
                <button 
                    onClick={() => window.location.reload()} 
                    style={{ 
                        background: 'none', 
                        border: '1px solid #e74c3c', 
                        color: '#e74c3c',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }}
                >
                    Retry
                </button>
            </div>
        );
    }

    const weatherItems = [
        { 
            icon: '🌡️', 
            label: 'Temperature', 
            value: `${data.temperature}°C`,
            description: 'Current air temperature'
        },
        { 
            icon: '💧', 
            label: 'Humidity', 
            value: `${data.humidity}%`,
            description: 'Relative humidity level'
        },
        { 
            icon: '📊', 
            label: 'Air Pressure', 
            value: `${data.airPressure} hPa`,
            description: 'Atmospheric pressure'
        },
        { 
            icon: '💨', 
            label: 'Wind Speed', 
            value: `${data.WindSpeedAvg} m/s`,
            description: 'Average wind velocity'
        },
        { 
            icon: '🧭', 
            label: 'Wind Direction', 
            value: `${data.windDirection}°`,
            description: 'Wind direction in degrees'
        },
        { 
            icon: '🌧️', 
            label: 'Rainfall (1h)', 
            value: `${data.rainfall1h || 0} mm`,
            description: 'Precipitation in last hour'
        },
        { 
            icon: '☔', 
            label: 'Rainfall (24h)', 
            value: `${data.rainfall24h || 0} mm`,
            description: 'Precipitation in last 24 hours'
        }
    ];

    return (
        <div>
            {weatherItems.map((item, index) => (
                <div key={index} className="weather-item" title={item.description}>
                    <span className="label">
                        <span className="icon">{item.icon}</span>
                        {item.label}
                    </span>
                    <span className="value">{item.value}</span>
                </div>
            ))}
            <div className="timestamp">
                🕐 Last updated: {new Date(`${data.date} ${data.time}`).toLocaleString()}
                <br />
                <small>Data refreshes every 30 seconds</small>
            </div>
        </div>
    );
};

// --- NEW: HISTORICAL CHARTS COMPONENT ---
// --- NEW: HISTORICAL CHARTS COMPONENT ---
const HistoricalCharts = ({ onFetchHistoricalData, historicalData, historicalLoading, historicalError }) => {
    // State to manage user selections
    const [selectedDays, setSelectedDays] = useState(5);
    // NEW: State for the single parameter selection. Default to 'temperature'.
    const [selectedParameter, setSelectedParameter] = useState('temperature');

    // Configuration for each selectable parameter
    // This makes it easy to define the label, color, and chart type for each option
    const parameterOptions = [
        { value: 'temperature', label: 'Temperature (°C)', color: '#e74c3c', type: 'line' },
        { value: 'humidity', label: 'Humidity (%)', color: '#3498db', type: 'line' },
        { value: 'airPressure', label: 'Air Pressure (hPa)', color: '#8e44ad', type: 'line' },
        { value: 'WindSpeedAvg', label: 'Avg. Wind Speed (m/s)', color: '#e67e22', type: 'line' },
        { value: 'rainfall1h', label: 'Rainfall - 1 Hour (mm)', color: '#27ae60', type: 'bar' },
        { value: 'rainfall24h', label: 'Rainfall - 24 Hours (mm)', color: '#3498db', type: 'bar' },
    ];

    // Find the full configuration for the currently selected parameter
    const selectedParamConfig = parameterOptions.find(p => p.value === selectedParameter);

    // Function to trigger the data fetch
    const handleFetchData = () => {
        onFetchHistoricalData(selectedDays); // We fetch all data, then display the selected parameter
    };

    // Fetch data when the component first loads
    useEffect(() => {
        handleFetchData();
    }, []);

    const formatTimestamp = (timestamp) => {
        try {
            const date = new Date(timestamp);
            return date.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return timestamp;
        }
    };

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '1px solid #ccc',
                    borderRadius: '8px',
                    padding: '10px',
                    backdropFilter: 'blur(10px)'
                }}>
                    <p style={{ margin: 0, fontWeight: 'bold' }}>{formatTimestamp(label)}</p>
                    {payload.map((entry, index) => (
                        <p key={index} style={{ margin: '2px 0', color: entry.color }}>
                            {entry.name}: {entry.value}
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };

    if (historicalLoading) {
        return (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
                <div className="loading-spinner" style={{ margin: '0 auto 1rem' }}></div>
                <p>Loading historical weather data...</p>
            </div>
        );
    }

    if (historicalError) {
        return (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#e74c3c' }}>
                <p>❌ {historicalError}</p>
                <button onClick={handleFetchData} className="submit-btn" style={{ marginTop: '1rem' }}>
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div>
            {/* --- UPDATED: Controls Section --- */}
            <div style={{ 
                display: 'flex', 
                gap: '1rem', 
                marginBottom: '1.5rem',
                padding: '1rem',
                backgroundColor: 'rgba(255, 255, 255, 0.8)',
                borderRadius: '12px',
                flexWrap: 'wrap',
                alignItems: 'center'
            }}>
                {/* Days Range Selector */}
                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', fontSize: '0.9rem' }}>
                        📅 Date Range:
                    </label>
                    <select 
                        value={selectedDays} 
                        onChange={(e) => setSelectedDays(parseInt(e.target.value))}
                        style={{ padding: '0.5rem', borderRadius: '8px', border: '2px solid rgba(102, 126, 234, 0.2)', backgroundColor: 'white' }}>
                        
                        <option value={3}>Last 3 Days</option>
                        <option value={5}>Last 5 Days</option>
                        <option value={7}>Last 7 Days</option>
                        <option value={15}>Last 15 Days</option>
                        <option value={30}>Last 30 Days</option>
                    </select>
                </div>

                {/* NEW: Parameter Selector */}
                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', fontSize: '0.9rem' }}>
                        📊 Parameter:
                    </label>
                    <select 
                        value={selectedParameter} 
                        onChange={(e) => setSelectedParameter(e.target.value)}
                        style={{ padding: '0.5rem', borderRadius: '8px', border: '2px solid rgba(102, 126, 234, 0.2)', backgroundColor: 'white' }}>
                        {parameterOptions.map(option => (
                            <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                    </select>
                </div>
                
                <button 
                    onClick={handleFetchData}
                    className="submit-btn"
                    disabled={historicalLoading}
                    style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', height: 'fit-content' }}
                >
                    📊 Update Chart
                </button>
            </div>

            {/* --- UPDATED: Single Dynamic Chart Section --- */}
            {historicalData && historicalData.length > 0 ? (
                <div>
                    <div style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: 'rgba(102, 126, 234, 0.1)', borderRadius: '8px' }}>
                        <strong>📈 Showing {historicalData.length} records</strong> for{' '}
                        <strong>{selectedParamConfig.label}</strong>
                    </div>

                    <div style={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', borderRadius: '12px', padding: '1rem' }}>
                        <ResponsiveContainer width="100%" height={350}>
                            {/* Conditionally render a Line or Bar chart based on config */}
                            {selectedParamConfig.type === 'line' ? (
                                <LineChart data={historicalData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(102, 126, 234, 0.1)" />
                                    <XAxis dataKey="timestamp" tickFormatter={formatTimestamp} angle={-45} textAnchor="end" height={60} fontSize={12} />
                                    <YAxis />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Legend />
                                    <Line 
                                        type="monotone" 
                                        dataKey={selectedParamConfig.value} 
                                        stroke={selectedParamConfig.color}
                                        name={selectedParamConfig.label}
                                        strokeWidth={2}
                                        dot={{ r: 2 }}
                                    />
                                </LineChart>
                            ) : (
                                <BarChart data={historicalData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(102, 126, 234, 0.1)" />
                                    <XAxis dataKey="timestamp" tickFormatter={formatTimestamp} angle={-45} textAnchor="end" height={60} fontSize={12} />
                                    <YAxis />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Legend />
                                    <Bar 
                                        dataKey={selectedParamConfig.value} 
                                        fill={selectedParamConfig.color}
                                        name={selectedParamConfig.label}
                                        radius={[2, 2, 0, 0]}
                                    />
                                </BarChart>
                            )}
                        </ResponsiveContainer>
                    </div>
                </div>
            ) : (
                <div style={{ textAlign: 'center', padding: '2rem', color: '#6c757d' }}>
                    <p>📈 No historical data available for the selected range.</p>
                </div>
            )}
        </div>
    );
};

// --- DATA REQUEST FORM COMPONENT ---
const DataRequestForm = ({ onSubmit, loading }) => {
    const [formData, setFormData] = useState({
        email: '',
        organization: '',
        start_date: '',
        end_date: '',
        data_type: 'all',
        purpose: ''
    });

    const [errors, setErrors] = useState({});

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
        
        if (errors[name]) {
            setErrors({ ...errors, [name]: '' });
        }
    };

    const validateForm = () => {
        const newErrors = {};
        
        if (!formData.email) {
            newErrors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = 'Email is invalid';
        }
        
        if (!formData.start_date) {
            newErrors.start_date = 'Start date is required';
        }
        
        if (!formData.end_date) {
            newErrors.end_date = 'End date is required';
        }
        
        if (formData.start_date && formData.end_date) {
            if (new Date(formData.start_date) > new Date(formData.end_date)) {
                newErrors.end_date = 'End date must be after start date';
            }
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const validateAndSubmit = () => {
        if (validateForm()) {
            onSubmit(formData);
        }
    };

    const dataTypeOptions = [
        { value: 'all', label: 'All Parameters' },
        { value: 'temperature', label: 'Temperature Only' },
        { value: 'humidity', label: 'Humidity Only' },
        { value: 'pressure', label: 'Air Pressure Only' },
        { value: 'wind', label: 'Wind Data Only' },
        { value: 'rainfall', label: 'Rainfall Data Only' }
    ];

    return (
        <div className="data-request-form">
            <div className="form-group">
                <label>Your Email Address *</label>
                <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="your.email@domain.com"
                    required
                    style={{ borderColor: errors.email ? '#e74c3c' : undefined }}
                />
                {errors.email && <small style={{ color: '#e74c3c', marginTop: '4px' }}>{errors.email}</small>}
            </div>

            <div className="form-group">
                <label>Organization (Optional)</label>
                <input
                    type="text"
                    name="organization"
                    value={formData.organization}
                    onChange={handleChange}
                    placeholder="Your institution or company"
                />
            </div>

            <div className="form-grid">
                <div className="form-group">
                    <label>Start Date *</label>
                    <input
                        type="date"
                        name="start_date"
                        value={formData.start_date}
                        onChange={handleChange}
                        max={new Date().toISOString().split('T')[0]}
                        required
                        style={{ borderColor: errors.start_date ? '#e74c3c' : undefined }}
                    />
                    {errors.start_date && <small style={{ color: '#e74c3c', marginTop: '4px' }}>{errors.start_date}</small>}
                </div>

                <div className="form-group">
                    <label>End Date *</label>
                    <input
                        type="date"
                        name="end_date"
                        value={formData.end_date}
                        onChange={handleChange}
                        max={new Date().toISOString().split('T')[0]}
                        required
                        style={{ borderColor: errors.end_date ? '#e74c3c' : undefined }}
                    />
                    {errors.end_date && <small style={{ color: '#e74c3c', marginTop: '4px' }}>{errors.end_date}</small>}
                </div>
            </div>

            <div className="form-group">
                <label>Data Type</label>
                <select
                    name="data_type"
                    value={formData.data_type}
                    onChange={handleChange}
                >
                    {dataTypeOptions.map(option => (
                        <option key={option.value} value={option.value}>
                            {option.label}
                        </option>
                    ))}
                </select>
            </div>

            <div className="form-group">
                <label>Purpose of Request</label>
                <textarea
                    name="purpose"
                    rows="4"
                    value={formData.purpose}
                    onChange={handleChange}
                    placeholder="Briefly describe how you plan to use this data"
                />
            </div>

            <button
                type="button"
                className="submit-btn"
                disabled={loading}
                onClick={validateAndSubmit}
            >
                {loading ? (
                    <>
                        <div className="loading-spinner" style={{ marginRight: '8px' }}></div>
                        Submitting Request...
                    </>
                ) : (
                    'Submit for Approval'
                )}
            </button>

            <div style={{ 
                marginTop: '1rem', 
                padding: '1rem', 
                backgroundColor: 'rgba(102, 126, 234, 0.1)', 
                borderRadius: '8px',
                fontSize: '0.9rem',
                color: '#667eea'
            }}>
                <strong>📋 Process:</strong>
                <ol style={{ margin: '8px 0', paddingLeft: '20px' }}>
                    <li>You submit a request through the system.</li>
                    <li>The admin verifies your details.</li>
                    <li>Once approved, your request is processed.</li>
                    <li>You’ll receive the requested data in your email as a CSV file.</li>
                </ol>
            </div>
        </div>
    );
};

// --- SIDEBAR COMPONENT ---
const Sidebar = ({ isOpen, onClose, activeTab, setActiveTab, ...props }) => {
    const getTabTitle = () => {
        switch (activeTab) {
            case 'live': return '📊 Live Weather Data';
            case 'historical': return '📈 Historical Data';
            case 'request': return '📥 Request Historical Data';
            default: return '📊 Weather Data';
        }
    };

    return (
        <div className={`sidebar ${isOpen ? 'open' : ''}`}>
            <div className="sidebar-header">
                <div className="sidebar-title">
                    <h3>{getTabTitle()}</h3>
                </div>
                <button className="close-btn" onClick={onClose} title="Close sidebar">
                    ×
                </button>
            </div>

            <div className="sidebar-tabs">
                <button
                    className={activeTab === 'live' ? 'active' : ''}
                    onClick={() => setActiveTab('live')}
                >
                    📊 Live Data
                </button>
                <button
                    className={activeTab === 'historical' ? 'active' : ''}
                    onClick={() => setActiveTab('historical')}
                >
                    📈 Charts
                </button>
                <button
                    className={activeTab === 'request' ? 'active' : ''}
                    onClick={() => setActiveTab('request')}
                >
                    📥 Request Data
                </button>
            </div>

            <div className="sidebar-content">
                {activeTab === 'live' && (
                    <WeatherDisplay
                        data={props.weatherData}
                        loading={props.loading}
                        error={props.error}
                    />
                )}
                {activeTab === 'historical' && (
                    <HistoricalCharts
                        onFetchHistoricalData={props.onFetchHistoricalData}
                        historicalData={props.historicalData}
                        historicalLoading={props.historicalLoading}
                        historicalError={props.historicalError}
                    />
                )}
                {activeTab === 'request' && (
                    <DataRequestForm
                        onSubmit={props.handleDataRequest}
                        loading={props.requestLoading}
                    />
                )}
            </div>
        </div>
    );
};

// --- MAIN APP COMPONENT ---
const App = () => {
    // State for navigation
    const [currentView, setCurrentView] = useState('homepage');
    
    // Weather app state
    const [weatherData, setWeatherData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [notification, setNotification] = useState({ show: false, message: '', type: '' });
    const [requestLoading, setRequestLoading] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [activeTab, setActiveTab] = useState('live');

    // NEW: Historical data state
    const [historicalData, setHistoricalData] = useState([]);
    const [historicalLoading, setHistoricalLoading] = useState(false);
    const [historicalError, setHistoricalError] = useState(null);

    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

    const fetchWeatherData = useCallback(async () => {
        try {
            setLoading(true);
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 8000);

            const response = await fetch(`${API_URL}/weather`, {
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            setWeatherData(data);
            setError(null);
        } catch (err) {
            if (err.name === 'AbortError') {
                setError('Request timeout - Please check your connection');
            } else {
                setError(`Connection failed: ${err.message}`);
            }
            console.error('Weather data fetch error:', err);
        } finally {
            setLoading(false);
        }
    }, [API_URL]);

    // NEW: Fetch historical data function
    const fetchHistoricalData = useCallback(async (days = 5, parameter = 'all') => {
        try {
            setHistoricalLoading(true);
            setHistoricalError(null);
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000);

            const response = await fetch(`${API_URL}/historical-data?days=${days}&parameter=${parameter}`, {
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}: Request failed`);
            }

            const data = await response.json();
            setHistoricalData(data.data || []);
            
        } catch (err) {
            if (err.name === 'AbortError') {
                setHistoricalError('Request timeout - Please try again');
            } else {
                setHistoricalError(err.message);
            }
            console.error('Historical data fetch error:', err);
        } finally {
            setHistoricalLoading(false);
        }
    }, [API_URL]);

    useEffect(() => {
        fetchWeatherData();
        const interval = setInterval(fetchWeatherData, 30000);
        return () => clearInterval(interval);
    }, [fetchWeatherData]);

    const showNotification = (message, type) => {
        setNotification({ show: true, message, type });
    };

    const handleDataRequest = async (formData) => {
        setRequestLoading(true);
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000);

            const response = await fetch(`${API_URL}/request-data`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || `HTTP ${response.status}: Request failed`);
            }

            showNotification(
                'Success! Your request has been submitted for admin approval.',
                'success'
            );
            setIsSidebarOpen(false);
        } catch (err) {
            if (err.name === 'AbortError') {
                showNotification('Request timeout - Please try again', 'error');
            } else {
                showNotification(`Error: ${err.message}`, 'error');
            }
            console.error('Data request error:', err);
        } finally {
            setRequestLoading(false);
        }
    };

    const openSidebarWithTab = (tab) => {
        setActiveTab(tab);
        setIsSidebarOpen(true);
    };

    // Navigation functions
    const navigateToWeather = (tab = 'live') => {
        setCurrentView('weather');
        setActiveTab(tab);
        if (tab === 'request' || tab === 'historical') {
            setIsSidebarOpen(true);
        }
    };

    const navigateToHome = () => {
        setCurrentView('homepage');
        setIsSidebarOpen(false);
    };

    // Render based on current view
    if (currentView === 'homepage') {
        return <Homepage onNavigateToWeather={navigateToWeather} />;
    }

    // Weather dashboard view
    return (
        <div className="app-container">
            <Header
                onLiveDataClick={() => openSidebarWithTab('live')}
                onHistoricalChartsClick={() => openSidebarWithTab('historical')}
                onRequestDataClick={() => openSidebarWithTab('request')}
                onHomeClick={navigateToHome}
                isConnected={!!weatherData && !error}
                weatherData={weatherData}
            />

            <Sidebar
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                weatherData={weatherData}
                loading={loading}
                error={error}
                handleDataRequest={handleDataRequest}
                requestLoading={requestLoading}
                onFetchHistoricalData={fetchHistoricalData}
                historicalData={historicalData}
                historicalLoading={historicalLoading}
                historicalError={historicalError}
            />

            <MapComponent
                onMarkerClick={() => openSidebarWithTab('live')}
                weatherData={weatherData}
            />

            <Notification
                {...notification}
                onClose={() => setNotification({ ...notification, show: false })}
            />
        </div>
    );
};

export default App;