import React, { useState } from 'react';
import { voiceService } from '../services/voiceService';
import DownloadPdfButton from './DownloadPdfButton';

const TamilVoiceRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [tamilText, setTamilText] = useState('');
  const [englishTranslation, setEnglishTranslation] = useState('');
  const [error, setError] = useState(null);

  const handleStartRecording = async () => {
    try {
      setIsRecording(true);
      setError(null);
      const result = await voiceService.recordTamilVoice();
      setTamilText(result.tamilText);
      setEnglishTranslation(result.englishTranslation);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsRecording(false);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Tamil Voice Recognition</h2>
      <div className="flex flex-col space-y-4">
        <button
          onClick={handleStartRecording}
          disabled={isRecording}
          className={`px-4 py-2 rounded ${
            isRecording
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          }`}
        >
          {isRecording ? 'Recording...' : 'Start Recording'}
        </button>

        {error && (
          <div className="text-red-500 bg-red-100 p-3 rounded">
            Error: {error}
          </div>
        )}

        {tamilText && (
          <div className="bg-gray-100 p-4 rounded">
            <h3 className="font-bold mb-2">Tamil Text:</h3>
            <p>{tamilText}</p>
          </div>
        )}

        {englishTranslation && (
          <div className="bg-gray-100 p-4 rounded">
            <h3 className="font-bold mb-2">English Translation:</h3>
            <p>{englishTranslation}</p>
          </div>
        )}

        {(tamilText || englishTranslation) && (
          <div className="mt-4">
            <DownloadPdfButton
              content={{
                tamilText,
                englishTranslation
              }}
              filename="tamil-voice-recognition"
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default TamilVoiceRecorder;
