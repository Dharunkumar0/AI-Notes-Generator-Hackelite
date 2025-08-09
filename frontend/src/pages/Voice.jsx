import React, { useState, useRef, useEffect } from 'react';
import { Mic, Upload, FileText, Copy, Download, Play, Square, AlertCircle } from 'lucide-react';
import { voiceService } from '../services/voiceService';
import toast from 'react-hot-toast';

const Voice = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(10);
  const [transcription, setTranscription] = useState('');
  const [confidence, setConfidence] = useState(null);
  const [duration, setDuration] = useState(null);
  const [wordCount, setWordCount] = useState(null);
  const [timestamps, setTimestamps] = useState([]);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState('');
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [supportedFormats, setSupportedFormats] = useState(['wav', 'mp3', 'm4a', 'ogg', 'flac']);
  const fileInputRef = useRef();

  useEffect(() => {
    // Fetch supported formats when component mounts
    const getFormats = async () => {
      try {
        const result = await voiceService.getSupportedFormats();
        if (result.success && result.data?.supported_formats) {
          setSupportedFormats(result.data.supported_formats);
        }
      } catch (err) {
        console.error('Failed to get supported formats:', err);
        // Keep default formats on error
      }
    };
    getFormats();
  }, []);

  const clearResults = () => {
    setTranscription('');
    setConfidence(null);
    setDuration(null);
    setWordCount(null);
    setTimestamps([]);
    setSummary('');
    setError('');
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    clearResults();

    try {
      setError('Processing audio file...');
      
      const result = await voiceService.transcribeAudioFile(file);

      if (result.success && result.data) {
        setTranscription(result.data.transcription || '');
        setConfidence(result.data.confidence || 0.95);
        setDuration(result.data.duration || 0);
        setWordCount(result.data.word_count || 0);
        setTimestamps(result.data.timestamps || []);
        setError('');
        toast.success('Audio transcribed successfully!');
      } else {
        throw new Error(result.error || 'Transcription failed');
      }

    } catch (err) {
      const errorMessage = err.message || 'Failed to transcribe audio file';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsProcessing(false);
      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleMicrophoneRecord = async () => {
    if (isRecording) {
      // Stop recording logic would go here
      setIsRecording(false);
      return;
    }

    setIsRecording(true);
    setIsProcessing(true);
    clearResults();

    try {
      setError(`Recording for ${recordingDuration} seconds...`);
      
      const result = await voiceService.recordAndTranscribe(recordingDuration);

      if (result.success && result.data) {
        setTranscription(result.data.transcription || '');
        setConfidence(result.data.confidence || 0.95);
        setDuration(result.data.duration || recordingDuration);
        setWordCount(result.data.word_count || 0);
        setTimestamps(result.data.timestamps || []);
        setError('');
        toast.success('Recording transcribed successfully!');
      } else {
        throw new Error(result.error || 'Recording transcription failed');
      }

    } catch (err) {
      const errorMessage = err.message || 'Failed to record and transcribe audio';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsRecording(false);
      setIsProcessing(false);
    }
  };

  const handleSummarize = async () => {
    if (!transcription || !transcription.trim()) {
      toast.error('No transcription available to summarize');
      return;
    }
    
    setIsSummarizing(true);
    setSummary('');
    
    try {
      const result = await voiceService.summarizeTranscription(transcription);
      
      if (result && result.summary) {
        setSummary(result.summary);
        toast.success('Summary generated successfully!');
      } else {
        throw new Error('No summary generated');
      }
    } catch (err) {
      const errorMessage = err.message || 'Failed to generate summary';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsSummarizing(false);
    }
  };

  const copyToClipboard = async (text, label) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`${label} copied to clipboard!`);
    } catch (err) {
      toast.error('Failed to copy to clipboard');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Voice to Text</h1>
          <p className="text-gray-600 dark:text-gray-400">Convert voice recordings to text with AI</p>
        </div>
        <div className="flex items-center space-x-2">
          <Mic className="h-8 w-8 text-primary-600" />
        </div>
      </div>

      <div className="card">
        <div className="text-center py-12">
          <Mic className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Voice Transcription</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Upload audio files ({supportedFormats.join(', ')}) or record directly to convert speech to text
          </p>

          <div className="flex flex-col items-center space-y-6">
            {/* File Upload */}
            <input
              type="file"
              ref={fileInputRef}
              accept={supportedFormats.map(format => `.${format}`).join(',')}
              className="hidden"
              onChange={handleFileUpload}
              disabled={isProcessing}
            />
            
            <button
              className="btn-primary flex items-center"
              onClick={() => fileInputRef.current?.click()}
              disabled={isProcessing || isRecording}
            >
              <Upload className="h-4 w-4 mr-2" />
              Upload Audio File
            </button>

            {/* Recording Controls */}
            <div className="flex flex-col items-center space-y-4">
              <div className="flex items-center space-x-4">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Duration:
                </label>
                <select
                  value={recordingDuration}
                  onChange={(e) => setRecordingDuration(parseInt(e.target.value))}
                  disabled={isProcessing || isRecording}
                  className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                >
                  <option value={5}>5 seconds</option>
                  <option value={10}>10 seconds</option>
                  <option value={15}>15 seconds</option>
                  <option value={30}>30 seconds</option>
                  <option value={60}>60 seconds</option>
                </select>
              </div>

              <button
                className={`btn-primary flex items-center ${isRecording ? 'bg-red-600 hover:bg-red-700' : ''}`}
                onClick={handleMicrophoneRecord}
                disabled={isProcessing && !isRecording}
              >
                {isRecording ? (
                  <>
                    <Square className="h-4 w-4 mr-2" />
                    Stop Recording
                  </>
                ) : (
                  <>
                    <Mic className="h-4 w-4 mr-2" />
                    Record Audio
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Processing Indicator */}
          {(isProcessing || isRecording) && (
            <div className="mt-6 flex items-center justify-center text-primary-600">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600 mr-2"></div>
              <span>
                {isRecording ? `Recording... (${recordingDuration}s)` : 'Processing...'}
              </span>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mt-6 flex items-center justify-center text-red-500">
              <AlertCircle className="h-4 w-4 mr-2" />
              <span>{error}</span>
            </div>
          )}

          {/* Results */}
          {transcription && (
            <div className="mt-6 space-y-4">
              <h3 className="text-lg font-semibold mb-2">Transcription Results</h3>
              
              {/* Main Transcription */}
              <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-left">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium">Transcribed Text</h4>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => copyToClipboard(transcription, 'Transcription')}
                      className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                      title="Copy transcription"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                    <button
                      onClick={handleSummarize}
                      disabled={isSummarizing}
                      className="btn-secondary flex items-center text-sm"
                    >
                      <FileText className="h-4 w-4 mr-2" />
                      {isSummarizing ? 'Generating...' : 'Generate Summary'}
                    </button>
                  </div>
                </div>
                <p className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
                  {transcription}
                </p>
              </div>

              {/* Summary */}
              {summary && (
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg text-left border border-blue-200 dark:border-blue-800">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium text-blue-900 dark:text-blue-100">Summary</h4>
                    <button
                      onClick={() => copyToClipboard(summary, 'Summary')}
                      className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                      title="Copy summary"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                  <p className="text-blue-800 dark:text-blue-200 whitespace-pre-wrap">
                    {summary}
                  </p>
                </div>
              )}
              
              {/* Statistics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
                  <h4 className="font-medium mb-1">Confidence</h4>
                  <p className="text-lg">{confidence ? (confidence * 100).toFixed(1) : '95.0'}%</p>
                </div>
                <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
                  <h4 className="font-medium mb-1">Duration</h4>
                  <p className="text-lg">{duration?.toFixed(2) || '0.00'}s</p>
                </div>
                <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
                  <h4 className="font-medium mb-1">Word Count</h4>
                  <p className="text-lg">{wordCount || 0} words</p>
                </div>
              </div>

              {/* Word Timestamps */}
              {timestamps && timestamps.length > 0 && (
                <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Word Timestamps</h4>
                  <div className="max-h-40 overflow-y-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="text-left">
                          <th className="pb-2 font-medium">Word</th>
                          <th className="pb-2 font-medium">Start</th>
                          <th className="pb-2 font-medium">End</th>
                        </tr>
                      </thead>
                      <tbody>
                        {timestamps.map((item, index) => (
                          <tr key={index} className="border-t border-gray-200 dark:border-gray-700">
                            <td className="py-2">{item.word}</td>
                            <td className="py-2">{item.start_time?.toFixed(2) || '0.00'}s</td>
                            <td className="py-2">{item.end_time?.toFixed(2) || '0.00'}s</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div className="card">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">How to Use</h3>
          <div className="space-y-3 text-gray-600 dark:text-gray-400">
            <div className="flex items-start space-x-3">
              <Upload className="h-5 w-5 text-primary-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">Upload Audio File</p>
                <p>Select an audio file from your device. Supported formats: {supportedFormats.join(', ')}</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <Mic className="h-5 w-5 text-primary-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">Record Audio</p>
                <p>Use your microphone to record audio directly. Choose duration from 5-60 seconds.</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <FileText className="h-5 w-5 text-primary-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">Generate Summary</p>
                <p>After transcription, click "Generate Summary" to get a concise summary of the content.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Voice;