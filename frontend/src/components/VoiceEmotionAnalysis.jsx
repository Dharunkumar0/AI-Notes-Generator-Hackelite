import React, { useState, useRef } from 'react';
import { Mic, StopCircle, Upload, AlertCircle } from 'lucide-react';
import { voiceService } from '../services/voiceService';

const VoiceEmotionAnalysis = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  // Start recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' });
        setAudioBlob(audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setError(null);
    } catch (err) {
      setError('Error accessing microphone. Please ensure microphone permissions are granted.');
      console.error('Error starting recording:', err);
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop all tracks
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  // Process the recording
  const processRecording = async () => {
    if (!audioBlob) {
      setError('No recording to analyze');
      return;
    }

    try {
      setIsProcessing(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.wav');

      const result = await voiceService.analyzeEmotion(formData);
      setResult(result);
    } catch (err) {
      setError(err.message || 'Error analyzing voice');
      console.error('Error processing recording:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  // Render emotion scores as a list of progress bars
  const renderEmotionScores = (scores) => {
    return Object.entries(scores).map(([key, value]) => (
      <div key={key} className="mb-2">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm capitalize">{key.replace('_', ' ')}</span>
          <span className="text-sm font-semibold">{value}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-primary-600 h-2 rounded-full"
            style={{ width: `${value}%` }}
          />
        </div>
      </div>
    ));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Voice Emotion Analysis
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Record your voice to analyze your emotional state and get personalized suggestions
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-400 mr-3" />
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        </div>
      )}

      {/* Recording Controls */}
      <div className="card">
        <div className="p-6">
          <div className="flex flex-col items-center justify-center space-y-4">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`btn-circle ${isRecording ? 'btn-error' : 'btn-primary'}`}
              disabled={isProcessing}
            >
              {isRecording ? (
                <StopCircle className="h-6 w-6" />
              ) : (
                <Mic className="h-6 w-6" />
              )}
            </button>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {isRecording ? 'Click to stop recording' : 'Click to start recording'}
            </span>
            
            {audioBlob && !isRecording && (
              <button
                onClick={processRecording}
                disabled={isProcessing}
                className="btn-primary flex items-center"
              >
                {isProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Analyze Recording
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="card">
          <div className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Analysis Results
            </h2>
            
            {/* Primary Emotion */}
            <div className="mb-6">
              <div className="flex items-center justify-between">
                <h3 className="text-md font-medium text-gray-700 dark:text-gray-300">
                  Detected Emotion
                </h3>
                <span className="px-3 py-1 bg-primary-100 dark:bg-primary-900/20 text-primary-800 dark:text-primary-200 rounded-full text-sm font-medium">
                  {result.primary_emotion}
                </span>
              </div>
            </div>
            
            {/* Emotion Scores */}
            <div className="mb-6">
              <h3 className="text-md font-medium text-gray-700 dark:text-gray-300 mb-3">
                Emotional State Analysis
              </h3>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                {renderEmotionScores(result.emotion_scores)}
              </div>
            </div>
            
            {/* Context and Suggestions */}
            <div className="space-y-4">
              <div>
                <h3 className="text-md font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Context
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {result.context}
                </p>
              </div>
              
              <div>
                <h3 className="text-md font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Suggestions
                </h3>
                <ul className="list-disc list-inside space-y-2">
                  {result.suggestions.map((suggestion, index) => (
                    <li key={index} className="text-gray-600 dark:text-gray-400">
                      {suggestion}
                    </li>
                  ))}
                </ul>
              </div>
              
              {result.additional_notes && (
                <div>
                  <h3 className="text-md font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Additional Notes
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    {result.additional_notes}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VoiceEmotionAnalysis;
