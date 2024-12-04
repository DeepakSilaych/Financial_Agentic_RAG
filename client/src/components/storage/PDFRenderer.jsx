// import { useState, useRef, useEffect } from 'react';
// import { Document, Page, pdfjs } from 'react-pdf';
// pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

// export default function PDFRenderer({ pdf }) {
//   const containerRef = useRef(null);
//   const [scale, setScale] = useState(1);
//   const [numPages, setNumPages] = useState(null);
//   const [pageHeight, setPageHeight] = useState(0);

//   const onLoadSuccess = ({ numPages }) => {
//     setNumPages(numPages);
//     updateScale();
//   };

//   const onPageLoadSuccess = ({ height, width }) => {
//     if (height && width) {
//       const calculatedHeight = height * (containerRef.current.offsetWidth / width);
//       setPageHeight(calculatedHeight);
//     }
//   };

//   const updateScale = () => {
//     if (containerRef.current) {
//       const containerWidth = containerRef.current.offsetWidth;
//       setScale(containerWidth / 600);
//     }
//   };

//   useEffect(() => {
// 		updateScale();
//     window.addEventListener('resize', updateScale);
//     return () => {
//       window.removeEventListener('resize', updateScale);
//     };
//   }, []);

//   return (
//     <div
//       ref={containerRef}
//       className="h-full w-full border-[2px] overflow-y-auto overflow-x-hidden rounded-lg shadow-md"
//       style={{ height: pageHeight ? `${pageHeight}px` : 'auto' }}
//     >
//       <Document file={pdf} onLoadSuccess={onLoadSuccess}>
//         {Array.from(new Array(numPages), (_, pageIndex) => (
//           <div
//             key={pageIndex}
//             className="border-y-[1px]"
//             style={{ minHeight: pageHeight ? `${pageHeight}px` : 'auto' }}
//           >
//             <Page
//               pageNumber={pageIndex + 1}
//               renderTextLayer={false}
//               renderAnnotationLayer={false}
//               scale={scale}
//               onLoadSuccess={onPageLoadSuccess}
//             />
//           </div>
//         ))}
//       </Document>
//     </div>
//   );
// }

import { useState, useRef, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

export default function PDFRenderer({ pdf }) {
  const containerRef = useRef(null);
  const [scale, setScale] = useState(1);
  const [numPages, setNumPages] = useState(null);
  const [pageHeight, setPageHeight] = useState(0);
  const [scrollPosition, setScrollPosition] = useState(0);  // Track scroll position

  const onLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    updateScale();
  };

  const onPageLoadSuccess = ({ height, width }) => {
    if (height && width) {
      const calculatedHeight = height * (containerRef.current.offsetWidth / width);
      setPageHeight(calculatedHeight);
    }
  };

  const updateScale = () => {
    if (containerRef.current) {
      const containerWidth = containerRef.current.offsetWidth;
      setScale(containerWidth / 600);
    }
  };

  const handleScroll = () => {
    if (containerRef.current) {
      setScrollPosition(containerRef.current.scrollTop);
    }
  };

  useEffect(() => {
    updateScale();
    window.addEventListener('resize', updateScale);

    if (containerRef.current) {
      containerRef.current.addEventListener('scroll', handleScroll);
    }

    return () => {
      window.removeEventListener('resize', updateScale);
      if (containerRef.current) {
        containerRef.current.removeEventListener('scroll', handleScroll);
      }
    };
  }, []);

  return (
		<Document file={pdf} onLoadSuccess={onLoadSuccess}>
			{console.log(scrollPosition)}
			<div
				ref={containerRef}
				className="h-full w-full border-[2px] overflow-y-auto overflow-x-hidden rounded-lg shadow-md"
				style={{ height: pageHeight ? `${pageHeight * numPages}px` : 'auto' }}
			>
        {Array.from(new Array(numPages), (_, pageIndex) => (
          <div
            key={pageIndex}
            className="border-y-[1px]"
            style={{ minHeight: pageHeight ? `${pageHeight}px` : 'auto' }}
          >
            <Page
              pageNumber={pageIndex + 1}
              renderTextLayer={false}
              renderAnnotationLayer={false}
              scale={scale}
              onLoadSuccess={onPageLoadSuccess}
            />
          </div>
        ))}
      </div>
		</Document>
  );
}
