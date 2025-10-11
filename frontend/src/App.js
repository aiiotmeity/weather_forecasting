import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Homepage from './Homepage';
import MapComponent from './MapComponent';
import RiverDashboard from './RiverDashboard';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Homepage />} />
      <Route path="/map" element={<MapComponent />} />
      <Route path="/river-forecast" element={<RiverDashboard />} />
      
    </Routes>
  );
}

export default App;