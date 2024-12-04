import { useState, useRef, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

export default function PDFRenderer({ pdf }) {
  const containerRef = useRef(null);
	const [scale, setScale] = useState(1);
	const [numPages, setNumPages] = useState(null);

	const onLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    updateScale(); // Update scale when document is loaded
  };

	const updateScale = () => {
    if (containerRef.current) {
      const containerWidth = containerRef.current.offsetWidth;
      setScale(containerWidth / 600);
    }
  };

  useEffect(() => {
    window.addEventListener('resize', updateScale);

    return () => {
      window.removeEventListener('resize', updateScale);
    };
  }, []);

  return (
		<div ref={containerRef} className='mt-12 w-full min-h-48 border-[2px]'>
			<Document file={pdf} onLoadSuccess={onLoadSuccess}>
			{Array.from(new Array(numPages), (_, pageIndex) => (
				<div key={pageIndex} className='border-y-[1px]'>
					<Page
						pageNumber={pageIndex + 1} // Pages are 1-indexed
						renderTextLayer={false}
						renderAnnotationLayer={false}
						scale={scale}
					/>
				</div>
			))}
			</Document>
		</div>
  );
}