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

// --- DATA SOURCE FOR STATIONS ---
const weatherStations = [
    {
        id: 'weather-v2',
        name: 'Adishankara Weather Station',
        location: 'Kalady, Kerala',
        coordinates: [10.1699, 76.4312],
        status: 'active'
    },
    {
        id: 'station-Airport Road',
        name: 'kochi Airport Road Station',
        location: 'Ernakulam, Kerala',
        coordinates: [10.15559139488071, 76.39268169730792],
        status: 'development'
    },
];

// --- HEADER COMPONENT ---
const Header = ({ currentStation, onHomeClick, onSidebarToggle, isConnected, weatherData }) => (
    <header className="app-header">
        <div className="header-left">
            <button onClick={onHomeClick} className="header-home-btn">🏠 Home</button>
            <div className="header-station-info">
                <span className="station-name">{currentStation.name}</span>
                <span className="station-location">{currentStation.location}</span>
            </div>
        </div>
        <div className="header-right">
            <div className={`header-status ${isConnected ? 'connected' : 'disconnected'}`}>
                <span className="status-dot"></span>
                {isConnected ? 'Live' : 'Offline'}
                {weatherData && isConnected && <span className="live-temp">{weatherData.temperature}°C</span>}
            </div>
            <button onClick={() => window.location.reload()} className="header-icon-btn" title="Refresh Page">🔄</button>
            <button onClick={onSidebarToggle} className="header-icon-btn" title="Toggle Data Panel">📊</button>
        </div>
    </header>
);

// --- MAP COMPONENT ---
const MapComponent = ({ stations, onStationSelect }) => (
    <div className="map-container">
        <MapContainer center={[10.05, 76.35]} zoom={11} style={{ height: '100%', width: '100%' }}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; OpenStreetMap' />
            {stations.map(station => (
                <Marker key={station.id} position={station.coordinates} eventHandlers={{ click: () => onStationSelect(station.id) }} className={station.status === 'development' ? 'inactive-marker' : ''}>
                    <Popup><b>{station.name}</b><br />{station.status === 'development' ? 'Under Development' : 'Click to view data'}</Popup>
                </Marker>
            ))}
        </MapContainer>
    </div>
);

// --- WEATHER DISPLAY COMPONENT ---
const WeatherDisplay = ({ data, loading, error }) => {
    if (loading) return <div>Loading...</div>;
    if (error || !data) return <div>Error: {error || 'No data available'}.</div>;
    const weatherItems = [
        { icon: '🌡️', label: 'Temperature', value: `${data.temperature}°C`}, { icon: '💧', label: 'Humidity', value: `${data.humidity}%`}, { icon: '📊', label: 'Air Pressure', value: `${data.airPressure} hPa`}, { icon: '💨', label: 'Wind Speed', value: `${data.WindSpeedAvg} m/s`}, { icon: '🧭', label: 'Wind Direction', value: `${data.windDirection}°`}, { icon: '🌧️', label: 'Rainfall (1h)', value: `${data.rainfall1h || 0} mm`},
    ];
    return (
        <div>
            {weatherItems.map((item, index) => (
                <div key={index} className="weather-item">
                    <span className="label"><span className="icon">{item.icon}</span>{item.label}</span>
                    <span className="value">{item.value}</span>
                </div>
            ))}
            <div className="timestamp">Last updated: {new Date(`${data.date} ${data.time}`).toLocaleString()}</div>
        </div>
    );
};

// --- HISTORICAL CHARTS COMPONENT ---
const HistoricalCharts = ({ historicalData, historicalLoading, historicalError, onFetchHistoricalData }) => {
    const [selectedDays, setSelectedDays] = useState(3);
    const [selectedParameter, setSelectedParameter] = useState('temperature');

    useEffect(() => { onFetchHistoricalData(selectedDays); }, [selectedDays, onFetchHistoricalData]);

    const parameterOptions = [
        { value: 'temperature', label: 'Temperature (°C)', color: '#e74c3c', type: 'line' }, { value: 'humidity', label: 'Humidity (%)', color: '#3498db', type: 'line' }, { value: 'airPressure', label: 'Air Pressure (hPa)', color: '#8e44ad', type: 'line' }, { value: 'WindSpeedAvg', label: 'Avg. Wind Speed (m/s)', color: '#f39c12', type: 'line' }, { value: 'rainfall1h', label: 'Rainfall (1h)', color: '#27ae60', type: 'bar' }, { value: 'rainfall24h', label: 'Rainfall (24h)', color: '#2980b9', type: 'bar' }
    ];
    const selectedParamConfig = parameterOptions.find(p => p.value === selectedParameter);

    const renderChart = () => {
        if (historicalLoading) return <p>Loading chart data...</p>;
        if (historicalError) return <p style={{color: 'red'}}>Error: {historicalError}</p>;
        if (!historicalData || historicalData.length === 0) return <p>No data available for this range.</p>;
        const ChartComponent = selectedParamConfig.type === 'line' ? LineChart : BarChart;
        const ChartElement = selectedParamConfig.type === 'line' ? Line : Bar;
        return (
            <ResponsiveContainer width="100%" height={300}>
                <ChartComponent data={historicalData}>
                    <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="timestamp" fontSize={10} tickFormatter={(ts) => new Date(ts).toLocaleDateString()} /><YAxis /><Tooltip /><Legend /><ChartElement dataKey={selectedParameter} fill={selectedParamConfig.color} stroke={selectedParamConfig.color} name={selectedParamConfig.label} />
                </ChartComponent>
            </ResponsiveContainer>
        );
    };

    return (
        <div>
            <div className="chart-controls">
                <div className="form-group"><label>Date Range</label><select value={selectedDays} onChange={(e) => setSelectedDays(Number(e.target.value))}><option value={3}>Last 3 Days</option><option value={7}>Last 7 Days</option><option value={15}>Last 15 Days</option><option value={30}>Last 30 Days</option></select></div>
                <div className="form-group"><label>Parameter</label><select value={selectedParameter} onChange={(e) => setSelectedParameter(e.target.value)}>{parameterOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}</select></div>
            </div>
            {renderChart()}
        </div>
    );
};

// --- DATA REQUEST FORM COMPONENT ---
const DataRequestForm = ({ onSubmit, loading, stations }) => {
    const activeStations = stations.filter(s => s.status === 'active');
    const [formData, setFormData] = useState({
        email: '', organization: '', purpose: '', start_date: '', end_date: '', stationId: activeStations[0]?.id || ''
    });

    const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

    return (
        <div className="data-request-form">
            <div className="form-group"><label>Weather Station *</label><select name="stationId" value={formData.stationId} onChange={handleChange}>{activeStations.map(station => (<option key={station.id} value={station.id}>{station.name}</option>))}</select></div>
            <div className="form-group"><label>Your Email Address *</label><input type="email" name="email" value={formData.email} onChange={handleChange} placeholder="your.email@domain.com" /></div>
            <div className="form-group"><label>Organization (Optional)</label><input type="text" name="organization" value={formData.organization} onChange={handleChange} placeholder="Your institution or company" /></div>
            <div className="form-grid">
                <div className="form-group"><label>Start Date *</label><input type="date" name="start_date" value={formData.start_date} onChange={handleChange} /></div>
                <div className="form-group"><label>End Date *</label><input type="date" name="end_date" value={formData.end_date} onChange={handleChange} /></div>
            </div>
            <div className="form-group"><label>Purpose of Request</label><textarea name="purpose" rows="3" value={formData.purpose} onChange={handleChange} placeholder="How you plan to use this data"></textarea></div>
            <button type="button" className="submit-btn" disabled={loading} onClick={() => onSubmit(formData)}>{loading ? 'Submitting...' : 'Submit for Approval'}</button>
            <div className="process-info"><strong>📋 Process:</strong><ol><li>Submit your request.</li><li>An admin reviews and approves it.</li><li>You’ll receive the data via email as a CSV file.</li></ol></div>
        </div>
    );
};

// --- SIDEBAR COMPONENT ---
const Sidebar = ({ isOpen, onClose, activeTab, setActiveTab, ...props }) => {
    const getTabTitle = () => {
        if (activeTab === 'live') return 'Live Data';
        if (activeTab === 'historical') return 'Historical Charts';
        if (activeTab === 'request') return 'Request Data';
        return 'Data Panel';
    };
    return (
        <div className={`sidebar ${isOpen ? 'open' : ''}`}>
            <div className="sidebar-header"><h3>{getTabTitle()}</h3><button onClick={onClose} className="close-btn">×</button></div>
            <div className="sidebar-tabs">
                <button className={activeTab === 'live' ? 'active' : ''} onClick={() => setActiveTab('live')}>Live Data</button>
                <button className={activeTab === 'historical' ? 'active' : ''} onClick={() => setActiveTab('historical')}>Historical Data</button>
                <button className={activeTab === 'request' ? 'active' : ''} onClick={() => setActiveTab('request')}>Request Data</button>
            </div>
            <div className="sidebar-content">
                {activeTab === 'live' && <WeatherDisplay data={props.weatherData} loading={props.loading} error={props.error} />}
                {activeTab === 'historical' && <HistoricalCharts onFetchHistoricalData={props.onFetchHistoricalData} historicalData={props.historicalData} historicalLoading={props.historicalLoading} historicalError={props.historicalError} />}
                {activeTab === 'request' && <DataRequestForm onSubmit={props.handleDataRequest} loading={props.requestLoading} stations={props.stations} />}
            </div>
        </div>
    );
};

// --- MAIN APP COMPONENT ---
const App = () => {
    const [currentView, setCurrentView] = useState('homepage');
    const [currentStationId, setCurrentStationId] = useState(weatherStations[0].id);
    const [weatherData, setWeatherData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [activeTab, setActiveTab] = useState('live');
    const [historicalData, setHistoricalData] = useState([]);
    const [historicalLoading, setHistoricalLoading] = useState(false);
    const [historicalError, setHistoricalError] = useState(null);
    const [requestLoading, setRequestLoading] = useState(false);

    const API_URL = 'http://localhost:5000/api';
    const currentStation = weatherStations.find(s => s.id === currentStationId);

    const fetchWeatherData = useCallback(async (stationId) => {
        const station = weatherStations.find(s => s.id === stationId);
        if (station?.status === 'development') {
            setWeatherData(null);
            setError('This station is under development.');
            setLoading(false);
            return;
        }
        setLoading(true);
        try {
            const response = await fetch(`${API_URL}/weather?station_id=${stationId}`);
            if (!response.ok) throw new Error('Network error');
            const data = await response.json();
            setWeatherData(data);
            setError(null);
        } catch (err) {
            setError('Failed to fetch weather data.');
        } finally {
            setLoading(false);
        }
    }, [API_URL]);

    const fetchHistoricalData = useCallback(async (days) => {
        const station = weatherStations.find(s => s.id === currentStationId);
        if (station?.status === 'development') {
            setHistoricalData([]);
            setHistoricalError('No historical data for development stations.');
            return;
        }
        setHistoricalLoading(true);
        setHistoricalError(null);
        try {
            const response = await fetch(`${API_URL}/historical-data?days=${days}&station_id=${currentStationId}`);
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Failed to fetch historical data');
            setHistoricalData(result.data || []);
        } catch (err) {
            setHistoricalError(err.message);
        } finally {
            setHistoricalLoading(false);
        }
    }, [API_URL, currentStationId]);
    
    useEffect(() => {
        fetchWeatherData(currentStationId);
    }, [currentStationId, fetchWeatherData]);

    const handleStationSelect = (stationId) => {
        setCurrentStationId(stationId);
        setActiveTab('live');
        setIsSidebarOpen(true);
    };

    const handleDataRequest = async (formData) => {
        setRequestLoading(true);
        try {
            const response = await fetch(`${API_URL}/request-data`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });
            if (!response.ok) throw new Error('Submission failed');
            // Handle success (e.g., show notification)
        } catch (err) {
            // Handle error
        } finally {
            setRequestLoading(false);
        }
    };
    
    const navigateToHome = () => setCurrentView('homepage');
    const navigateToWeather = () => setCurrentView('weather');

    if (currentView === 'homepage') return <Homepage onNavigateToWeather={navigateToWeather} />;

    return (
        <div className="app-container">
            <Header currentStation={currentStation} onHomeClick={navigateToHome} onSidebarToggle={() => setIsSidebarOpen(!isSidebarOpen)} isConnected={!!weatherData && !error} weatherData={weatherData} />
            <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} activeTab={activeTab} setActiveTab={setActiveTab} weatherData={weatherData} loading={loading} error={error} handleDataRequest={handleDataRequest} requestLoading={requestLoading} onFetchHistoricalData={fetchHistoricalData} historicalData={historicalData} historicalLoading={historicalLoading} historicalError={historicalError} stations={weatherStations} />
            <MapComponent stations={weatherStations} onStationSelect={handleStationSelect} />
        </div>
    );
};

export default App;