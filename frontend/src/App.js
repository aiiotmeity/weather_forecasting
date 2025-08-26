    import React, { useState, useEffect } from 'react';
    import './App.css';

    function App() {
      // Create a state variable to store the message from the backend
      const [message, setMessage] = useState("Loading...");

      // useEffect runs once after the component mounts
      useEffect(() => {
        // Fetch the data from our Flask API
        fetch('http://127.0.0.1:5000/api/hello')
          .then(response => response.json())
          .then(data => {
            // Update the message state with the data from the API
            setMessage(data.message);
          })
          .catch(error => {
            console.error("There was an error fetching the data!", error);
            setMessage("Error fetching data");
          });
      }, []); // The empty array means this effect runs only once

      return (
        <div className="App">
          <header className="App-header">
            <h1>
              {/* Display the message from the backend */}
              {message}
            </h1>
          </header>
        </div>
      );
    }

    export default App;
    