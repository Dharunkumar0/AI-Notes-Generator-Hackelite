import React, { useState, useRef } from 'react';
import { FaMicrophone, FaStop, FaPause, FaTrash, FaPlay, FaSpinner } from 'react-icons/fa';
import { toast } from 'react-hot-toast';
import { voiceService } from '../services/voiceService';

const VoiceRecorder = ({ onTranscriptionComplete }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [duration, setDuration] = useState(0);
    const [audioBlob, setAudioBlob] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [audioURL, setAudioURL] = useState(null);

    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const timerRef = useRef(null);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    channelCount: 1,
                    sampleRate: 44100,
                    sampleSize: 16,
                    volume: 1.0,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            const options = { 
                mimeType: 'audio/webm',
                audioBitsPerSecond: 128000 // 128 kbps for better quality
            };
            mediaRecorderRef.current = new MediaRecorder(stream, options);
            audioChunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorderRef.current.onstop = () => {
                // Create WebM blob with proper MIME type
                const audioBlob = new Blob(audioChunksRef.current, { 
                    type: 'audio/webm' 
                });
                setAudioBlob(audioBlob);
                const url = URL.createObjectURL(audioBlob);
                setAudioURL(url);
            };

            // Start recording with smaller timeslices for more frequent updates
            mediaRecorderRef.current.start(100);
            setIsRecording(true);
            setIsPaused(false);

            timerRef.current = setInterval(() => {
                setDuration(prev => prev + 1);
            }, 1000);
        } catch (error) {
            console.error('Error accessing microphone:', error);
            toast.error('Could not access microphone. Please check permissions.');
        }
    };

    const pauseRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            if (!isPaused) {
                mediaRecorderRef.current.pause();
                clearInterval(timerRef.current);
            } else {
                mediaRecorderRef.current.resume();
                timerRef.current = setInterval(() => {
                    setDuration(prev => prev + 1);
                }, 1000);
            }
            setIsPaused(!isPaused);
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            clearInterval(timerRef.current);
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
            setIsRecording(false);
            setIsPaused(false);
        }
    };

    const resetRecording = () => {
        if (audioURL) {
            URL.revokeObjectURL(audioURL);
        }
        setAudioBlob(null);
        setAudioURL(null);
        setDuration(0);
    };

    const handleSubmit = async () => {
        if (!audioBlob) {
            toast.error('Please record audio first');
            return;
        }

        setIsProcessing(true);
        try {
            // Create a File object from the Blob with a unique filename
            const timestamp = Date.now();
            const audioFile = new File([audioBlob], `recording_${timestamp}.webm`, { 
                type: 'audio/webm',
                lastModified: timestamp
            });
            
            // Use voiceService to transcribe
            const result = await voiceService.transcribeAudioFile(audioFile);
            onTranscriptionComplete(result);
            resetRecording();
            toast.success('Audio transcribed successfully');
        } catch (error) {
            console.error('Error transcribing audio:', error);
            toast.error(error.message || 'Error transcribing audio');
        } finally {
            setIsProcessing(false);
        }
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="flex flex-col items-center space-y-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="flex items-center space-x-4">
                {!isRecording && !audioBlob && (
                    <button
                        onClick={startRecording}
                        className="p-4 bg-blue-500 text-white rounded-full hover:bg-blue-600 transition-colors"
                        title="Start Recording"
                    >
                        <FaMicrophone className="w-6 h-6" />
                    </button>
                )}

                {isRecording && (
                    <>
                        <button
                            onClick={pauseRecording}
                            className="p-4 bg-yellow-500 text-white rounded-full hover:bg-yellow-600 transition-colors"
                            title={isPaused ? "Resume Recording" : "Pause Recording"}
                        >
                            {isPaused ? <FaPlay className="w-6 h-6" /> : <FaPause className="w-6 h-6" />}
                        </button>
                        <button
                            onClick={stopRecording}
                            className="p-4 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
                            title="Stop Recording"
                        >
                            <FaStop className="w-6 h-6" />
                        </button>
                    </>
                )}

                {audioBlob && !isRecording && (
                    <>
                        <audio src={audioURL} controls className="w-64" />
                        <button
                            onClick={resetRecording}
                            className="p-4 bg-gray-500 text-white rounded-full hover:bg-gray-600 transition-colors"
                            title="Reset Recording"
                        >
                            <FaTrash className="w-6 h-6" />
                        </button>
                    </>
                )}
            </div>

            <div className="text-center text-gray-600 dark:text-gray-300">
                {formatTime(duration)}
            </div>

            {audioBlob && !isRecording && (
                <button
                    onClick={handleSubmit}
                    disabled={isProcessing}
                    className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:bg-gray-400 flex items-center space-x-2"
                >
                    {isProcessing ? (
                        <>
                            <FaSpinner className="w-5 h-5 animate-spin" />
                            <span>Processing...</span>
                        </>
                    ) : (
                        <span>Transcribe Audio</span>
                    )}
                </button>
            )}
        </div>
    );
};

export default VoiceRecorder;
