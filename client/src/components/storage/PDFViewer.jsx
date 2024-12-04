import React, { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ChevronLeft, ChevronRight, X, Download, ZoomIn, ZoomOut, Loader2, File } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

const PDFViewer = ({ url, filename, onClose }) => {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const onDocumentLoadSuccess = ({ numPages }) => {
    setLoading(false);
    setNumPages(numPages);
    setError(null);
  };

  const onDocumentLoadError = (error) => {
    setLoading(false);
    setError('Error loading PDF. Please try again.');
    console.error('PDF load error:', error);
  };

  const changePage = (offset) => {
    setPageNumber(prevPageNumber => {
      const newPageNumber = prevPageNumber + offset;
      return Math.min(Math.max(1, newPageNumber), numPages);
    });
  };

  const previousPage = () => changePage(-1);
  const nextPage = () => changePage(1);

  const zoomIn = () => setScale(prev => Math.min(prev + 0.1, 2.0));
  const zoomOut = () => setScale(prev => Math.max(prev - 0.1, 0.5));

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center"
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          transition={{ type: "spring", duration: 0.3 }}
          className="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-2xl w-full max-w-6xl h-[90vh] flex flex-col border border-white/60"
        >
          {/* Header */}
          <motion.div
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="flex items-center justify-between px-8 py-5 border-b border-gray-100 bg-white/50 backdrop-blur-sm"
          >
            <div className="flex items-center space-x-3">
              <div className="bg-blue-100 p-2 rounded-xl">
                <File className="w-5 h-5 text-blue-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-900">{filename}</h3>
            </div>
            <div className="flex items-center space-x-3">
              <motion.a
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                href={`http://localhost:8000/files/${filename}`}
                download={filename}
                className="p-3 text-gray-500 hover:text-gray-700 hover:bg-blue-50 rounded-xl transition-all duration-200 flex items-center space-x-2"
                title="Download PDF"
              >
                <Download size={18} />
                <span className="text-sm font-medium">Download</span>
              </motion.a>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onClose}
                className="p-3 text-gray-500 hover:text-gray-700 hover:bg-red-50 rounded-xl transition-all duration-200"
                title="Close preview"
              >
                <X size={18} />
              </motion.button>
            </div>
          </motion.div>

          {/* PDF Viewer */}
          <div className="flex-1 overflow-auto p-8 relative bg-gray-50">
            {loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 flex items-center justify-center bg-white/90 backdrop-blur-sm"
              >
                <div className="flex flex-col items-center space-y-4">
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-blue-200 rounded-full animate-spin border-t-blue-500"></div>
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                      <File className="w-6 h-6 text-blue-500" />
                    </div>
                  </div>
                  <span className="text-sm font-medium text-gray-600">Loading PDF...</span>
                </div>
              </motion.div>
            )}

            {error && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute inset-0 flex items-center justify-center"
              >
                <div className="bg-white p-8 rounded-2xl shadow-xl text-center max-w-md mx-auto">
                  <div className="bg-red-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                    <X className="w-8 h-8 text-red-500" />
                  </div>
                  <p className="text-xl font-semibold text-gray-900 mb-2">{error}</p>
                  <p className="text-gray-500 mb-6">Please try again or contact support if the issue persists.</p>
                  <button
                    onClick={() => window.location.reload()}
                    className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-blue-700 transition-all duration-200"
                  >
                    Retry
                  </button>
                </div>
              </motion.div>
            )}

            <Document
              file={url}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={null}
              className="flex flex-col items-center"
            >
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <Page
                  pageNumber={pageNumber}
                  scale={scale}
                  className="shadow-2xl rounded-xl"
                  renderTextLayer={true}
                  renderAnnotationLayer={true}
                  loading={null}
                />
              </motion.div>
            </Document>
          </div>

          {/* Controls */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="px-8 py-5 border-t border-gray-100 flex items-center justify-between bg-white/50 backdrop-blur-sm"
          >
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2 bg-gray-100 px-3 py-1.5 rounded-lg">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={zoomOut}
                  className="p-2 text-gray-600 hover:bg-white rounded-lg transition-all duration-200"
                  disabled={scale <= 0.5}
                  title="Zoom Out"
                >
                  <ZoomOut size={18} />
                </motion.button>
                <span className="text-sm font-semibold text-gray-700 min-w-[60px] text-center">
                  {Math.round(scale * 100)}%
                </span>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={zoomIn}
                  className="p-2 text-gray-600 hover:bg-white rounded-lg transition-all duration-200"
                  disabled={scale >= 2.0}
                  title="Zoom In"
                >
                  <ZoomIn size={18} />
                </motion.button>
              </div>
            </div>

            <div className="flex items-center bg-gray-100 rounded-lg px-3 py-1.5">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={previousPage}
                disabled={pageNumber <= 1}
                className="p-2 text-gray-600 hover:bg-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Previous Page"
              >
                <ChevronLeft size={18} />
              </motion.button>
              <span className="text-sm font-semibold text-gray-700 min-w-[120px] text-center">
                Page {pageNumber} of {numPages}
              </span>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={nextPage}
                disabled={pageNumber >= numPages}
                className="p-2 text-gray-600 hover:bg-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Next Page"
              >
                <ChevronRight size={18} />
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default PDFViewer;
