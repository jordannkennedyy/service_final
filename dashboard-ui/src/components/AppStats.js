import React, { useEffect, useState, useCallback } from 'react'
import '../App.css';

export default function AppStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [anomaly_data_torque, setTorqueAnomaly] = useState([]);
    const [anomaly_data_fuel, setFuelAnomaly] = useState([]);
    const [error, setError] = useState(null);

    const getStats = useCallback(() => {
        fetch(`http://acit3855-lab06.eastus2.cloudapp.azure.com:8100/stats`)
            .then(res => res.json())
            .then((result) => {
                console.log("Received Stats");
                setStats(result);
                setIsLoaded(true);
            }, (error) => {
                setError(error);
                setIsLoaded(true);
            });
    

        fetch('http://acit3855-lab06.eastus2.cloudapp.azure.com:8120/anomalies?anomaly_type=TooHigh')
            .then(res => res.json())
            .then((torque) => {
                console.log("Received Torque Anomaly");
                setTorqueAnomaly(torque);
                setIsLoaded(true);
            }, (error) => {
                setError(error);
                setIsLoaded(true);
            });

        fetch('http://acit3855-lab06.eastus2.cloudapp.azure.com:8120/anomalies?anomaly_type=TooLow')
            .then(res => res.json())
            .then((fuel) => {
                console.log("Received Fuel Anomaly");
                setFuelAnomaly(fuel);
                setIsLoaded(true);
            }, (error) => {
                setError(error);
                setIsLoaded(true);
            })
}, []); // Empty dependency array ensures getStats is stable and won't be recreated

    useEffect(() => {
        const interval = setInterval(() => getStats(), 2000); // Update every 2 seconds
        return () => clearInterval(interval);
    }, [getStats]); // Now depends on the memoized getStats

    if (error) {
        return (<div className={"error"}>Error found when fetching from API</div>);
    } else if (isLoaded === false) {
        return (<div>Loading...</div>);
    } else {
        return (
            <div>
                <h1>Latest Stats</h1>
                <table className={"StatsTable"}>
                    <tbody>
                        <tr>
                            <th>Fuel Readings</th>
                            <th>Torque Readings</th>
                        </tr>
                        <tr>
                            <td># Fuel: {stats['num_fuel_readings']}</td>
                            <td># Torque: {stats['num_torque_readings']}</td>
                        </tr>
                        <tr>
                            <td colSpan="3">Average Fuel Reading: {stats['avg_fuel_reading']}</td>
                        </tr>
                        <tr>
                            <td colSpan="3">Average Torque Reading: {stats['avg_torque_reading']}</td>
                        </tr>
                        <tr>
                            <td>Torque Reading Latest Anomaly UUID: {anomaly_data_torque?.[0]?.event_id}</td>
                            <td>Description: {anomaly_data_torque?.[0]?.description}</td>
                            <td>Detected on: {anomaly_data_torque?.[0]?.timestamp}</td>
                        </tr>
                        <tr>
                            <td>Fuel Reading Latest Anomaly UUID: {anomaly_data_fuel?.[0]?.event_id}</td>
                            <td>Description: {anomaly_data_fuel?.[0]?.description}</td>
                            <td>Detected on: {anomaly_data_fuel?.[0]?.timestamp}</td>
                        </tr>
                    </tbody>
                </table>
                <h3>Last Updated: {stats['last_updated']}</h3>
            </div>
        );
    }
}
