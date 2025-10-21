import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from 'recharts';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import './App.css';
import { useLocation, useNavigate } from 'react-router-dom';

// --- LEAFLET ICON FIX ---
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

// --- ENHANCED DATA SOURCE FOR STATIONS ---
const weatherStations = [
    {
        id: 'weather-v2',
        name: 'Adishankara Weather Station',
        location: 'Kalady, Kerala',
        coordinates: [10.1699, 76.4312],
        status: 'active',
        description: 'Primary weather monitoring station with full sensor suite'
    },
    {
        id: 'station-Airport Road',
        name: 'Kochi Airport Road Station',
        location: 'Ernakulam, Kerala',
        coordinates: [10.15559139488071, 76.39268169730792],
        status: 'development',
        description: 'Station under development - Limited functionality'
    },
];

// --- UTILITY FUNCTIONS ---
const getWindDirection = (degrees) => {
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    return directions[Math.round(degrees / 22.5) % 16];
};

// --- NOTIFICATION COMPONENT ---
const Notification = ({ message, type, onClose }) => {
    useEffect(() => {
        const timer = setTimeout(onClose, 4000);
        return () => clearTimeout(timer);
    }, [onClose]);

    return (
        <div className={`notification ${type}`}>
            <span>{message}</span>
            <button onClick={onClose}>×</button>
        </div>
    );
};

// --- LOADING COMPONENT ---
const LoadingSpinner = ({ message = "Loading..." }) => (
    <div className="loading-spinner">
        <div className="spinner"></div>
        <span style={{ marginLeft: '8px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{message}</span>
    </div>
);

// --- COMPACT HEADER COMPONENT ---
const Header = ({ currentStation, onHomeClick, onSidebarToggle, isConnected, weatherData, isSidebarOpen }) => (
    <header className="app-header">
        <div className="header-left">
            <button onClick={onHomeClick} className="header-home-btn" aria-label="Go to homepage">
                🏠 Home
            </button>
            {currentStation && (
                <div className="header-station-info">
                    <span className="station-name">{currentStation.name}</span>
                    <span className="station-location">{currentStation.location}</span>
                </div>
            )}
        </div>
        <div className="header-right">
            <div className={`header-status ${isConnected ? 'connected' : 'disconnected'}`}>
                <span className="status-dot"></span>
                {isConnected ? 'Live' : 'Offline'}
                {weatherData && isConnected && (
                    <span className="live-temp">{weatherData.temperature}°C</span>
                )}
            </div>
            <button
                onClick={() => window.location.reload()}
                className="header-icon-btn"
                title="Refresh Page"
                aria-label="Refresh page"
            >
                🔄
            </button>
            <button
                onClick={onSidebarToggle}
                className={`header-icon-btn ${isSidebarOpen ? 'active' : ''}`}
                title="Toggle Data Panel"
                aria-label="Toggle data panel"
            >
                📊
            </button>
        </div>
    </header>
);

// --- ENHANCED MAP COMPONENT ---
const WeatherMap = ({ stations, onStationSelect, currentStationId }) => {
    const [selectedStation, setSelectedStation] = useState(null);

    const handleMarkerClick = (station) => {
        setSelectedStation(station);
        onStationSelect(station.id);
    };

    return (
        <div className="map-container">
            <MapContainer
                center={[10.05, 76.35]}
                zoom={11}
                style={{ height: '100%', width: '100%' }}
                zoomControl={true}
            >
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                {stations.map(station => (
                    <Marker
                        key={station.id}
                        position={station.coordinates}
                        eventHandlers={{
                            click: () => handleMarkerClick(station)
                        }}
                        className={station.status === 'development' ? 'inactive-marker' : 'active-marker'}
                    >
                        <Popup>
                            <div className="popup-content">
                                <h4>{station.name}</h4>
                                <p>{station.location}</p>
                                <p className="station-description">{station.description}</p>
                                {station.status === 'development' ? (
                                    <div className="status-badge development">
                                        🚧 Under Development
                                    </div>
                                ) : (
                                    <div className="status-badge active">
                                        ✅ Click to view live data
                                    </div>
                                )}
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>

            {!selectedStation && (
                <div className="map-overlay">
                    <div className="map-instructions">
                        <h3>🗺️ Weather Station Network</h3>
                        <p>Click on any active station marker to view real-time weather data</p>
                        <div className="legend">
                            <div className="legend-item">
                                <span className="legend-dot active"></span>
                                <span>Active Station</span>
                            </div>
                            <div className="legend-item">
                                <span className="legend-dot development"></span>
                                <span>Under Development</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// --- COMPACT WEATHER DISPLAY COMPONENT ---
const WeatherDisplay = ({ data, loading, error, stationInfo }) => {
    if (loading) return <LoadingSpinner message="Fetching weather data..." />;

    if (error || !data) {
        return (
            <div className="error-message">
                <h4>⚠️ Data Unavailable</h4>
                <p>{error || 'No data available for this station'}</p>
                {stationInfo?.status === 'development' && (
                    <p>This station is currently under development.</p>
                )}
            </div>
        );
    }

    const weatherItems = [
        {
            icon: '🌡️',
            label: 'Temperature',
            value: `${data.temperature}°C`,
            trend: data.temperatureTrend || 'stable'
        },
        {
            icon: '💧',
            label: 'Humidity',
            value: `${data.humidity}%`,
            trend: data.humidityTrend || 'stable'
        },
        {
            icon: '📊',
            label: 'Air Pressure',
            value: `${data.airPressure} hPa`,
            trend: data.pressureTrend || 'stable'
        },
        {
            icon: '💨',
            label: 'Wind Speed',
            value: `${data.WindSpeedAvg} m/s`,
            trend: data.windTrend || 'stable'
        },
        {
            icon: '🧭',
            label: 'Wind Direction',
            value: `${data.windDirection}°`,
            description: getWindDirection(data.windDirection)
        },
        {
            icon: '🌧️',
            label: 'Rainfall (1h)',
            value: `${data.rainfall1h || 0} mm`,
            trend: data.rainfallTrend || 'stable'
        },
    ];

    return (
        <div className="weather-display">
            <div className="station-header">
                <h4>{stationInfo?.name}</h4>
                <span className="status-indicator active">🟢 Live Data</span>
            </div>

            <div className="weather-grid">
                {weatherItems.map((item, index) => (
                    <div key={index} className="weather-item">
                        <div className="label">
                            <span className="icon">{item.icon}</span>
                            <span>{item.label}</span>
                        </div>
                        <div className="value-container">
                            <span className="value">{item.value}</span>
                            {item.description && (
                                <span className="description">{item.description}</span>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            <div className="timestamp">
                <span className="update-time">
                    Last updated: {new Date(`${data.date} ${data.time}`).toLocaleString()}
                </span>
                <span className="auto-refresh"></span>
            </div>
        </div>
    );
};

// --- COMPACT HISTORICAL CHARTS COMPONENT ---
const HistoricalCharts = ({ historicalData, historicalLoading, historicalError, onFetchHistoricalData, currentStation }) => {
    const [selectedDays, setSelectedDays] = useState(3);
    const [selectedParameter, setSelectedParameter] = useState('temperature');

    useEffect(() => {
        if(currentStation?.status === 'active') {
            onFetchHistoricalData(selectedDays);
        }
    }, [selectedDays, onFetchHistoricalData, currentStation]);

    const parameterOptions = [
        { value: 'temperature', label: 'Temperature (°C)', color: '#ef4444', type: 'line' },
        { value: 'humidity', label: 'Humidity (%)', color: '#3b82f6', type: 'line' },
        { value: 'airPressure', label: 'Air Pressure (hPa)', color: '#8b5cf6', type: 'line' },
        { value: 'WindSpeedAvg', label: 'Avg. Wind Speed (m/s)', color: '#f59e0b', type: 'line' },
        { value: 'rainfall1h', label: 'Rainfall (1h)', color: '#10b981', type: 'bar' },
        { value: 'rainfall24h', label: 'Rainfall (24h)', color: '#06b6d4', type: 'bar' }
    ];

    const selectedParamConfig = parameterOptions.find(p => p.value === selectedParameter);

    const renderChart = () => {
        if (historicalLoading) return <LoadingSpinner message="Loading historical data..." />;

        if (historicalError) {
            return (
                <div className="error-message">
                    <h4>⚠️ Chart Error</h4>
                    <p>{historicalError}</p>
                </div>
            );
        }

        if (!historicalData || historicalData.length === 0) {
            return (
                <div className="no-data-message">
                    <h4>📊 No Data Available</h4>
                    <p>No historical data found for the selected time range.</p>
                </div>
            );
        }

        const ChartComponent = selectedParamConfig.type === 'line' ? LineChart : BarChart;
        const ChartElement = selectedParamConfig.type === 'line' ? Line : Bar;

        return (
            <div className="chart-container">
                <ResponsiveContainer width="100%" height={280}>
                    <ChartComponent data={historicalData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                        <XAxis
                            dataKey="timestamp"
                            fontSize={11}
                            tickFormatter={(ts) => new Date(ts).toLocaleDateString()}
                            stroke="var(--text-secondary)"
                        />
                        <YAxis stroke="var(--text-secondary)" fontSize={11} />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'var(--card-bg)',
                                border: '1px solid var(--border-color)',
                                borderRadius: '8px',
                                color: 'var(--text-primary)',
                                fontSize: '0.8rem'
                            }}
                        />
                        <Legend />
                        <ChartElement
                            dataKey={selectedParameter}
                            fill={selectedParamConfig.color}
                            stroke={selectedParamConfig.color}
                            name={selectedParamConfig.label}
                            strokeWidth={2}
                        />
                    </ChartComponent>
                </ResponsiveContainer>
            </div>
        );
    };

    return (
        <div className="historical-charts">
            <div className="chart-header">
                <h4>📈 Historical Data Analysis</h4>
                <p>Station: {currentStation?.name}</p>
            </div>

            <div className="chart-controls">
                <div className="form-group">
                    <label>📅 Date Range</label>
                    <select
                        value={selectedDays}
                        onChange={(e) => setSelectedDays(Number(e.target.value))}
                    >
                        <option value={1}>Last 24 Hours</option>
                        <option value={3}>Last 3 Days</option>
                        <option value={7}>Last 7 Days</option>
                        <option value={15}>Last 15 Days</option>
                        <option value={30}>Last 30 Days</option>
                    </select>
                </div>

                <div className="form-group">
                    <label>📊 Parameter</label>
                    <select
                        value={selectedParameter}
                        onChange={(e) => setSelectedParameter(e.target.value)}
                    >
                        {parameterOptions.map(option => (
                            <option key={option.value} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {renderChart()}

            {historicalData && historicalData.length > 0 && (
                <div className="chart-stats">
                    <div className="stat-item">
                        <span className="stat-label">Data Points:</span>
                        <span className="stat-value">{historicalData.length}</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">Period:</span>
                        <span className="stat-value">{selectedDays} day{selectedDays > 1 ? 's' : ''}</span>
                    </div>
                </div>
            )}
        </div>
    );
};

// --- COMPACT DATA REQUEST FORM COMPONENT ---
const DataRequestForm = ({ onSubmit, loading, stations, currentStation }) => {
    const activeStations = stations.filter(s => s.status === 'active');
    const [formData, setFormData] = useState({
        email: '',
        organization: '',
        purpose: '',
        start_date: '',
        end_date: '',
        stationId: currentStation?.id || activeStations[0]?.id || '',
        dataFormat: 'csv',
        parameters: []
    });

    const [errors, setErrors] = useState({});

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;

        if (type === 'checkbox') {
            setFormData(prev => ({
                ...prev,
                parameters: checked
                    ? [...prev.parameters, value]
                    : prev.parameters.filter(p => p !== value)
            }));
        } else {
            setFormData(prev => ({ ...prev, [name]: value }));
        }

        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const validateForm = () => {
        const newErrors = {};

        if (!formData.email) newErrors.email = 'Email is required';
        if (!formData.start_date) newErrors.start_date = 'Start date is required';
        if (!formData.end_date) newErrors.end_date = 'End date is required';
        if (!formData.purpose) newErrors.purpose = 'Purpose is required';

        if (formData.start_date && formData.end_date) {
            if (new Date(formData.start_date) > new Date(formData.end_date)) {
                newErrors.end_date = 'End date must be after start date';
            }
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = () => {
        if (validateForm()) {
            onSubmit(formData);
        }
    };

    const parameterOptions = [
        { label: 'Temperature', value: 'temperature' },
        { label: 'Humidity', value: 'humidity' },
        { label: 'Air Pressure', value: 'airPressure' },
        { label: 'Wind Speed (Avg)', value: 'WindSpeedAvg' },
        { label: 'Wind Speed (Max)', value: 'windSpeedMax' },
        { label: 'Wind Direction', value: 'windDirection' },
        { label: 'Rainfall (1h)', value: 'rainfall1h' },
        { label: 'Rainfall (24h)', value: 'rainfall24h' },
    ];


    return (
        <div className="data-request-form">
            <div className="form-header">
                <h4>📋 Data Access Request</h4>
                <p>Request historical weather data for research or analysis</p>
            </div>

            <div className="form-group">
                <label>🏢 Weather Station *</label>
                <select
                    name="stationId"
                    value={formData.stationId}
                    onChange={handleChange}
                    className={errors.stationId ? 'error' : ''}
                >
                    {activeStations.map(station => (
                        <option key={station.id} value={station.id}>
                            {station.name} - {station.location}
                        </option>
                    ))}
                </select>
                {errors.stationId && <span className="error-text">{errors.stationId}</span>}
            </div>

            <div className="form-group">
                <label>📧 Your Email Address *</label>
                <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="your.email@domain.com"
                    className={errors.email ? 'error' : ''}
                />
                {errors.email && <span className="error-text">{errors.email}</span>}
            </div>

            <div className="form-group">
                <label>🏛️ Organization (Optional)</label>
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
                    <label>📅 Start Date *</label>
                    <input
                        type="date"
                        name="start_date"
                        value={formData.start_date}
                        onChange={handleChange}
                        className={errors.start_date ? 'error' : ''}
                    />
                    {errors.start_date && <span className="error-text">{errors.start_date}</span>}
                </div>

                <div className="form-group">
                    <label>📅 End Date *</label>
                    <input
                        type="date"
                        name="end_date"
                        value={formData.end_date}
                        onChange={handleChange}
                        className={errors.end_date ? 'error' : ''}
                    />
                    {errors.end_date && <span className="error-text">{errors.end_date}</span>}
                </div>
            </div>

            <div className="form-group">
                <label>📄 Data Format</label>
                <select name="dataFormat" value={formData.dataFormat} onChange={handleChange}>
                    <option value="csv">CSV</option>

                    <option value="xlsx">Excel Spreadsheet</option>
                </select>
            </div>

            <div className="form-group">
                <label>📊 Parameters (Optional - Leave blank for all data)</label>
                <div className="checkbox-grid">
                    {parameterOptions.map(param => (
                        <label key={param.value} className="checkbox-label">
                            <input
                                type="checkbox"
                                value={param.value}
                                checked={formData.parameters.includes(param.value)}
                                onChange={handleChange}
                            />
                            <span>{param.label}</span>
                        </label>
                    ))}
                </div>
            </div>

            <div className="form-group">
                <label>📝 Purpose of Request *</label>
                <textarea
                    name="purpose"
                    rows="3"
                    value={formData.purpose}
                    onChange={handleChange}
                    placeholder="Please describe how you plan to use this data (research, analysis, etc.)"
                    className={errors.purpose ? 'error' : ''}
                />
                {errors.purpose && <span className="error-text">{errors.purpose}</span>}
            </div>

            <button
                type="button"
                className="submit-btn"
                disabled={loading}
                onClick={handleSubmit}
                aria-label="Submit data request"
            >
                {loading ? (
                    <>
                        <span className="spinner-sm"></span>
                        Submitting...
                    </>
                ) : (
                    'Submit for Approval'
                )}
            </button>

            <div className="process-info">
                <strong>📋 Review Process:</strong>
                <ol>
                    <li>Submit your request with required details</li>
                    <li>Our team reviews and validates the request (1-2 business days)</li>
                    <li>Upon approval, you'll receive the data via email</li>
                    <li>Data is provided in your requested format with metadata</li>
                </ol>
                <p className="note">
                    <strong>Note:</strong> Requests for commercial use may require additional approval.
                </p>
            </div>
        </div>
    );
};

// --- COMPACT SIDEBAR COMPONENT ---
const Sidebar = ({ isOpen, onClose, activeTab, setActiveTab, currentStation, ...props }) => {
    const getTabTitle = () => {
        switch(activeTab) {
            case 'live': return '🌡️ Live Weather Data';
            case 'historical': return '📈 Historical Analytics';
            case 'request': return '📋 Data Access Request';
            default: return '📊 Data Panel';
        }
    };

    const getTabIcon = (tab) => {
        switch(tab) {
            case 'live': return '🌡️';
            case 'historical': return '📈';
            case 'request': return '📋';
            default: return '📊';
        }
    };

    return (
        <div className={`sidebar ${isOpen ? 'open' : ''}`}>
            <div className="sidebar-header">
                <div className="sidebar-title">
                    <h3>{getTabTitle()}</h3>
                    {currentStation && (
                        <span className="current-station">{currentStation.name}</span>
                    )}
                </div>
                <button
                    onClick={onClose}
                    className="close-btn"
                    aria-label="Close sidebar"
                >
                    ×
                </button>
            </div>

            <div className="sidebar-tabs">
                {[
                    { id: 'live', label: 'Live Data' },
                    { id: 'historical', label: 'Historical' },
                    { id: 'request', label: 'Request Data' }
                ].map(tab => (
                    <button
                        key={tab.id}
                        className={activeTab === tab.id ? 'active' : ''}
                        onClick={() => setActiveTab(tab.id)}
                        aria-label={`Switch to ${tab.label} tab`}
                    >
                        {getTabIcon(tab.id)} {tab.label}
                    </button>
                ))}
            </div>

            <div className="sidebar-content">
                {activeTab === 'live' && (
                    <WeatherDisplay
                        data={props.weatherData}
                        loading={props.loading}
                        error={props.error}
                        stationInfo={currentStation}
                    />
                )}
                {activeTab === 'historical' && (
                    <HistoricalCharts
                        onFetchHistoricalData={props.onFetchHistoricalData}
                        historicalData={props.historicalData}
                        historicalLoading={props.historicalLoading}
                        historicalError={props.historicalError}
                        currentStation={currentStation}
                    />
                )}
                {activeTab === 'request' && (
                    <DataRequestForm
                        onSubmit={props.handleDataRequest}
                        loading={props.requestLoading}
                        stations={props.stations}
                        currentStation={currentStation}
                    />
                )}
            </div>
        </div>
    );
};

// --- MAIN APP COMPONENT ---
const MapComponent = () => {
    const [currentStationId, setCurrentStationId] = useState(null);
    const [weatherData, setWeatherData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [activeTab, setActiveTab] = useState('live');
    const [historicalData, setHistoricalData] = useState([]);
    const [historicalLoading, setHistoricalLoading] = useState(false);
    const [historicalError, setHistoricalError] = useState(null);
    const [requestLoading, setRequestLoading] = useState(false);
    const [notification, setNotification] = useState(null);

    const refreshIntervalRef = useRef(null);
    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
    const currentStation = weatherStations.find(s => s.id === currentStationId);

    const location = useLocation();
    const navigate = useNavigate();

    // *** FIX START ***
    // Moved fetchWeatherData before the useEffect that uses it.

    const showNotification = useCallback((message, type = 'info') => {
        setNotification({ message, type });
    }, []);

    const fetchWeatherData = useCallback(async (stationId, showLoader = true) => {
        const station = weatherStations.find(s => s.id === stationId);

        if (station?.status === 'development') {
            setWeatherData(null);
            setError('This station is currently under development and not providing live data.');
            setLoading(false);
            return;
        }

        if (showLoader) setLoading(true);

        try {
            const response = await fetch(`${API_URL}/weather?station_id=${stationId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}: Failed to fetch data`);

            const data = await response.json();
            setWeatherData(data);
            setError(null);

        } catch (err) {
            const errorMessage = err.message.includes('fetch')
                ? 'Unable to connect to weather station. Please check your internet connection.'
                : 'Failed to fetch weather data from the station.';

            setError(errorMessage);
            showNotification(errorMessage, 'error');
        } finally {
            if (showLoader) setLoading(false);
        }
    }, [showNotification]); // Added correct dependency

    // *** FIX END ***

    useEffect(() => {
        if (location.state?.openTab) {
            setActiveTab(location.state.openTab);
            setIsSidebarOpen(true);
        }
    }, [location.state]);

    // Auto-refresh weather data every 30 seconds
    useEffect(() => {
        if (currentStationId && currentStation?.status === 'active') {
            refreshIntervalRef.current = setInterval(() => {
                fetchWeatherData(currentStationId, false); // Silent refresh
            }, 30000);
        }

        return () => {
            if (refreshIntervalRef.current) {
                clearInterval(refreshIntervalRef.current);
            }
        };
    }, [currentStationId, currentStation, fetchWeatherData]); // Added correct dependency


    const fetchHistoricalData = useCallback(async (days) => {
        if (!currentStationId) return;
        const station = weatherStations.find(s => s.id === currentStationId);

        if (station?.status === 'development') {
            setHistoricalData([]);
            setHistoricalError('No historical data available for stations under development.');
            return;
        }

        setHistoricalLoading(true);
        setHistoricalError(null);

        try {
            const response = await fetch(`${API_URL}/historical-data?days=${days}&station_id=${currentStationId}`);
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to fetch historical data');
            }

            setHistoricalData(result.data || []);

            if (result.data && result.data.length > 0) {
                showNotification(`Loaded ${result.data.length} data points`, 'success');
            }
        } catch (err) {
            setHistoricalError(err.message);
            showNotification(err.message, 'error');
        } finally {
            setHistoricalLoading(false);
        }
    }, [currentStationId, showNotification]);

    const handleStationSelect = (stationId) => {
        const station = weatherStations.find(s => s.id === stationId);
        setCurrentStationId(stationId);
        setActiveTab('live');
        setIsSidebarOpen(true);
        showNotification(`Selected ${station.name}`, 'info');
        fetchWeatherData(stationId);
    };

    const handleDataRequest = async (formData) => {
        setRequestLoading(true);

        try {
            const response = await fetch(`${API_URL}/request-data`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to submit request');
            }

            showNotification('Data request submitted successfully! You will receive an email confirmation.', 'success');

        } catch (err) {
            showNotification(err.message || 'Failed to submit data request', 'error');
        } finally {
            setRequestLoading(false);
        }
    };

    const navigateToHome = () => {
        navigate('/');
    };

    return (
        <div className="app-container">
            {notification && (
                <Notification
                    message={notification.message}
                    type={notification.type}
                    onClose={() => setNotification(null)}
                />
            )}

            <Header
                currentStation={currentStation}
                onHomeClick={navigateToHome}
                onSidebarToggle={() => setIsSidebarOpen(!isSidebarOpen)}
                isConnected={!!weatherData && !error && currentStation?.status === 'active'}
                weatherData={weatherData}
                isSidebarOpen={isSidebarOpen}
            />

            <Sidebar
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                currentStation={currentStation}
                weatherData={weatherData}
                loading={loading}
                error={error}
                handleDataRequest={handleDataRequest}
                requestLoading={requestLoading}
                onFetchHistoricalData={fetchHistoricalData}
                historicalData={historicalData}
                historicalLoading={historicalLoading}
                historicalError={historicalError}
                stations={weatherStations}
            />

            <WeatherMap
                stations={weatherStations}
                onStationSelect={handleStationSelect}
                currentStationId={currentStationId}
            />
        </div>
    );
};

export default MapComponent;
