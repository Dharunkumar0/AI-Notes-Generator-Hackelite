import React from 'react';
import { Download } from 'lucide-react';
import { exportService } from '../services/exportService';

// getHtml is a function that returns a string of HTML to render in the PDF
const DownloadPdfButton = ({ getHtml, filename = 'export.pdf', title = 'Export', className = 'btn-secondary' }) => {
  const handleClick = async () => {
    try {
      const html = getHtml?.();
      if (!html || typeof html !== 'string') return;
      await exportService.downloadPdf(html, filename, title);
    } catch (err) {
      console.error('Failed to download PDF', err);
    }
  };

  return (
    <button onClick={handleClick} className={className}>
      <Download className="h-4 w-4 mr-2" />
      Download PDF
    </button>
  );
};

export default DownloadPdfButton;


