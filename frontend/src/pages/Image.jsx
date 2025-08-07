import React, { useState, useRef } from 'react';
import { 
  Upload, 
  FileImage, 
  Text, 
  FileText, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  X,
  Download,
  Trash2,
  Eye,
  History
} from 'lucide-react';
import { imageService } from '../services/imageService';
import { useAuth } from '../contexts/AuthContext';
import { format } from 'date-fns';

const ImagePage = () => {
  const { user } = useAuth();
  const fileInputRef = useRef(null);
  
  // State for file upload and processing
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState('');
  
  // State for results
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  // State for history
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);
  const [showHistoryDetail, setShowHistoryDetail] = useState(false);

  // Handle file selection
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Please select a valid image file (JPG, PNG, etc.)');
        return;
      }
      
      // Validate file size (10MB limit)
      if (file.size > 10 * 1024 * 1024) {
        setError('File size too large. Maximum size is 10MB.');
        return;
      }
      
      setSelectedFile(file);
      setError(null);
      
      // Create preview URL
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  // Handle drag and drop
  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file) {
      fileInputRef.current.files = event.dataTransfer.files;
      handleFileSelect({ target: { files: [file] } });
    }
  };

  // Process image
  const handleProcessImage = async () => {
    if (!selectedFile) {
      setError('Please select an image file first.');
      return;
    }

    try {
      setIsProcessing(true);
      setError(null);
      setProcessingProgress('Uploading image...');
      
      const response = await imageService.processImage(selectedFile);
      
      setProcessingProgress('Processing complete!');
      setResult(response);
      
      // Refresh history
      loadHistory();
      
    } catch (error) {
      setError(error.response?.data?.detail || error.message || 'Failed to process image');
    } finally {
      setIsProcessing(false);
      setProcessingProgress('');
    }
  };

  // Load history
  const loadHistory = async () => {
    try {
      const data = await imageService.getImageHistory();
      setHistory(data);
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  // Handle history item selection
  const handleViewHistoryDetail = (item) => {
    setSelectedHistoryItem(item);
    setShowHistoryDetail(true);
  };

  // Handle history item deletion
  const handleDeleteHistoryItem = async (itemId) => {
    if (window.confirm('Are you sure you want to delete this record?')) {
      try {
        await imageService.deleteImageRecord(itemId);
        loadHistory();
      } catch (error) {
        setError('Failed to delete record');
      }
    }
  };

  // Clear all history
  const handleClearHistory = async () => {
    if (window.confirm('Are you sure you want to clear all image processing history?')) {
      try {
        await imageService.clearImageHistory();
        setHistory([]);
      } catch (error) {
        setError('Failed to clear history');
      }
    }
  };

  // Download extracted text
  const handleDownloadText = (text, filename) => {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}_extracted_text.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Image OCR & Summarizer</h1>
          <p className="text-gray-600 dark:text-gray-400">Upload images to extract text and generate summaries</p>
        </div>
        <div className="flex items-center space-x-2">
          <FileImage className="h-8 w-8 text-primary-600" />
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="card bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-400 mr-3" />
            <p className="text-red-800 dark:text-red-200">{error}</p>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-400 hover:text-red-600"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Upload Section */}
      <div className="card">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Upload Image
          </h2>
          
          {/* File Upload Area */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              selectedFile
                ? 'border-primary-300 bg-primary-50 dark:bg-primary-900/20'
                : 'border-gray-300 dark:border-gray-600 hover:border-primary-400'
            }`}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
            />
            
            {!selectedFile ? (
              <div>
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                  Drop your image here or click to browse
                </p>
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  Supports JPG, PNG, and other image formats (max 10MB)
                </p>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="btn-primary"
                >
                  Choose File
                </button>
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-center mb-4">
                  <img
                    src={previewUrl}
                    alt="Preview"
                    className="max-h-32 max-w-full rounded-lg"
                  />
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </p>
                <div className="flex items-center justify-center space-x-2">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="btn-secondary"
                  >
                    Change File
                  </button>
                  <button
                    onClick={() => {
                      setSelectedFile(null);
                      setPreviewUrl(null);
                      if (previewUrl) URL.revokeObjectURL(previewUrl);
                    }}
                    className="btn-error"
                  >
                    Remove
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Process Button */}
          {selectedFile && (
            <div className="mt-6 text-center">
              <button
                onClick={handleProcessImage}
                disabled={isProcessing}
                className="btn-primary flex items-center justify-center mx-auto"
              >
                {isProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Processing...
                  </>
                ) : (
                  <>
                    <Text className="h-4 w-4 mr-2" />
                    Extract Text & Summarize
                  </>
                )}
              </button>
              
              {processingProgress && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                  {processingProgress}
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Results Section */}
      {result && (
        <div className="card">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Processing Results
              </h2>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {result.processing_time ? `${result.processing_time.toFixed(2)}s` : 'N/A'}
                </span>
                <CheckCircle className="h-5 w-5 text-green-500" />
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <p className="text-sm text-blue-600 dark:text-blue-400">Words Extracted</p>
                <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                  {result.word_count}
                </p>
              </div>
              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                <p className="text-sm text-green-600 dark:text-green-400">Characters</p>
                <p className="text-2xl font-bold text-green-900 dark:text-green-100">
                  {result.character_count}
                </p>
              </div>
              <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                <p className="text-sm text-purple-600 dark:text-purple-400">Key Points</p>
                <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">
                  {result.summary.key_points?.length || 0}
                </p>
              </div>
            </div>

            {/* Extracted Text */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-md font-semibold text-gray-900 dark:text-gray-100">
                  Extracted Text
                </h3>
                <button
                  onClick={() => handleDownloadText(result.extracted_text, result.filename)}
                  className="text-primary-600 hover:text-primary-700 text-sm flex items-center"
                >
                  <Download className="h-4 w-4 mr-1" />
                  Download
                </button>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg max-h-48 overflow-y-auto">
                <p className="text-gray-700 dark:text-gray-300 text-sm whitespace-pre-wrap">
                  {result.extracted_text}
                </p>
              </div>
            </div>

            {/* Summary */}
            <div>
              <h3 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-2">
                AI Summary
              </h3>
              
              {/* Main Summary */}
              {result.summary.main_summary && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Main Summary
                  </h4>
                  <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                    <p className="text-gray-700 dark:text-gray-300 text-sm">
                      {result.summary.main_summary}
                    </p>
                  </div>
                </div>
              )}

              {/* Key Points */}
              {result.summary.key_points && result.summary.key_points.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Key Points
                  </h4>
                  <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                    <ul className="list-disc list-inside space-y-1">
                      {result.summary.key_points.map((point, index) => (
                        <li key={index} className="text-gray-700 dark:text-gray-300 text-sm">
                          {point}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Important Details */}
              {result.summary.important_details && result.summary.important_details.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Important Details
                  </h4>
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg">
                    <ul className="list-disc list-inside space-y-1">
                      {result.summary.important_details.map((detail, index) => (
                        <li key={index} className="text-gray-700 dark:text-gray-300 text-sm">
                          {detail}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* History Section */}
      <div className="card">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Processing History
            </h2>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="btn-secondary flex items-center"
              >
                <History className="h-4 w-4 mr-2" />
                {showHistory ? 'Hide' : 'Show'} History
              </button>
              {showHistory && history.length > 0 && (
                <button
                  onClick={handleClearHistory}
                  className="btn-error flex items-center"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear All
                </button>
              )}
            </div>
          </div>

          {showHistory && (
            <div>
              {history.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                  No processing history found. Upload an image to get started!
                </p>
              ) : (
                <div className="space-y-3">
                  {history.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                    >
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 dark:text-gray-100">
                          {item.filename}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {format(new Date(item.created_at), 'PPpp')} • {item.word_count} words
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleViewHistoryDetail(item)}
                          className="text-blue-600 hover:text-blue-700 p-1"
                          title="View details"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteHistoryItem(item.id)}
                          className="text-red-600 hover:text-red-700 p-1"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* History Detail Modal */}
      {showHistoryDetail && selectedHistoryItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                  {selectedHistoryItem.filename}
                </h2>
                <button
                  onClick={() => setShowHistoryDetail(false)}
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                  <span>Created: {format(new Date(selectedHistoryItem.created_at), 'PPpp')}</span>
                  <span>Processing Time: {selectedHistoryItem.processing_time ? `${selectedHistoryItem.processing_time.toFixed(2)}s` : 'N/A'}</span>
                  <span>Words: {selectedHistoryItem.word_count}</span>
                </div>
                
                {/* Extracted Text */}
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Extracted Text</h3>
                  <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg max-h-32 overflow-y-auto">
                    <p className="text-gray-700 dark:text-gray-300 text-sm whitespace-pre-wrap">
                      {selectedHistoryItem.extracted_text}
                    </p>
                  </div>
                </div>
                
                {/* Summary */}
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Summary</h3>
                  <div className="space-y-3">
                    {selectedHistoryItem.summary.main_summary && (
                      <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Main Summary</h4>
                        <p className="text-gray-700 dark:text-gray-300 text-sm">
                          {selectedHistoryItem.summary.main_summary}
                        </p>
                      </div>
                    )}
                    
                    {selectedHistoryItem.summary.key_points && selectedHistoryItem.summary.key_points.length > 0 && (
                      <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Key Points</h4>
                        <ul className="list-disc list-inside space-y-1">
                          {selectedHistoryItem.summary.key_points.map((point, index) => (
                            <li key={index} className="text-gray-700 dark:text-gray-300 text-sm">{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImagePage;
