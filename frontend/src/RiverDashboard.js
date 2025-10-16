import React, { useState, useEffect } from 'react';
import './RiverDashboard.css';
import { useNavigate } from 'react-router-dom';

const RiverDashboard = () => {
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('/api/river-data');
                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                const jsonData = await response.json();
                setData(jsonData);
                setError(null);
            } catch (error) {
                console.error("Failed to fetch river data:", error);
                setError(error.message);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 30000);

        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="loading-message">
                <div>Loading River Dashboard</div>
                <div style={{ fontSize: '1.1rem', opacity: 0.9, fontWeight: 400 }}>
                    Fetching real-time water level data...
                </div>
            </div>
        );
    }
    
    if (error) {
        return (
            <div className="error-message">
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
                <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '1rem' }}>
                    Connection Error
                </div>
                <div style={{ fontSize: '1.1rem', opacity: 0.9, maxWidth: '500px' }}>
                    Unable to fetch river data. Please ensure the backend server is running and try again.
                </div>
            </div>
        );
    }

    const formatTimestamp = (ts) => new Date(ts).toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour: '2-digit',
        minute: '2-digit',
        day: 'numeric',
        month: 'short',
        year: 'numeric'
    });

    const getStatusEmoji = (alert) => {
        const emojis = {
            normal: '✅',
            watch: '⚠️',
            warning: '🚨',
            critical: '🔴'
        };
        return emojis[alert] || '•';
    };

    return (
        <div className="river-dashboard-body">
            {/* Premium Header */}
            <header className="river-gov-header">
                <div className="river-header-container">
                    <div className="river-logo-section">
                        <div className="river-logo">
                            <i className="fas fa-water" style={{ color: 'white' }}></i>
                        </div>
                        <div className="river-title-section">
                            <h1>Periyar River Monitoring System</h1>
                            <p>Kalady Region - Real-time Water Level Forecast</p>
                        </div>
                    </div>
                    <div className="river-header-badge">
                        <span>Live Monitoring</span>
                    </div>
                    <button
                        className="btn btn-outline"
                        style={{ marginLeft: 'auto', marginRight: '1rem' }}
                        onClick={() => navigate('/')}
                    >
                        <i className="fas fa-home"></i> Home
                    </button>
                </div>
            </header>

            <div className="dashboard-container">
                {/* Enhanced Alert Banner */}
                <div className={`alert-banner ${data.currentAlert}`}>
                    <div>
                        {getStatusEmoji(data.currentAlert)} Water Level: <strong>{data.currentWaterLevel.toFixed(2)}m</strong> - Status: <strong>{data.currentAlert.toUpperCase()}</strong>
                    </div>
                </div>

                {/* Premium Metric Cards */}
                <div className="metrics-grid">
                    <div className="metric-card">
                        <div className="metric-title">
                            <i className="fas fa-tint" style={{ color: '#06b6d4' }}></i>
                            Current Water Level
                        </div>
                        <div className="metric-value">
                            {data.currentWaterLevel.toFixed(2)}
                            <span>mtrs</span>
                        </div>
                        <div className="metric-timestamp">
                            <i className="far fa-clock"></i> {formatTimestamp(data.waterLevelTime)}
                        </div>
                    </div>

                    

                    <div className="metric-card">
                        <div className="metric-title">
                            <i className="fas fa-chart-line" style={{ color: '#06b6d4' }}></i>
                            Next Hour Forecast
                        </div>
                        <div className="metric-value">
                            {data.forecast[0].toFixed(2)}
                            <span>mtrs</span>
                        </div>
                        <div className="metric-timestamp">
                            <i className="fas fa-brain"></i> AI-Powered Prediction
                        </div>
                    </div>
                </div>

                {/* Premium Forecast Section */}
                <div className="forecast-section">
                    <h2>
                        <i className="fas fa-water" style={{ 
                            background: 'linear-gradient(135deg, #0c4a6e, #0284c7)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            marginRight: '0.5rem'
                        }}></i>
                        6-Hour Water Level Forecast
                    </h2>
                    <div className="forecast-grid">
                        {data.forecast.map((value, index) => (
                            <div className="forecast-card" key={index}>
                                <div className="forecast-time">
                                    <i className="far fa-clock"></i> +{index + 1} Hour
                                </div>
                                <div className="forecast-value">{value.toFixed(2)} m</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RiverDashboard;