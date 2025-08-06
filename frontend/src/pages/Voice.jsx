import React, { useState, useRef, useEffect } from 'react';
import { Mic, Upload, Play, StopCircle, Loader } from 'lucide-react';
import { voiceService } from '../services/voiceService';

const Voice = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [error, setError] = useState('');
  const [supportedFormats, setSupportedFormats] = useState([]);
  const fileInputRef = useRef();

  useEffect(() => {
    // Get supported formats when component mounts
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

    try {
      setIsProcessing(true);
      setError('');
      const result = await voiceService.transcribeAudioFile(file);
      setTranscription(result.transcription);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to transcribe audio file');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRecord = async () => {
    if (isRecording) {
      setIsRecording(false);
      try {
        setIsProcessing(true);
        setError('');
        const result = await voiceService.transcribeMicrophone(10); // 10 seconds recording
        setTranscription(result.transcription);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to transcribe voice');
      } finally {
        setIsProcessing(false);
      }
    } else {
      setIsRecording(true);
      setTranscription('');
      setError('');
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
              <h3 className="text-lg font-semibold mb-2">Transcription</h3>
              <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-left">
                {transcription}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Voice; 