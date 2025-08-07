import React, { useState, useRef, useEffect } from 'react';
import { Mic, Upload, Play, StopCircle, Loader, FileText } from 'lucide-react';
import { voiceService } from '../services/voiceService';
import { notesService } from '../services/notesService';

const Voice = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [confidence, setConfidence] = useState(null);
  const [duration, setDuration] = useState(null);
  const [word_count, setWordCount] = useState(null);
  const [timestamps, setTimestamps] = useState([]);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState('');
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [supportedFormats, setSupportedFormats] = useState([]);
  const fileInputRef = useRef();

  useEffect(() => {
    // Fetch supported formats when component mounts
    const getFormats = async () => {
      try {
        const { data } = await voiceService.getSupportedFormats();
        setSupportedFormats(data.supported_formats);
      } catch (err) {
        console.error('Failed to get supported formats:', err);
      }
    };
    getFormats();
  }, []);

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    setError('');
    setTranscription('');
    setConfidence(null);
    setDuration(null);
    setWordCount(null);
    setTimestamps([]);
    setSummary('');

    try {
      // Reduce max file size to 5MB to prevent timeouts
      if (file.size > 5 * 1024 * 1024) {
        throw new Error('File size exceeds 5MB limit. For better performance, please select a smaller file or try a shorter audio clip.');
      }

      // Validate file type
      const fileType = file.type.toLowerCase();
      if (!fileType.includes('audio/')) {
        throw new Error('Please select a valid audio file.');
      }

      // Show specific message for processing
      setError('Processing audio file. This may take a few moments for longer files...');
      const result = await voiceService.transcribeAudioFile(file);

      if (result.transcription) {
        setTranscription(result.transcription);
        setConfidence(result.confidence || null);
        setDuration(result.duration || null);
        setWordCount(result.word_count || null);
        setTimestamps(result.timestamps || []);
      } else {
        throw new Error('No transcription received from server');
      }

    } catch (err) {
      const errorMessage = err.message || err.response?.data?.detail || 'Failed to transcribe audio file';
      setError(errorMessage);
      console.error('Upload error:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSummarize = async () => {
    if (!transcription) return;
    
    try {
      setIsSummarizing(true);
      setError('');
      setSummary('');
      const result = await notesService.summarize(transcription);
      if (result.summary) {
        setSummary(result.summary);
      } else {
        throw new Error('No summary received');
      }
    } catch (err) {
      const errorMessage = err.message || err.response?.data?.detail || 'Failed to generate summary';
      setError(errorMessage);
      console.error('Summary error:', err);
    } finally {
      setIsSummarizing(false);
    }
  };

  const handleRecord = async () => {
    if (isRecording) {
      setIsRecording(false);
      try {
        setIsProcessing(true);
        setError('');
        const result = await voiceService.transcribeMicrophone(10); // 10-second recording
        if (result.transcription) {
          setTranscription(result.transcription);
        } else {
          throw new Error('No transcription received from microphone');
        }
      } catch (err) {
        const errorMessage = err.message || err.response?.data?.detail || 'Failed to transcribe voice';
        setError(errorMessage);
        console.error('Microphone error:', err);
      } finally {
        setIsProcessing(false);
      }
    } else {
      setIsRecording(true);
      setTranscription('');
      setError('');
      setConfidence(null);
      setDuration(null);
      setWordCount(null);
      setTimestamps([]);
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

          <div className="flex justify-center space-x-4">
            <input
              type="file"
              ref={fileInputRef}
              accept={supportedFormats.map(format => `.${format}`).join(',')}
              className="hidden"
              onChange={handleFileUpload}
            />
            <button
              className="btn-primary flex items-center"
              onClick={() => fileInputRef.current?.click()}
              disabled={isProcessing || isRecording}
            >
              <Upload className="h-4 w-4 mr-2" />
              Upload Audio
            </button>
            <button
              className={`btn-secondary flex items-center ${isRecording ? 'bg-red-500 hover:bg-red-600' : ''}`}
              onClick={handleRecord}
              disabled={isProcessing}
            >
              {isRecording ? (
                <>
                  <StopCircle className="h-4 w-4 mr-2" />
                  Stop Recording
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Record Voice
                </>
              )}
            </button>
          </div>

          {(isProcessing || isRecording) && (
            <div className="mt-6 flex items-center justify-center text-primary-600">
              <Loader className="h-6 w-6 animate-spin mr-2" />
              <span>{isRecording ? 'Recording...' : 'Processing...'}</span>
            </div>
          )}

          {error && (
            <div className="mt-6 text-red-500">
              {error}
            </div>
          )}

          {transcription && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-2">Transcription Results</h3>
              <div className="space-y-4">
                <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-left">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium">Text</h4>
                    <button
                      onClick={handleSummarize}
                      disabled={isSummarizing}
                      className="btn-secondary flex items-center text-sm"
                    >
                      <FileText className="h-4 w-4 mr-2" />
                      {isSummarizing ? 'Generating...' : 'Generate Summary'}
                    </button>
                  </div>
                  {transcription}
                </div>

                {summary && (
                  <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-left">
                    <h4 className="font-medium mb-2">Summary</h4>
                    {summary}
                  </div>
                )}
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
                    <h4 className="font-medium mb-1">Confidence</h4>
                    <p>{(confidence * 100).toFixed(1)}%</p>
                  </div>
                  <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
                    <h4 className="font-medium mb-1">Duration</h4>
                    <p>{duration?.toFixed(2)}s</p>
                  </div>
                  <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
                    <h4 className="font-medium mb-1">Word Count</h4>
                    <p>{word_count} words</p>
                  </div>
                </div>

                {timestamps && timestamps.length > 0 && (
                  <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
                    <h4 className="font-medium mb-2">Word Timestamps</h4>
                    <div className="max-h-40 overflow-y-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="text-left">
                            <th className="pb-2">Word</th>
                            <th className="pb-2">Start</th>
                            <th className="pb-2">End</th>
                          </tr>
                        </thead>
                        <tbody>
                          {timestamps.map((item, index) => (
                            <tr key={index} className="border-t border-gray-200 dark:border-gray-700">
                              <td className="py-2">{item.word}</td>
                              <td className="py-2">{item.start_time.toFixed(2)}s</td>
                              <td className="py-2">{item.end_time.toFixed(2)}s</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Voice;
