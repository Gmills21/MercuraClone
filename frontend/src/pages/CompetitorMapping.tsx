import React, { useState } from 'react';
import { productsApi } from '../services/api';
import { Upload, CheckCircle, AlertTriangle, FileText } from 'lucide-react';

export const CompetitorMapping = () => {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

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
            <h1 className="text-2xl font-bold text-white">Competitor Mapping</h1>
            
            {/* Import Section */}
            <div className="glass-panel rounded-2xl p-6">
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Upload size={20} /> Import Cross-Reference Data
                </h2>
                <div className="flex items-center gap-4">
                    <input 
                        type="file" 
                        accept=".csv,.xlsx,.xls"
                        onChange={handleFileChange}
                        className="block w-full text-sm text-slate-400
                            file:mr-4 file:py-2 file:px-4
                            file:rounded-full file:border-0
                            file:text-sm file:font-semibold
                            file:bg-slate-800 file:text-blue-400
                            hover:file:bg-slate-700
                            cursor-pointer"
                    />
                    <button 
                        onClick={handleUpload}
                        disabled={!file || uploading}
                        className="btn-primary whitespace-nowrap"
                    >
                        {uploading ? 'Uploading...' : 'Upload File'}
                    </button>
                </div>
                {message && (
                    <div className={`mt-4 p-3 rounded-lg flex items-center gap-2 text-sm ${
                        message.type === 'success' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                    }`}>
                        {message.type === 'success' ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
                        {message.text}
                    </div>
                )}
                
                <div className="mt-6 p-4 rounded-xl bg-slate-900/50 border border-slate-800">
                    <h3 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                        <FileText size={16} /> Expected File Format
                    </h3>
                    <p className="text-xs text-slate-400 mb-2">
                        Upload a CSV or Excel file with the following columns:
                    </p>
                    <ul className="list-disc list-inside text-xs text-slate-400 space-y-1 ml-2">
                        <li><span className="text-slate-300">Competitor SKU</span> (Required): The part number used by the competitor/customer.</li>
                        <li><span className="text-slate-300">Our SKU</span> (Required): Your matching internal SKU.</li>
                        <li><span className="text-slate-300">Competitor Name</span> (Optional): Name of the competitor or customer.</li>
                    </ul>
                </div>
            </div>
            
            {/* Instructions */}
            <div className="glass-panel rounded-2xl p-6">
                 <h2 className="text-lg font-semibold text-white mb-4">How it works</h2>
                 <p className="text-slate-400 text-sm leading-relaxed">
                     When you upload competitor mappings, the system will prioritize these exact matches when analyzing new quotes. 
                     If a customer sends a request with their SKU "COMP-123", and you have mapped it to your SKU "OUR-456", 
                     Mercura will automatically select "OUR-456" with 95% confidence.
                 </p>
            </div>
        </div>
    );
};
