import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';

// Set worker source for pdf.js
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const PDFViewer = ({ isOpen, onClose, file, targetPage = 1 }) => {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(targetPage);
  const [scale, setScale] = useState(1.0);

  useEffect(() => {
    if (targetPage && targetPage <= numPages) {
      setPageNumber(targetPage);
    }
  }, [targetPage, numPages]);

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  const changePage = (offset) => {
    setPageNumber(prevPageNumber => {
      const newPage = prevPageNumber + offset;
      return newPage >= 1 && newPage <= numPages ? newPage : prevPageNumber;
    });
  };

  const handleZoom = (factor) => {
    setScale(prevScale => {
      const newScale = prevScale * factor;
      return newScale >= 0.5 && newScale <= 2.0 ? newScale : prevScale;
    });
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={onClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%] bg-white rounded-lg shadow-lg w-[90vw] h-[90vh] p-6">
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => handleZoom(0.8)}
                className="px-3 py-1 bg-gray-200 rounded-lg hover:bg-gray-300"
              >
                -
              </button>
              <span>{Math.round(scale * 100)}%</span>
              <button
                onClick={() => handleZoom(1.2)}
                className="px-3 py-1 bg-gray-200 rounded-lg hover:bg-gray-300"
              >
                +
              </button>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => changePage(-1)}
                disabled={pageNumber <= 1}
                className="px-3 py-1 bg-gray-200 rounded-lg hover:bg-gray-300 disabled:opacity-50"
              >
                Previous
              </button>
              <span>
                Page {pageNumber} of {numPages}
              </span>
              <button
                onClick={() => changePage(1)}
                disabled={pageNumber >= numPages}
                className="px-3 py-1 bg-gray-200 rounded-lg hover:bg-gray-300 disabled:opacity-50"
              >
                Next
              </button>
            </div>

            <Dialog.Close className="p-2 hover:bg-gray-100 rounded-full">
              <X size={24} />
            </Dialog.Close>
          </div>

          <div className="flex-1 overflow-auto h-[calc(90vh-8rem)] flex justify-center">
            <Document
              file={file}
              onLoadSuccess={onDocumentLoadSuccess}
              className="max-w-full"
            >
              <Page
                pageNumber={pageNumber}
                scale={scale}
                className="shadow-lg"
                renderTextLayer={false}
                renderAnnotationLayer={false}
              />
            </Document>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

export default PDFViewer;