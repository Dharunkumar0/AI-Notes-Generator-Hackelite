import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, RefreshCw } from 'lucide-react';
import { textToSpeechService } from '../services/textToSpeechService';

const TextToSpeech = ({ text }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const audioRef = useRef(null);
  const [audioUrl, setAudioUrl] = useState(null);

  const generateSpeech = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await textToSpeechService.generateSpeech(text);
      const baseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
      setAudioUrl(`${baseUrl}${data.file_path}`);
      
      // Load and play the audio
      if (audioRef.current) {
        await audioRef.current.load();
      }
    } catch (err) {
      setError(err.message);
      console.error('Error generating speech:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const togglePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  useEffect(() => {
    if (audioRef.current) {
      // Handle audio end
      audioRef.current.onended = () => setIsPlaying(false);
      
      // Handle errors
      audioRef.current.onerror = (e) => {
        setError('Error playing audio');
        setIsPlaying(false);
      };
    }
  }, [audioUrl]);

  const regenerateSpeech = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
    generateSpeech();
  };

  return (
    <div className="flex items-center space-x-2">
      {audioUrl && (
        <audio ref={audioRef} src={audioUrl} />
      )}
      
      <button
        onClick={audioUrl ? togglePlayPause : generateSpeech}
        disabled={isLoading}
        className="btn-primary flex items-center space-x-2"
        title={audioUrl ? (isPlaying ? "Pause" : "Play") : "Generate Speech"}
      >
        {isLoading ? (
          <div className="animate-spin">
            <RefreshCw className="h-4 w-4" />
          </div>
        ) : (
          isPlaying ? (
            <Pause className="h-4 w-4" />
          ) : (
            <Play className="h-4 w-4" />
          )
        )}
        <span>{isLoading ? "Generating..." : (audioUrl ? (isPlaying ? "Pause" : "Play") : "Read Aloud")}</span>
      </button>

      {audioUrl && (
        <button
          onClick={regenerateSpeech}
          disabled={isLoading}
          className="btn-secondary p-2"
          title="Regenerate Speech"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      )}

      {error && (
        <p className="text-red-500 text-sm">{error}</p>
      )}
    </div>
  );
};

export default TextToSpeech;
