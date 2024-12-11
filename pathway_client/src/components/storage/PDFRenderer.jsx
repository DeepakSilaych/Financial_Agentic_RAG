import { useState, useRef, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

export default function PDFRenderer({ pdf, currentPage, setCurrentPage }) {
  const containerRef = useRef(null);
  const [scale, setScale] = useState(1);
  const [numPages, setNumPages] = useState(null);
  const [pageHeight, setPageHeight] = useState(0);

  const onLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    updateScale();
  };

  const onPageLoadSuccess = ({ height, width }) => {
    if (height && width && containerRef.current) {
      const calculatedHeight =
        height * (containerRef.current.offsetWidth / width);
      setPageHeight(calculatedHeight);
    }
  };

  const updateScale = () => {
    if (containerRef.current) {
      const containerWidth = containerRef.current.offsetWidth;
      setScale(containerWidth / 600);
    }
  };

  useEffect(() => {
    updateScale();
    window.addEventListener("resize", updateScale);
    return () => window.removeEventListener("resize", updateScale);
  }, []);

  useEffect(() => {
    if (containerRef.current && pageHeight) {
      containerRef.current.scrollTo({
        top: (currentPage + 1) * pageHeight,
        behavior: "smooth",
      });
    }
  }, [currentPage, pageHeight]);

  return (
    <div
      ref={containerRef}
      className="h-full w-3/4 mx-auto border-[2px] overflow-y-auto overflow-x-hidden rounded-lg shadow-md"
      // style={{ height: pageHeight ? `${pageHeight * numPages}px` : 'auto' }}
    >
      <Document file={pdf} onLoadSuccess={onLoadSuccess}>
        {Array.from(new Array(numPages), (_, index) => (
          <div
            key={index}
            className="border-y-[1px]"
            // style={{ minHeight: pageHeight ? `${pageHeight}px` : 'auto' }}
          >
            <Page
              pageNumber={index + 1}
              renderTextLayer={false}
              renderAnnotationLayer={false}
              scale={scale}
              onLoadSuccess={onPageLoadSuccess}
            />
          </div>
        ))}
      </Document>
    </div>
  );
}
