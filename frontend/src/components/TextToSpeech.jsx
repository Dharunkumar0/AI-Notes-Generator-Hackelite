import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, RefreshCw, Globe } from 'lucide-react';
import { textToSpeechService } from '../services/textToSpeechService';

const TextToSpeech = ({ text }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const audioRef = useRef(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [language, setLanguage] = useState('en');
  const [translatedText, setTranslatedText] = useState(null);
  
  const languages = [
    { code: 'en', name: 'English' },
    { code: 'ta', name: 'Tamil' }
  ];

  const generateSpeech = async () => {
    try {
      setIsLoading(true);
      setError(null);
      setTranslatedText(null);

      console.log('Generating speech:', {
        text,
        language,
        translate: language !== 'en'
      });

      const data = await textToSpeechService.generateSpeech(
        text,
        language,
        language !== 'en' // translate if not English
      );
      
      const baseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
      setAudioUrl(`${baseUrl}${data.file_path}`);
      
      if (data.translated_text && language !== 'en') {
        setTranslatedText(data.translated_text);
      }
      
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

  const togglePlayPause = async () => {
    if (audioRef.current) {
      try {
        if (isPlaying) {
          audioRef.current.pause();
          setIsPlaying(false);
        } else {
          await audioRef.current.play();
          setIsPlaying(true);
        }
      } catch (err) {
        console.error('Playback error:', err);
        setError('Error playing audio. Please try again.');
        setIsPlaying(false);
      }
    }
  };

  useEffect(() => {
    if (audioUrl && audioRef.current) {
      setIsPlaying(false);
      setError(null);
      audioRef.current.load();
      try {
        const playPromise = audioRef.current.play();
        if (playPromise !== undefined) {
          playPromise.catch(error => {
            console.error('Audio playback failed:', error);
            setError('Click play to start audio');
          });
        }
      } catch (err) {
        console.error('Play error:', err);
        setError('Click play to start audio');
      }
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
    <div className="flex flex-col space-y-2">
      <div className="flex items-center space-x-2">
        <audio
          ref={audioRef}
          src={audioUrl || ''}
          style={{ display: 'none' }}
          onEnded={() => setIsPlaying(false)}
          onError={() => {
            console.error('Audio failed to load');
            setError('Click play to start audio');
            setIsPlaying(false);
          }}
        />
        
        <select
          value={language}
          onChange={(e) => {
            setLanguage(e.target.value);
            setAudioUrl(null);
            setTranslatedText(null);
          }}
          className="select select-bordered select-sm"
        >
          {languages.map(lang => (
            <option key={lang.code} value={lang.code}>
              {lang.name}
            </option>
          ))}
        </select>
        
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
      </div>

      {translatedText && language !== 'en' && (
        <div className="text-sm text-gray-600 bg-gray-100 p-2 rounded">
          <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
            <Globe className="h-3 w-3" />
            <span>Translated Text:</span>
          </div>
          {translatedText}
        </div>
      )}

      {error && (
        <div className="text-red-500 text-sm">
          {error}
          {audioUrl && (
            <>
              <br />
              <span>If the audio does not play, <a href={audioUrl} target="_blank" rel="noopener noreferrer" className="underline">click here to test the audio file directly</a>.</span>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default TextToSpeech;