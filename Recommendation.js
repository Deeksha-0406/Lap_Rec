// src/components/Recommendation.js
import React, { useState } from 'react';
import { recommendLaptop } from '../apiService';

const Recommendation = () => {
    const [role, setRole] = useState('');
    const [requireGpu, setRequireGpu] = useState(null);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleRecommend = async () => {
        try {
            const response = await recommendLaptop(role, requireGpu);
            setResult(response.data.laptop);
            setError(null);
        } catch (err) {
            setError(err.response.data.error);
            setResult(null);
        }
    };

    return (
        <div>
            <h2>Get Laptop Recommendation</h2>
            <input type="text" placeholder="Enter role" value={role} onChange={(e) => setRole(e.target.value)} />
            <select onChange={(e) => setRequireGpu(e.target.value === 'yes' ? true : e.target.value === 'no' ? false : null)}>
                <option value="">Require GPU?</option>
                <option value="yes">Yes</option>
                <option value="no">No</option>
            </select>
            <button onClick={handleRecommend}>Get Recommendation</button>
            {result && <p>Recommended Laptop: {result}</p>}
            {error && <p>Error: {error}</p>}
        </div>
    );
};

export default Recommendation;
