import React, { useEffect, useState } from 'react';
import { customersApi } from '../services/api';

export const Customers = () => {
    const [customers, setCustomers] = useState<any[]>([]);

    useEffect(() => {
        customersApi.list().then(res => setCustomers(res.data)).catch(console.error);
    }, []);

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-white">Customers</h1>
            <div className="glass-panel rounded-2xl p-6">
                <pre className="text-slate-400 text-sm overflow-auto">
                    {JSON.stringify(customers, null, 2)}
                </pre>
            </div>
        </div>
    );
};
