import React, { useState, useRef, useEffect } from 'react';
import { File, Upload, FileText, Loader, Info, X, BookOpen, Copy } from 'lucide-react';
import { pdfService } from '../services/pdfService';
import toast from 'react-hot-toast';
import DownloadPdfButton from '../components/DownloadPdfButton';

const PDF = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [pdfInfo, setPdfInfo] = useState(null);
  const [extractedText, setExtractedText] = useState(null);
  const [error, setError] = useState('');
  const [formats, setFormats] = useState(null);
  const [summary, setSummary] = useState(null);
  const [summarizing, setSummarizing] = useState(false);
  const [maxLength, setMaxLength] = useState(500);
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
    setSummary(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSummarize = async (pageIndex) => {
    try {
      setSummarizing(true);
      setError('');
      const text = extractedText.pages[pageIndex].text;
      const result = await pdfService.summarizeText(text, maxLength);
      setSummary({
        ...result,
        pageIndex
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to summarize text');
    } finally {
      setSummarizing(false);
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
                <div className="flex items-center space-x-4">
                  <DownloadPdfButton
                    className="btn-secondary flex items-center space-x-2"
                    filename="pdf-extraction.pdf"
                    title="PDF Analysis Results"
                    getHtml={() => `
                      <div class="container">
                        <h1>PDF Analysis Results</h1>
                        <div class="meta">
                          ${pdfInfo ? `
                            <p>Title: ${pdfInfo.title || 'N/A'}</p>
                            <p>Author: ${pdfInfo.author || 'N/A'}</p>
                            <p>Pages: ${pdfInfo.pages}</p>
                            <p>Created: ${pdfInfo.created || 'N/A'}</p>
                          ` : ''}
                        </div>
                        ${extractedText.pages.map((page, index) => `
                          <div class="section">
                            <h2>Page ${page.page}</h2>
                            <p>${page.text}</p>
                            ${summary && summary.pageIndex === index ? `
                              <div class="summary">
                                <h3>Summary</h3>
                                <p>${summary.summary}</p>
                                <div class="meta">
                                  Word count: ${summary.word_count}
                                  Processing time: ${summary.processing_time.toFixed(2)}s
                                </div>
                              </div>
                            ` : ''}
                          </div>
                        `).join('')}
                        <div class="meta">
                          Generated on ${new Date().toLocaleString()}
                        </div>
                      </div>
                    `}
                  >
                    <FileText className="h-4 w-4" />
                    <span>Export PDF</span>
                  </DownloadPdfButton>
                  <button
                    onClick={clearResults}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
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

                  {/* Summarization Controls */}
                  <div className="mb-4 bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Max Summary Length (words)
                        </label>
                        <input
                          type="number"
                          value={maxLength}
                          onChange={(e) => setMaxLength(Number(e.target.value))}
                          min="100"
                          max="1000"
                          className="input-field w-32"
                        />
                      </div>
                      <div className="text-sm text-gray-500">
                        Select a page and click "Summarize" to generate a summary
                      </div>
                    </div>
                  </div>

                  {/* Summary Results */}
                  {summary && (
                    <div className="mb-4 bg-primary-50 dark:bg-primary-900/20 p-4 rounded-lg">
                      <h4 className="font-semibold mb-2">Summary of Page {summary.pageIndex + 1}</h4>
                      <p className="text-gray-700 dark:text-gray-300">{summary.summary}</p>
                      <div className="mt-2 text-sm text-gray-500">
                        Processing time: {summary.processing_time.toFixed(2)}s | 
                        Word count: {summary.word_count}
                      </div>
                    </div>
                  )}

                  {/* Extracted Text by Page */}
                  <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg max-h-96 overflow-y-auto">
                    {extractedText.pages.map((page, index) => (
                      <div key={index} className="mb-4">
                        <div className="flex justify-between items-center mb-2">
                          <div className="text-sm text-gray-500">Page {page.page}</div>
                          <button
                            onClick={() => handleSummarize(index)}
                            disabled={summarizing}
                            className="btn-secondary btn-sm"
                          >
                            {summarizing && summary?.pageIndex === index ? (
                              <Loader className="h-4 w-4 animate-spin" />
                            ) : (
                              'Summarize'
                            )}
                          </button>
                        </div>
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