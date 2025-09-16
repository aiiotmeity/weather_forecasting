import React, { useState, useEffect } from 'react';
import './Homepage.css';

const Homepage = ({ onNavigateToWeather }) => {
  const [currentWeather, setCurrentWeather] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch current weather data
  useEffect(() => {
    const fetchWeatherData = async () => {
      try {
        const response = await fetch('/api/weather');
        if (response.ok) {
          const data = await response.json();
          setCurrentWeather(data);
        }
      } catch (error) {
        console.error('Error fetching weather data:', error);
      }
    };

    fetchWeatherData();
    const interval = setInterval(fetchWeatherData, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, []);

  const handleAccessWeatherApp = () => {
    if (onNavigateToWeather) {
      onNavigateToWeather('live');
    } else {
      // Fallback: redirect to weather app
      window.location.href = '#weather';
    }
  };

  const handleDataRequest = () => {
    if (onNavigateToWeather) {
      onNavigateToWeather('request');
    } else {
      window.location.href = '#weather?tab=request';
    }
  };

  return (
    <div className="homepage">
      {/* Government Header */}
      <header className="gov-header">
        <div className="header-top">
          <div className="header-top-content">
            <div className="gov-links">
              <a href="https://www.india.gov.in" target="_blank" rel="noopener noreferrer">
                Govt.of India
              </a>
              <a href="https://moes.gov.in" target="_blank" rel="noopener noreferrer">
                Ministry of Earth Sciences
              </a>
            </div>
            <div className="header-time">
              {currentTime.toLocaleString('en-IN', {
                timeZone: 'Asia/Kolkata',
                dateStyle: 'medium',
                timeStyle: 'short'
              })}
            </div>
          </div>
        </div>

        <div className="header-main">
          <div className="header-container">
            <div className="logo-section">
              <div className="logo">
                <i className="fas fa-cloud-sun"></i>
              </div>
              <div className="title-section">
                <h1>Weather Monitoring System</h1>
                <p>Adishankara Engineering College</p>
                <div className="subtitle">Kalady, Kerala - 683574</div>
              </div>
            </div>

            <div className="header-actions">
              <button 
                className="btn btn-primary"
                onClick={handleAccessWeatherApp}
              >
                <i className="fas fa-tachometer-alt"></i>
                Access Live Data
              </button>
              <button 
                className="btn btn-secondary"
                onClick={handleDataRequest}
              >
                <i className="fas fa-download"></i>
                Request Historical Data
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="nav-bar">
        <div className="nav-container">
          <ul className="nav-menu">
            <li className="nav-item">
              <a href="#home" className="nav-link active">Home</a>
            </li>
            <li className="nav-item">
              <a href="#about" className="nav-link">About</a>
            </li>
            <li className="nav-item">
              <a href="#services" className="nav-link">Services</a>
            </li>
            
            <li className="nav-item">
              <a href="#contact" className="nav-link">Contact</a>
            </li>
          </ul>
        </div>
      </nav>

      {/* Hero Section */}
      <section id="home" className="hero-section">
        <div className="hero-container">
          <div className="hero-content">
            <h2>Meteorological Research and Development Sector for AI-IoT Innovation</h2>
            <p>
             Real-time data from the weather station at Adi Shankara Institute of Engineering and Technology
            </p>


            <div className="hero-stats">
              <div className="stat-card">
                <span className="stat-number">24/7</span>
                <span className="stat-label">Continuous Monitoring</span>
              </div>
              <div className="stat-card">
                <span className="stat-number">
                  {currentWeather ? `${currentWeather.temperature}°C` : '--°C'}
                </span>
                <span className="stat-label">Current Temperature</span>
              </div>
              <div className="stat-card">
                <span className="stat-number">
                  {currentWeather ? `${currentWeather.humidity}%` : '--%'}
                </span>
                <span className="stat-label">Current Humidity</span>
              </div>
              
            </div>

            <div className="hero-actions">
              <button 
                className="btn btn-primary btn-large"
                onClick={handleAccessWeatherApp}
              >
                <i className="fas fa-chart-line"></i>
                View Live Weather Dashboard
              </button>
              <a href="#about" className="btn btn-outline">
                <i className="fas fa-info-circle"></i>
                Learn More
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="about" className="features-section">
        <div className="features-container">
          <div className="section-header">
            <h2>Advanced Meteorological Capabilities</h2>
            <p>
              Our advanced weather monitoring system provides reliable atmospheric insights for innovation, learning, and community benefit
            </p>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <i className="fas fa-thermometer-half"></i>
              </div>
              <h3>Real-time Monitoring</h3>
              <p>
                Continuous monitoring of temperature, humidity, pressure, wind speed, 
                wind direction, and precipitation with high-precision sensors
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <i className="fas fa-database"></i>
              </div>
              <h3>Historical Data Archive</h3>
              <p>
                Comprehensive database of weather patterns and trends spanning multiple years, 
                available for research and analysis purposes
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <i className="fas fa-chart-area"></i>
              </div>
              <h3>Data Analytics</h3>
              <p>
                Advanced data processing and visualization tools for climate research, 
                agricultural planning, and environmental studies
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <i className="fas fa-graduation-cap"></i>
              </div>
              <h3>Educational Resources</h3>
              <p>
                Supporting academic research and education in meteorology, 
                environmental science, and climate studies
              </p>
            </div>

            

            <div className="feature-card">
              <div className="feature-icon">
                <i className="fas fa-shield-alt"></i>
              </div>
              <h3>Data Security</h3>
              <p>
                Secure data transmission and storage with regular backups, 
                ensuring data integrity and availability
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section id="services" className="services-section">
        <div className="services-container">
          <div className="section-header">
            <h2>Our Services</h2>
            <p>Comprehensive weather monitoring and data services for various applications</p>
          </div>

          <div className="services-grid">
            <div className="service-card">
              <h4>
                <i className="fas fa-eye"></i>
                Live Weather Monitoring
              </h4>
              <p>
                Real-time access to current weather conditions with automatic updates 
                every 30 seconds for immediate weather awareness
              </p>
            </div>

            <div className="service-card">
              <h4>
                <i className="fas fa-history"></i>
                Historical Data Access
              </h4>
              <p>
                Request and download historical weather data for research, 
                analysis, and academic projects with admin approval process
              </p>
            </div>

            <div className="service-card">
              <h4>
                <i className="fas fa-chart-line"></i>
                Climate Analysis
              </h4>
              <p>
                Long-term climate pattern analysis and trend identification 
                for environmental and agricultural research applications
              </p>
            </div>

            
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="contact-section">
        <div className="contact-container">
          <div className="section-header">
            <h2>Contact Information</h2>
            <p>Get in touch with our weather monitoring team</p>
          </div>

          <div className="contact-grid">
            <div className="contact-info">
              <h3>Weather Station Contact</h3>
              
              <div className="contact-item">
                <div className="contact-icon">
                  <i className="fas fa-map-marker-alt"></i>
                </div>
                <div className="contact-details">
                  <h4>Address</h4>
                  <p>
                    Adishankara Engineering College<br />
                    Kalady, Ernakulam District<br />
                    Kerala - 683574, India
                  </p>
                </div>
              </div>

              <div className="contact-item">
                <div className="contact-icon">
                  <i className="fas fa-phone"></i>
                </div>
                <div className="contact-details">
                  <h4>Phone</h4>
                  <p>+91 484 246 3030</p>
                </div>
              </div>

              <div className="contact-item">
                <div className="contact-icon">
                  <i className="fas fa-envelope"></i>
                </div>
                <div className="contact-details">
                  <h4>Email</h4>
                  <p>weather@adishankara.ac.in</p>
                </div>
              </div>
            </div>

            <div className="quick-access">
              <h3>Quick Access</h3>
              <div className="quick-links">
                <button 
                  className="quick-link"
                  onClick={handleAccessWeatherApp}
                >
                  <i className="fas fa-tachometer-alt"></i>
                  <span>Live Weather Dashboard</span>
                </button>

                <button 
                  className="quick-link"
                  onClick={handleDataRequest}
                >
                  <i className="fas fa-download"></i>
                  <span>Request Historical Data</span>
                </button>

                
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-container">
          <div className="footer-grid">
            <div className="footer-section">
              <h4>Weather Monitoring System</h4>
              <p>
                Advanced meteorological monitoring facility providing real-time weather data 
                and historical records for research, education, and public service.
              </p>
            </div>

            <div className="footer-section">
              <h4>Quick Links</h4>
              <ul className="footer-links">
                <li><a href="#home">Home</a></li>
                <li><a href="#about">About System</a></li>
                <li><a href="#services">Services</a></li>
                <li><a href="#contact">Contact</a></li>
              </ul>
            </div>

            <div className="footer-section">
              <h4>Institution</h4>
              <ul className="footer-links">
                <li><a href="https://www.adishankara.ac.in" target="_blank" rel="noopener noreferrer">Adishankara Engineering College</a></li>
                <li><a href="https://www.india.gov.in" target="_blank" rel="noopener noreferrer">
                Govt. of India
              </a></li>
              </ul>
            </div>
          </div>

          <div className="footer-bottom">
            <p>
              © {new Date().getFullYear()} Adishankara Engineering College Weather Monitoring System. 
              All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Homepage;