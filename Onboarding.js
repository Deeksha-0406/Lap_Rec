// src/components/Onboarding.js
import React, { useState } from 'react';
import { onboardEmployee } from '../apiService';

const Onboarding = () => {
    const [employeeId, setEmployeeId] = useState('');
    const [name, setName] = useState('');
    const [role, setRole] = useState('');
    const [requireGpu, setRequireGpu] = useState(null);
    const [message, setMessage] = useState(null);

    const handleOnboard = async () => {
        try {
            const response = await onboardEmployee(employeeId, name, role, requireGpu);
            setMessage(response.data.message);
        } catch (err) {
            setMessage(err.response.data.message);
        }
    };

    return (
        <div>
            <h2>Onboard Employee</h2>
            <input type="text" placeholder="Employee ID" value={employeeId} onChange={(e) => setEmployeeId(e.target.value)} />
            <input type="text" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
            <input type="text" placeholder="Role" value={role} onChange={(e) => setRole(e.target.value)} />
            <select onChange={(e) => setRequireGpu(e.target.value === 'yes' ? true : e.target.value === 'no' ? false : null)}>
                <option value="">Require GPU?</option>
                <option value="yes">Yes</option>
                <option value="no">No</option>
            </select>
            <button onClick={handleOnboard}>Onboard Employee</button>
            {message && <p>{message}</p>}
        </div>
    );
};

export default Onboarding;
