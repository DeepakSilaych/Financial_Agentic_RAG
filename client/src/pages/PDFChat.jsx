import { useEffect, useState } from "react";
import PDFRenderer from "../components/storage/PDFRenderer";

export default function PDFChat () {
	const [pdfBlob, setPdfBlob] = useState(null);

	useEffect(() => {
		const url = localStorage.getItem("pdf_req_url");
		if (!url)
			return;
		
		fetch(url)
		.then(async (response) => {
			if (!response.ok)
				throw new Error(`Download failed with status: ${response.status}`);
			const blob = await response.blob();
			setPdfBlob(blob);
		});
	}, []);

	return pdfBlob ? (
		<div className="p-4 w-full flex">
			<div className='w-3/5'>
			</div>
			<div className='w-2/5 h-full'>
				<PDFRenderer pdf={pdfBlob} setPage={5} />
			</div>
		</div>
	) : <></>;
};