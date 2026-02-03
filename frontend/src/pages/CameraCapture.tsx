import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Camera, Upload, X, Check, Loader2, Image as ImageIcon,
  AlertCircle, FileText, Plus, ArrowRight, RotateCcw
} from 'lucide-react';
import { api } from '../services/api';

interface ExtractedItem {
  item_name: string;
  quantity: number;
  sku?: string;
  notes?: string;
}

interface ExtractionResult {
  success: boolean;
  extracted_text: string;
  structured_data: {
    customer_name?: string;
    contact_email?: string;
    contact_phone?: string;
    line_items: ExtractedItem[];
    delivery_date?: string;
    delivery_location?: string;
    special_instructions?: string;
    confidence: number;
  };
  confidence: number;
  error?: string;
}

export const CameraCapture = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  
  const [step, setStep] = useState<'capture' | 'processing' | 'review' | 'creating'>('capture');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [createdQuoteId, setCreatedQuoteId] = useState<string | null>(null);

  // Handle file selection (from gallery or camera)
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>, source: 'camera' | 'gallery') => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setError('Please select a valid image (JPG, PNG)');
      return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setError('Image too large (max 10MB)');
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setError(null);
  }, []);

  // Process the image
  const processImage = async () => {
    if (!selectedFile) return;

    setStep('processing');
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('source', previewUrl?.includes('camera') ? 'camera' : 'gallery');

      const res = await api.post('/image-extract/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setResult(res.data);
      setStep('review');
    } catch (err: any) {
      console.error('Extraction failed:', err);
      setError(err.response?.data?.detail || 'Failed to process image. Try a clearer photo.');
      setStep('capture');
    }
  };

  // Create quote from extraction
  const createQuote = async () => {
    if (!selectedFile || !result) return;

    setStep('creating');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('notes', 'Created from camera capture');

      const res = await api.post('/image-extract/create-quote', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setCreatedQuoteId(res.data.quote_id);
      
      // Navigate to quote after short delay
      setTimeout(() => {
        navigate(`/quotes/${res.data.quote_id}`);
      }, 1500);
    } catch (err: any) {
      console.error('Quote creation failed:', err);
      setError(err.response?.data?.detail || 'Failed to create quote');
      setStep('review');
    }
  };

  // Reset for another capture
  const reset = () => {
    setStep('capture');
    setPreviewUrl(null);
    setSelectedFile(null);
    setResult(null);
    setError(null);
    setCreatedQuoteId(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  // STEP 1: CAPTURE
  if (step === 'capture') {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-2xl mx-auto px-6 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-semibold text-gray-900">Camera Capture</h1>
                <p className="text-gray-600 mt-1">Take a photo of an RFQ email or document</p>
              </div>
              <button onClick={() => navigate('/')} className="text-gray-500 hover:text-gray-700">
                <X size={24} />
              </button>
            </div>
          </div>
        </div>

        <div className="max-w-2xl mx-auto px-6 py-8">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-700">
              <AlertCircle size={20} />
              {error}
            </div>
          )}

          {/* Capture Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Camera Option */}
            <button
              onClick={() => cameraInputRef.current?.click()}
              className="flex flex-col items-center gap-4 p-8 bg-white border-2 border-dashed border-gray-300 rounded-xl hover:border-orange-500 hover:bg-orange-50 transition-colors"
            >
              <div className="p-4 bg-orange-100 rounded-full">
                <Camera className="text-orange-600" size={32} />
              </div>
              <div className="text-center">
                <h3 className="font-semibold text-gray-900">Take Photo</h3>
                <p className="text-sm text-gray-500 mt-1">Use your camera to capture an RFQ</p>
              </div>
              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={(e) => handleFileSelect(e, 'camera')}
                className="hidden"
              />
            </button>

            {/* Gallery Option */}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex flex-col items-center gap-4 p-8 bg-white border-2 border-dashed border-gray-300 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-colors"
            >
              <div className="p-4 bg-blue-100 rounded-full">
                <ImageIcon className="text-blue-600" size={32} />
              </div>
              <div className="text-center">
                <h3 className="font-semibold text-gray-900">Choose from Gallery</h3>
                <p className="text-sm text-gray-500 mt-1">Select an existing photo</p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/jpg,image/png,image/webp"
                onChange={(e) => handleFileSelect(e, 'gallery')}
                className="hidden"
              />
            </button>
          </div>

          {/* Tips */}
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-6">
            <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
              <Check size={18} />
              Tips for Best Results
            </h3>
            <ul className="space-y-2 text-sm text-blue-800">
              <li>• Make sure text is clearly visible and in focus</li>
              <li>• Good lighting helps accuracy</li>
              <li>• Capture the full document if possible</li>
              <li>• Avoid shadows and glare</li>
            </ul>
          </div>

          {/* Selected Preview */}
          {previewUrl && (
            <div className="mt-6">
              <h3 className="font-medium text-gray-700 mb-3">Preview:</h3>
              <div className="relative rounded-xl overflow-hidden border border-gray-200">
                <img 
                  src={previewUrl} 
                  alt="Preview" 
                  className="w-full max-h-96 object-contain bg-gray-100"
                />
                <button
                  onClick={reset}
                  className="absolute top-2 right-2 p-2 bg-white/90 rounded-lg shadow-sm hover:bg-white"
                >
                  <X size={18} />
                </button>
              </div>
              
              <button
                onClick={processImage}
                className="w-full mt-4 flex items-center justify-center gap-2 px-6 py-3 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 transition-colors"
              >
                <FileText size={18} />
                Extract Text & Create Quote
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  // STEP 2: PROCESSING
  if (step === 'processing') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="relative mb-6">
            <Loader2 className="animate-spin mx-auto text-orange-600" size={48} />
            {previewUrl && (
              <img 
                src={previewUrl} 
                alt="Processing" 
                className="absolute inset-0 w-12 h-12 object-cover rounded-lg opacity-50 blur-sm mx-auto"
              />
            )}
          </div>
          <h2 className="text-xl font-semibold text-gray-900">Analyzing Image...</h2>
          <p className="text-gray-600 mt-2">We're extracting text and identifying items</p>
          <p className="text-sm text-gray-500 mt-4">This usually takes 5-10 seconds</p>
        </div>
      </div>
    );
  }

  // STEP 3: REVIEW RESULTS
  if (step === 'review' && result) {
    const data = result.structured_data;
    const hasItems = data.line_items && data.line_items.length > 0;

    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-3xl mx-auto px-6 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-semibold text-gray-900">Review Extraction</h1>
                <p className="text-gray-600 mt-1">
                  Confidence: {Math.round(result.confidence * 100)}%
                </p>
              </div>
              <button onClick={reset} className="p-2 text-gray-500 hover:text-gray-700">
                <RotateCcw size={20} />
              </button>
            </div>
          </div>
        </div>

        <div className="max-w-3xl mx-auto px-6 py-6">
          {/* Confidence Warning */}
          {result.confidence < 0.5 && (
            <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="text-amber-600 flex-shrink-0 mt-0.5" size={20} />
              <div>
                <p className="font-medium text-amber-800">Low Confidence Reading</p>
                <p className="text-sm text-amber-700 mt-1">
                  The image quality made it hard to read. Please review carefully and make corrections.
                </p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Extracted Data */}
            <div className="space-y-6">
              {/* Customer Info */}
              <div className="bg-white border border-gray-200 rounded-xl p-5">
                <h3 className="font-semibold text-gray-900 mb-4">Customer Information</h3>
                <div className="space-y-3">
                  <div>
                    <label className="text-sm text-gray-500">Name</label>
                    <p className="font-medium text-gray-900">{data.customer_name || 'Not detected'}</p>
                  </div>
                  {data.contact_email && (
                    <div>
                      <label className="text-sm text-gray-500">Email</label>
                      <p className="font-medium text-gray-900">{data.contact_email}</p>
                    </div>
                  )}
                  {data.contact_phone && (
                    <div>
                      <label className="text-sm text-gray-500">Phone</label>
                      <p className="font-medium text-gray-900">{data.contact_phone}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Line Items */}
              <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-200 bg-gray-50">
                  <h3 className="font-semibold text-gray-900">
                    Items Found ({data.line_items?.length || 0})
                  </h3>
                </div>
                
                {hasItems ? (
                  <div className="divide-y divide-gray-100">
                    {data.line_items.map((item, index) => (
                      <div key={index} className="p-4">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium text-gray-900">{item.item_name}</p>
                            {item.sku && (
                              <p className="text-sm text-gray-500">SKU: {item.sku}</p>
                            )}
                            {item.notes && (
                              <p className="text-sm text-gray-600 mt-1">{item.notes}</p>
                            )}
                          </div>
                          <span className="px-2 py-1 bg-gray-100 rounded text-sm font-medium text-gray-700">
                            Qty: {item.quantity}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center text-gray-500">
                    <p>No items detected in the image.</p>
                    <p className="text-sm mt-1">You can add them manually in the quote.</p>
                  </div>
                )}
              </div>

              {/* Special Instructions */}
              {(data.delivery_date || data.delivery_location || data.special_instructions) && (
                <div className="bg-white border border-gray-200 rounded-xl p-5">
                  <h3 className="font-semibold text-gray-900 mb-4">Additional Details</h3>
                  {data.delivery_date && (
                    <p className="text-sm"><span className="text-gray-500">Delivery:</span> {data.delivery_date}</p>
                  )}
                  {data.delivery_location && (
                    <p className="text-sm mt-2"><span className="text-gray-500">Location:</span> {data.delivery_location}</p>
                  )}
                  {data.special_instructions && (
                    <p className="text-sm mt-2"><span className="text-gray-500">Notes:</span> {data.special_instructions}</p>
                  )}
                </div>
              )}
            </div>

            {/* Right: Original Image & Actions */}
            <div className="space-y-6">
              {previewUrl && (
                <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                  <div className="px-5 py-4 border-b border-gray-200 bg-gray-50">
                    <h3 className="font-semibold text-gray-900">Original Image</h3>
                  </div>
                  <img 
                    src={previewUrl} 
                    alt="Captured" 
                    className="w-full object-contain max-h-96 bg-gray-100"
                  />
                </div>
              )}

              {/* Raw OCR Text (collapsible) */}
              <details className="bg-gray-50 border border-gray-200 rounded-xl">
                <summary className="px-5 py-4 cursor-pointer font-medium text-gray-700">
                  View Extracted Text
                </summary>
                <div className="px-5 py-4 border-t border-gray-200">
                  <pre className="text-sm text-gray-600 whitespace-pre-wrap font-mono">
                    {result.extracted_text || 'No text extracted'}
                  </pre>
                </div>
              </details>

              {/* Actions */}
              <div className="space-y-3">
                <button
                  onClick={createQuote}
                  className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 transition-colors"
                >
                  <Plus size={18} />
                  Create Quote from Extraction
                </button>
                
                <button
                  onClick={() => navigate('/quotes/new')}
                  className="w-full flex items-center justify-center gap-2 px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <ArrowRight size={18} />
                  Create Quote Manually
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // STEP 4: CREATING
  if (step === 'creating') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin mx-auto mb-4 text-orange-600" size={48} />
          <h2 className="text-xl font-semibold text-gray-900">Creating Quote...</h2>
          <p className="text-gray-600 mt-2">Setting up your quote with extracted items</p>
        </div>
      </div>
    );
  }

  return null;
};

export default CameraCapture;
