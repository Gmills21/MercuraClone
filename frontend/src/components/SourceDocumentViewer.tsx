import React, { useState, useEffect, useRef } from 'react';
import { FileText, Mail, Image, ZoomIn, ZoomOut, RotateCcw, ChevronLeft, ChevronRight, Maximize2, X, ExternalLink, MapPin } from 'lucide-react';

interface SourceDocumentViewerProps {
  sourceType: 'pdf' | 'email' | 'image';
  sourceUrl?: string;
  sourceContent?: string;
  sourceMetadata?: any;
  extractedItems?: any[];
  selectedItemIndex?: number | null;
  onItemClick?: (index: number) => void;
  className?: string;
}

interface SourceAnchor {
  itemIndex: number;
  page: number;
  bbox: { x: number; y: number; width: number; height: number };
  text: string;
}

export const SourceDocumentViewer: React.FC<SourceDocumentViewerProps> = ({
  sourceType,
  sourceUrl,
  sourceContent,
  sourceMetadata,
  extractedItems = [],
  selectedItemIndex,
  onItemClick,
  className = ''
}) => {
  const [zoom, setZoom] = useState(100);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [anchors, setAnchors] = useState<SourceAnchor[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  // Generate anchors from extracted items metadata
  useEffect(() => {
    if (extractedItems && sourceMetadata?.extraction_anchors) {
      const newAnchors: SourceAnchor[] = [];
      extractedItems.forEach((item, index) => {
        if (item.metadata?.source_location) {
          newAnchors.push({
            itemIndex: index,
            page: item.metadata.source_location.page || 1,
            bbox: item.metadata.source_location.bbox || { x: 0, y: 0, width: 100, height: 20 },
            text: item.metadata.original_extraction?.item_name || item.description || ''
          });
        }
      });
      setAnchors(newAnchors);
      setTotalPages(sourceMetadata.total_pages || 1);
    }
  }, [extractedItems, sourceMetadata]);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 200));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 50));
  const handleResetZoom = () => setZoom(100);

  const handlePrevPage = () => setCurrentPage(prev => Math.max(prev - 1, 1));
  const handleNextPage = () => setCurrentPage(prev => Math.min(prev + 1, totalPages));

  // Filter anchors for current page
  const currentPageAnchors = anchors.filter(a => a.page === currentPage);

  // Render different source types
  const renderSourceContent = () => {
    switch (sourceType) {
      case 'email':
        return (
          <div className="bg-white text-slate-900 p-8 rounded-lg shadow-lg max-w-4xl mx-auto">
            <div className="border-b border-slate-200 pb-4 mb-4">
              <div className="flex items-center gap-2 text-slate-600 mb-2">
                <Mail size={16} />
                <span className="text-sm font-medium">Email Source</span>
              </div>
              <div className="space-y-2 text-sm">
                {sourceMetadata?.sender && (
                  <div><span className="font-semibold">From:</span> {sourceMetadata.sender}</div>
                )}
                {sourceMetadata?.subject && (
                  <div><span className="font-semibold">Subject:</span> {sourceMetadata.subject}</div>
                )}
                {sourceMetadata?.date && (
                  <div><span className="font-semibold">Date:</span> {new Date(sourceMetadata.date).toLocaleString()}</div>
                )}
              </div>
            </div>
            <div 
              className="prose prose-slate max-w-none whitespace-pre-wrap"
              dangerouslySetInnerHTML={{ __html: sourceContent || '' }}
            />
          </div>
        );

      case 'pdf':
        return (
          <div className="relative bg-slate-100 rounded-lg overflow-hidden" style={{ minHeight: '600px' }}>
            {sourceUrl ? (
              <iframe
                src={`${sourceUrl}#page=${currentPage}&zoom=${zoom}`}
                className="w-full h-full min-h-[600px] border-0"
                title="PDF Source"
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-[600px] text-slate-500">
                <FileText size={64} className="mb-4 opacity-50" />
                <p className="text-lg font-medium">PDF Source Document</p>
                <p className="text-sm">Original file reference</p>
                {sourceMetadata?.filename && (
                  <p className="text-xs text-slate-400 mt-2">{sourceMetadata.filename}</p>
                )}
              </div>
            )}
            
            {/* Overlay anchors for extracted items */}
            {currentPageAnchors.map((anchor, idx) => (
              <button
                key={idx}
                onClick={() => onItemClick?.(anchor.itemIndex)}
                className={`absolute flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-all ${
                  selectedItemIndex === anchor.itemIndex
                    ? 'bg-orange-500 text-white shadow-lg scale-110 z-20'
                    : 'bg-blue-500/80 text-white hover:bg-blue-500 z-10'
                }`}
                style={{
                  left: `${anchor.bbox.x}%`,
                  top: `${anchor.bbox.y}%`,
                  width: `${anchor.bbox.width}%`,
                  height: `${Math.max(anchor.bbox.height, 3)}%`,
                }}
                title={`Item ${anchor.itemIndex + 1}: ${anchor.text.slice(0, 50)}...`}
              >
                <MapPin size={12} />
                {anchor.itemIndex + 1}
              </button>
            ))}
          </div>
        );

      case 'image':
        return (
          <div className="relative bg-slate-900 rounded-lg overflow-hidden flex items-center justify-center" style={{ minHeight: '600px' }}>
            {sourceUrl ? (
              <img
                src={sourceUrl}
                alt="Source"
                className="max-w-full max-h-[800px] object-contain"
                style={{ transform: `scale(${zoom / 100})` }}
              />
            ) : (
              <div className="flex flex-col items-center justify-center text-slate-500">
                <Image size={64} className="mb-4 opacity-50" />
                <p className="text-lg font-medium">Image Source</p>
                <p className="text-sm">Original image reference</p>
              </div>
            )}
            
            {/* Overlay anchors */}
            {currentPageAnchors.map((anchor, idx) => (
              <button
                key={idx}
                onClick={() => onItemClick?.(anchor.itemIndex)}
                className={`absolute flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold transition-all ${
                  selectedItemIndex === anchor.itemIndex
                    ? 'bg-orange-500 text-white shadow-lg scale-125 z-20'
                    : 'bg-blue-500/80 text-white hover:bg-blue-500 z-10'
                }`}
                style={{
                  left: `${anchor.bbox.x}%`,
                  top: `${anchor.bbox.y}%`,
                }}
                title={`Item ${anchor.itemIndex + 1}: ${anchor.text.slice(0, 50)}...`}
              >
                {anchor.itemIndex + 1}
              </button>
            ))}
          </div>
        );

      default:
        return (
          <div className="flex items-center justify-center h-[400px] text-slate-500">
            <p>Unknown source type</p>
          </div>
        );
    }
  };

  return (
    <div 
      ref={containerRef}
      className={`flex flex-col bg-slate-950 rounded-xl border border-slate-800 overflow-hidden ${className} ${isFullscreen ? 'fixed inset-4 z-50' : ''}`}
    >
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-3">
          {sourceType === 'pdf' && <FileText size={18} className="text-blue-400" />}
          {sourceType === 'email' && <Mail size={18} className="text-emerald-400" />}
          {sourceType === 'image' && <Image size={18} className="text-purple-400" />}
          <span className="font-medium text-slate-200">
            Source: {sourceMetadata?.filename || sourceType.toUpperCase()}
          </span>
          {totalPages > 1 && (
            <span className="text-sm text-slate-500">
              Page {currentPage} of {totalPages}
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* Page navigation for PDFs */}
          {sourceType === 'pdf' && totalPages > 1 && (
            <div className="flex items-center gap-1 mr-4">
              <button
                onClick={handlePrevPage}
                disabled={currentPage === 1}
                className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded disabled:opacity-30"
              >
                <ChevronLeft size={18} />
              </button>
              <span className="text-sm text-slate-500 px-2">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={handleNextPage}
                disabled={currentPage === totalPages}
                className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded disabled:opacity-30"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          )}
          
          {/* Zoom controls */}
          <div className="flex items-center gap-1 bg-slate-800/50 rounded-lg p-1">
            <button
              onClick={handleZoomOut}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700 rounded"
              title="Zoom out"
            >
              <ZoomOut size={16} />
            </button>
            <span className="text-xs text-slate-400 w-12 text-center">{zoom}%</span>
            <button
              onClick={handleZoomIn}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700 rounded"
              title="Zoom in"
            >
              <ZoomIn size={16} />
            </button>
            <button
              onClick={handleResetZoom}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700 rounded"
              title="Reset zoom"
            >
              <RotateCcw size={16} />
            </button>
          </div>
          
          {/* Fullscreen toggle */}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded ml-2"
          >
            {isFullscreen ? <X size={18} /> : <Maximize2 size={18} />}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4 bg-slate-950">
        {renderSourceContent()}
      </div>

      {/* Extraction Legend */}
      {anchors.length > 0 && (
        <div className="px-4 py-2 border-t border-slate-800 bg-slate-900/30">
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span className="font-medium">Extracted Items:</span>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-500/80" />
              <span>Click to highlight source</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-orange-500" />
              <span>Currently selected</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SourceDocumentViewer;
