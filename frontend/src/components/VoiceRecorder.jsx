import React, { useState, useRef, useEffect } from 'react';
import { FaMicrophone, FaStop, FaPause, FaTrash, FaPlay, FaSpinner, FaUpload } from 'react-icons/fa';
import { toast } from 'react-hot-toast';
import { voiceService } from '../services/voiceService';

const VoiceRecorder = ({ onTranscriptionComplete }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [duration, setDuration] = useState(0);
    const [audioBlob, setAudioBlob] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [audioURL, setAudioURL] = useState(null);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [availableMicrophones, setAvailableMicrophones] = useState([]);
    const [selectedMicrophone, setSelectedMicrophone] = useState(null);
    const [isLoadingMics, setIsLoadingMics] = useState(false);

    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const timerRef = useRef(null);
    const fileInputRef = useRef(null);

    const supportedFormats = ['wav', 'mp3', 'm4a', 'ogg', 'flac', 'webm'];

    useEffect(() => {
        fetchAvailableMicrophones();
    }, []);

    const fetchAvailableMicrophones = async () => {
        try {
            setIsLoadingMics(true);
            const response = await voiceService.getAvailableMicrophones();
            if (response && Array.isArray(response)) {
                setAvailableMicrophones(response);
                if (response.length > 0) {
                    setSelectedMicrophone(response[0]);
                }
            }
        } catch (error) {
            console.error('Error fetching microphones:', error);
            toast.error('Could not fetch available microphones');
        } finally {
            setIsLoadingMics(false);
        }
    };

    const startRecording = async () => {
        try {
            if (!selectedMicrophone) {
                toast.error('Please select a microphone first');
                return;
            }

            const response = await voiceService.startRecording(selectedMicrophone.index);
            if (response.success && response.audioPath) {
                setAudioURL(response.audioPath);
                setIsRecording(true);
                setIsPaused(false);

                timerRef.current = setInterval(() => {
                    setDuration(prev => prev + 1);
                }, 1000);
            } else {
                throw new Error(response.error || 'Failed to start recording');
            }
        } catch (error) {
            console.error('Error starting recording:', error);
            toast.error(error.message || 'Could not start recording. Please try again.');
        }
    };

    const pauseRecording = () => {
        if (!mediaRecorderRef.current || !isRecording) return;

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
    };

    const stopRecording = () => {
        if (!mediaRecorderRef.current || !isRecording) return;

        mediaRecorderRef.current.stop();
        clearInterval(timerRef.current);
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
        setIsRecording(false);
        setIsPaused(false);
    };

    const resetRecording = () => {
        if (audioURL) {
            URL.revokeObjectURL(audioURL);
        }
        setAudioBlob(null);
        setAudioURL(null);
        setDuration(0);
        setUploadProgress(0);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const handleFileUpload = async (event) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const format = file.name.split('.').pop()?.toLowerCase();
        if (!supportedFormats.includes(format)) {
            toast.error(`Unsupported file format. Supported formats: ${supportedFormats.join(', ')}`);
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            toast.error('File size must be less than 10MB');
            return;
        }

        try {
            setIsProcessing(true);
            const formData = new FormData();
            formData.append('file', file);

            const result = await voiceService.uploadAudio(formData, progress => {
                setUploadProgress(Math.round(progress));
            });

            if (result?.transcription) {
                onTranscriptionComplete(result);
                toast.success('Audio processed successfully');
            } else {
                toast.error('Failed to process audio');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            toast.error(error.message || 'Failed to process audio file');
        } finally {
            setIsProcessing(false);
            setUploadProgress(0);
        }
    };

    const handleSubmit = async () => {
        if (!audioBlob) {
            toast.error('Please record audio first');
            return;
        }

        setIsProcessing(true);
        try {
            const timestamp = Date.now();
            const audioFile = new File([audioBlob], `recording_${timestamp}.webm`, {
                type: 'audio/webm',
                lastModified: timestamp
            });

            const result = await voiceService.transcribeAudioFile(audioFile);
            if (result?.transcription) {
                onTranscriptionComplete(result);
                resetRecording();
                toast.success('Audio transcribed successfully');
            } else {
                toast.error('Failed to transcribe audio');
            }
        } catch (error) {
            console.error('Error transcribing audio:', error);
            toast.error(error.message || 'Error transcribing audio');
        } finally {
            setIsProcessing(false);
        }
    };

    const formatTime = seconds => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="flex flex-col items-center space-y-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
            {/* Microphone selector */}
            <div className="w-full max-w-sm">
                <label htmlFor="microphone-select" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Select Microphone
                </label>
                <div className="relative">
                    <select
                        id="microphone-select"
                        value={selectedMicrophone?.index ?? ''}
                        onChange={(e) => {
                            const mic = availableMicrophones.find(m => m.index === parseInt(e.target.value));
                            setSelectedMicrophone(mic || null);
                        }}
                        disabled={isLoadingMics || isRecording}
                        className="block w-full rounded-lg border border-gray-300 bg-white dark:bg-gray-700 px-4 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">Select a microphone...</option>
                        {availableMicrophones.map(mic => (
                            <option key={mic.index} value={mic.index}>
                                {mic.name}
                            </option>
                        ))}
                    </select>
                    {isLoadingMics && (
                        <div className="absolute right-2 top-1/2 transform -translate-y-1/2">
                            <FaSpinner className="w-4 h-4 animate-spin text-gray-400" />
                        </div>
                    )}
                </div>
            </div>
            
            <div className="flex items-center space-x-4">
                {!isRecording && !audioBlob && (
                    <>
                        <button
                            onClick={startRecording}
                            disabled={isProcessing || !selectedMicrophone}
                            className="p-4 bg-blue-500 text-white rounded-full hover:bg-blue-600 transition-colors disabled:bg-blue-400"
                            title={!selectedMicrophone ? "Select a microphone first" : "Start Recording"}
                        >
                            <FaMicrophone className="w-6 h-6" />
                        </button>
                        
                        <div className="relative">
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileUpload}
                                accept=".wav,.mp3,.m4a,.ogg,.flac,.webm"
                                className="hidden"
                                disabled={isProcessing}
                            />
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                disabled={isProcessing}
                                className="p-4 bg-green-500 text-white rounded-full hover:bg-green-600 transition-colors disabled:bg-green-400"
                                title="Upload Audio File"
                            >
                                <FaUpload className="w-6 h-6" />
                            </button>
                        </div>
                    </>
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
                    <div className="flex items-center space-x-4">
                        <audio src={audioURL} controls className="w-64" />
                        <button
                            onClick={handleSubmit}
                            disabled={isProcessing}
                            className="p-4 bg-green-500 text-white rounded-full hover:bg-green-600 transition-colors disabled:bg-green-400"
                            title="Transcribe Audio"
                        >
                            {isProcessing ? (
                                <FaSpinner className="w-6 h-6 animate-spin" />
                            ) : (
                                <FaPlay className="w-6 h-6" />
                            )}
                        </button>
                        <button
                            onClick={resetRecording}
                            disabled={isProcessing}
                            className="p-4 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors disabled:bg-red-400"
                            title="Reset Recording"
                        >
                            <FaTrash className="w-6 h-6" />
                        </button>
                    </div>
                )}
            </div>

            {isRecording && (
                <div className="text-center text-gray-600 dark:text-gray-300">
                    {isPaused ? 'Paused' : 'Recording'} ({formatTime(duration)})
                </div>
            )}

            {isProcessing && uploadProgress > 0 && uploadProgress < 100 && (
                <div className="w-full max-w-md">
                    <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div 
                            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${uploadProgress}%` }}
                        />
                    </div>
                    <div className="text-center text-sm text-gray-600 dark:text-gray-300 mt-1">
                        Uploading: {uploadProgress}%
                    </div>
                </div>
            )}

            {isProcessing && (
                <div className="text-center text-gray-600 dark:text-gray-300">
                    Processing audio...
                </div>
            )}
        </div>
    );
};

export default VoiceRecorder;
