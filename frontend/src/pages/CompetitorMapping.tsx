import React, { useState } from 'react';
import { productsApi } from '../services/api';
import { Upload, CheckCircle, AlertTriangle, FileText } from 'lucide-react';

export const CompetitorMapping = () => {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setMessage(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        try {
            setUploading(true);
            setMessage(null);
            const res = await productsApi.uploadCompetitorMap(file);
            setMessage({ type: 'success', text: res.data.message });
            setFile(null);
        } catch (error: any) {
            console.error('Upload failed:', error);
            setMessage({
                type: 'error',
                text: error.response?.data?.detail || 'Failed to upload mappings.'
            });
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="space-y-6 animate-fade-in">
            <h1 className="text-2xl font-bold text-gray-900">Competitor Mapping</h1>

            {/* Import Section */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Upload size={20} className="text-orange-500" /> Import Cross-Reference Data
                </h2>
                <div className="flex flex-col sm:flex-row items-center gap-4">
                    <div className="relative flex-1 w-full">
                        <input
                            type="file"
                            id="mapping-upload"
                            accept=".csv,.xlsx,.xls"
                            onChange={handleFileChange}
                            className="SR-only hidden"
                        />
                        <label
                            htmlFor="mapping-upload"
                            className="flex items-center justify-between w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
                        >
                            <span className="text-sm text-gray-600 truncate">
                                {file ? file.name : "Choose cross-reference file..."}
                            </span>
                            <span className="text-xs font-semibold text-orange-600 px-2 py-1 bg-orange-50 rounded">
                                Browse
                            </span>
                        </label>
                    </div>
                    <button
                        onClick={handleUpload}
                        disabled={!file || uploading}
                        className="w-full sm:w-auto bg-orange-600 hover:bg-orange-700 disabled:bg-gray-300 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                    >
                        {uploading ? 'Uploading...' : 'Upload File'}
                    </button>
                </div>
                {message && (
                    <div className={`mt-4 p-3 rounded-lg flex items-center gap-2 text-sm ${message.type === 'success' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                        }`}>
                        {message.type === 'success' ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
                        {message.text}
                    </div>
                )}

                <div className="mt-6 p-4 rounded-xl bg-orange-50 border border-orange-100">
                    <h3 className="text-sm font-semibold text-orange-900 mb-2 flex items-center gap-2">
                        <FileText size={16} className="text-orange-600" /> Expected File Format
                    </h3>
                    <p className="text-xs text-orange-800 mb-2 opacity-80">
                        Upload a CSV or Excel file with the following columns:
                    </p>
                    <ul className="list-disc list-inside text-xs text-orange-800 space-y-1 ml-2 opacity-80">
                        <li><span className="font-semibold">Competitor SKU</span> (Required): The part number used by the competitor/customer.</li>
                        <li><span className="font-semibold">Our SKU</span> (Required): Your matching internal SKU.</li>
                        <li><span className="font-semibold">Competitor Name</span> (Optional): Name of the competitor or customer.</li>
                    </ul>
                </div>
            </div>

            {/* Instructions */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">How it works</h2>
                <p className="text-gray-600 text-sm leading-relaxed">
                    When you upload competitor mappings, the system will prioritize these exact matches when analyzing new quotes.
                    If a customer sends a request with their SKU "COMP-123", and you have mapped it to your SKU "OUR-456",
                    Mercura will automatically select "OUR-456" with 95% confidence.
                </p>
            </div>
        </div>
    );
};
