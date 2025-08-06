import React, { useState, useRef, useEffect } from 'react';
import { File, Upload, FileText, Loader, Info, X } from 'lucide-react';
import { pdfService } from '../services/pdfService';

const PDF = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [pdfInfo, setPdfInfo] = useState(null);
  const [extractedText, setExtractedText] = useState(null);
  const [error, setError] = useState('');
  const [formats, setFormats] = useState(null);
  const fileInputRef = useRef();

  useEffect(() => {
    // Get supported formats when component mounts
    const getFormats = async () => {
      try {
        const { data } = await pdfService.getSupportedFormats();
        setFormats(data);
      } catch (err) {
        console.error('Failed to get supported formats:', err);
      }
    };
    getFormats();
  }, []);

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Reset states
    setError('');
    setPdfInfo(null);
    setExtractedText(null);

    try {
      setIsProcessing(true);

      // Get PDF info first
      const info = await pdfService.getPDFInfo(file);
      setPdfInfo(info);

      // Then extract text
      const result = await pdfService.extractText(file);
      setExtractedText(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process PDF');
    } finally {
      setIsProcessing(false);
    }
  };

  const clearResults = () => {
    setExtractedText(null);
    setPdfInfo(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">PDF Processor</h1>
          <p className="text-gray-600 dark:text-gray-400">Extract and process text from PDF documents</p>
        </div>
        <div className="flex items-center space-x-2">
          <File className="h-8 w-8 text-primary-600" />
        </div>
      </div>

      <div className="card">
        <div className="text-center py-12">
          {!extractedText && !isProcessing && (
            <>
              <File className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">PDF Text Extraction</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Upload PDF files ({formats?.max_file_size} max) to extract and process text content
              </p>
              <div className="flex justify-center space-x-4">
                <input
                  type="file"
                  ref={fileInputRef}
                  accept=".pdf"
                  className="hidden"
                  onChange={handleFileUpload}
                />
                <button
                  className="btn-primary flex items-center"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isProcessing}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Upload PDF
                </button>
              </div>
            </>
          )}

          {isProcessing && (
            <div className="flex flex-col items-center">
              <Loader className="h-8 w-8 animate-spin text-primary-600 mb-4" />
              <p className="text-gray-600">Processing PDF...</p>
            </div>
          )}

          {error && (
            <div className="mt-6 text-red-500">
              {error}
            </div>
          )}

          {(pdfInfo || extractedText) && !isProcessing && (
            <div className="text-left">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold">Results</h3>
                <button
                  onClick={clearResults}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {pdfInfo && (
                <div className="mb-6 bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2 flex items-center">
                    <Info className="h-4 w-4 mr-2" />
                    Document Information
                  </h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p><span className="font-medium">Title:</span> {pdfInfo.title}</p>
                      <p><span className="font-medium">Author:</span> {pdfInfo.author}</p>
                      <p><span className="font-medium">Pages:</span> {pdfInfo.total_pages}</p>
                    </div>
                    <div>
                      <p><span className="font-medium">Created:</span> {pdfInfo.creation_date}</p>
                      <p><span className="font-medium">Modified:</span> {pdfInfo.modification_date}</p>
                      <p><span className="font-medium">Producer:</span> {pdfInfo.producer}</p>
                    </div>
                  </div>
                </div>
              )}

              {extractedText && (
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-semibold">Extracted Text</h4>
                    <span className="text-sm text-gray-500">
                      {extractedText.word_count} words | {extractedText.total_pages} pages | {Math.round(extractedText.processing_time * 100) / 100}s
                    </span>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg max-h-96 overflow-y-auto">
                    {extractedText.pages.map((page, index) => (
                      <div key={index} className="mb-4">
                        <div className="text-sm text-gray-500 mb-1">Page {page.page}</div>
                        <p className="whitespace-pre-wrap">{page.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PDF; 