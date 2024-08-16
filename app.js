// app.js
import React, { useEffect, useState } from 'react';
import { getLaptops } from './api'; // Import the API functions

const App = () => {
  const [laptops, setLaptops] = useState([]);

  useEffect(() => {
    const fetchLaptops = async () => {
      try {
        const data = await getLaptops();
        setLaptops(data);
      } catch (error) {
        console.error('Error fetching laptops:', error);
      }
    };

    fetchLaptops();
  }, []);

  return (
    <div>
      <h1>Laptops</h1>
      <ul>
        {laptops.map(laptop => (
          <li key={laptop.id}>{laptop.name}</li>
        ))}
      </ul>
    </div>
  );
};

export default App;
