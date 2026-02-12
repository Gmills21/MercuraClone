
import React from 'react';
import { Shield, Lock, Database, Server, Cpu, CheckCircle, XCircle } from 'lucide-react';

export const Security = () => {
    return (
        <div className="max-w-7xl mx-auto px-6 py-8">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-900">Security & Data Privacy</h1>
                <p className="text-gray-600 mt-2">Enterprise-grade protection. Your data stays yours.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                        <Database className="text-green-600" size={24} />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Local SQLite Storage</h3>
                    <p className="text-gray-600 text-sm">
                        All customer data, pricing history, and operational metrics are stored locally in a secure SQLite database.
                        We allow strictly zero cloud retention of your proprietary business records.
                    </p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                        <Cpu className="text-blue-600" size={24} />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Private Vector Search</h3>
                    <p className="text-gray-600 text-sm">
                        Our RAG (Retrieval-Augmented Generation) system uses a local instance of ChromaDB.
                        Your documents are indexed on your hardware, ensuring sensitive RFQs never leave your control.
                    </p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                        <Lock className="text-purple-600" size={24} />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Zero-Training AI</h3>
                    <p className="text-gray-600 text-sm">
                        We explicitly strictly separate customer data.
                        It is <strong>never</strong> used to train external AI models. Your proprietary pricing strategies remain your competitive advantage.
                    </p>
                </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm mb-12">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                    <h3 className="font-semibold text-gray-900">Privacy-First Architecture Comparison</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-gray-50 text-gray-600 font-medium border-b border-gray-100">
                            <tr>
                                <th className="px-6 py-4">Feature</th>
                                <th className="px-6 py-4 text-orange-600 font-semibold">OpenMercura (Local)</th>
                                <th className="px-6 py-4 text-gray-500">Traditional SaaS</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            <tr>
                                <td className="px-6 py-4 font-medium text-gray-900">Data Storage</td>
                                <td className="px-6 py-4 text-gray-700 flex items-center gap-2">
                                    <Server size={16} className="text-green-500" /> On-Premise / Local
                                </td>
                                <td className="px-6 py-4 text-gray-500">Cloud (Often Multi-tenant)</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 font-medium text-gray-900">AI Model Training</td>
                                <td className="px-6 py-4 text-gray-700 flex items-center gap-2">
                                    <CheckCircle size={16} className="text-green-500" /> Zero Training on Data
                                </td>
                                <td className="px-6 py-4 text-gray-500">Aggregated Community Data</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 font-medium text-gray-900">Vector Embeddings</td>
                                <td className="px-6 py-4 text-gray-700 flex items-center gap-2">
                                    <Database size={16} className="text-green-500" /> Local ChromaDB
                                </td>
                                <td className="px-6 py-4 text-gray-500">Shared Cloud Vector Stores</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 font-medium text-gray-900">Access Control</td>
                                <td className="px-6 py-4 text-gray-700 flex items-center gap-2">
                                    <Shield size={16} className="text-green-500" /> Physical Access Only
                                </td>
                                <td className="px-6 py-4 text-gray-500">Credential-based (Hackable)</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="bg-orange-50 border border-orange-100 rounded-xl p-8 text-center">
                <Shield className="mx-auto text-orange-600 mb-4" size={48} />
                <h2 className="text-xl font-bold text-gray-900 mb-2">Our Commitment to You</h2>
                <p className="text-gray-700 max-w-2xl mx-auto">
                    In an era where data is the new oil, we believe your specialized knowledge is your most valuable asset.
                    OpenMercura is built to empower your workflow with AI, without compromising your trade secrets.
                </p>
            </div>
        </div>
    );
};

export default Security;
