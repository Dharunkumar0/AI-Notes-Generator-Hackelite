import React, { useState } from 'react';
import { FileText, Copy, Download, Sparkles, Target, Clock } from 'lucide-react';
import { notesService } from '../services/notesService';
import toast from 'react-hot-toast';

const Notes = () => {
  const [text, setText] = useState('');
  const [maxLength, setMaxLength] = useState(500);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [summarizationType, setSummarizationType] = useState('abstractive');
  const [summaryMode, setSummaryMode] = useState('narrative');
  const [useBlooms, setUseBlooms] = useState(false);

  const handleSummarize = async () => {
    if (!text.trim()) {
      toast.error('Please enter some text to summarize');
      return;
    }

    if (text.length > 10000) {
      toast.error('Text is too long. Maximum 10,000 characters allowed.');
      return;
    }

    try {
      setLoading(true);
      const response = await notesService.summarize(text, maxLength, summarizationType, summaryMode, useBlooms);
      setResult(response);
      toast.success('Text summarized successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to summarize text');
    } finally {
      setLoading(false);
    }
  };

  const handleExtractKeyPoints = async () => {
    if (!text.trim()) {
      toast.error('Please enter some text to extract key points');
      return;
    }

    try {
      setLoading(true);
      const response = await notesService.extractKeyPoints(text);
      setResult({
        summary: 'Key points extracted successfully',
        key_points: response.key_points,
        word_count: text.split(' ').length,
        processing_time: 0
      });
      toast.success('Key points extracted successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to extract key points');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const downloadAsText = (content, filename) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('Downloaded successfully!');
  };

  const clearAll = () => {
    setText('');
    setResult(null);
    setMaxLength(500);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Notes Summarizer</h1>
          <p className="text-gray-600 dark:text-gray-400">Transform long text into concise summaries with AI</p>
        </div>
        <div className="flex items-center space-x-2">
          <FileText className="h-8 w-8 text-primary-600" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="space-y-4">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Input Text</h2>
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="maxLength" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Maximum Summary Length (words)
                  </label>
                  <input
                    type="number"
                    id="maxLength"
                    min="100"
                    max="1000"
                    value={maxLength}
                    onChange={(e) => setMaxLength(Number(e.target.value))}
                    className="input-field w-32"
                  />
                </div>
                <div>
                  <label htmlFor="summarizationType" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Summarization Method
                  </label>
                  <select
                    id="summarizationType"
                    value={summarizationType}
                    onChange={(e) => setSummarizationType(e.target.value)}
                    className="input-field w-full"
                  >
                    <option value="abstractive">Abstractive (New Sentences)</option>
                    <option value="extractive">Extractive (Original Sentences)</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label htmlFor="summaryMode" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Summary Style
                  </label>
                  <select
                    id="summaryMode"
                    value={summaryMode}
                    onChange={(e) => setSummaryMode(e.target.value)}
                    className="input-field w-full"
                  >
                    <option value="narrative">Narrative (Flowing Story-like)</option>
                    <option value="beginner">Beginner-Friendly (Simple Language)</option>
                    <option value="technical">Technical/Expert (Advanced Terms)</option>
                    <option value="bullet">Bullet Points (Concise List)</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={useBlooms}
                      onChange={(e) => setUseBlooms(e.target.checked)}
                      className="form-checkbox h-4 w-4 text-primary-600"
                    />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Use Bloom's Taxonomy for deeper learning analysis
                    </span>
                  </label>
                  {useBlooms && (
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                      This will analyze the content across different cognitive levels (Remember, Understand, Apply, Analyze, Evaluate, Create)
                    </p>
                  )}
                </div>
              </div>

              <div>
                <label htmlFor="text" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Text to Summarize
                </label>
                <textarea
                  id="text"
                  rows={12}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Paste your long text here..."
                  className="textarea-field"
                />
                <div className="mt-2 flex justify-between text-sm text-gray-500 dark:text-gray-400">
                  <span>{text.length} characters</span>
                  <span>{text.split(' ').filter(word => word.length > 0).length} words</span>
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={handleSummarize}
                  disabled={loading || !text.trim()}
                  className="btn-primary flex items-center"
                >
                  {loading ? (
                    <div className="loading-spinner mr-2"></div>
                  ) : (
                    <Sparkles className="h-4 w-4 mr-2" />
                  )}
                  Summarize
                </button>
                <button
                  onClick={handleExtractKeyPoints}
                  disabled={loading || !text.trim()}
                  className="btn-secondary flex items-center"
                >
                  <Target className="h-4 w-4 mr-2" />
                  Extract Key Points
                </button>
                <button
                  onClick={clearAll}
                  className="btn-error"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Output Section */}
        <div className="space-y-4">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Results</h2>
            
            {result ? (
              <div className="space-y-6">
                {/* Summary */}
                <div>
                  <h3 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-2">Summary</h3>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{result.summary}</p>
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                      <Clock className="h-4 w-4 mr-1" />
                      {result.processing_time.toFixed(2)}s
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => copyToClipboard(result.summary)}
                        className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                        title="Copy to clipboard"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => {
                          const content = `Summary\n${result.summary}\n\n${
                            result.key_points?.length
                              ? `Key Points:\n${result.key_points.map(p => `• ${p}`).join('\n')}`
                              : ''
                          }`;
                          downloadAsText(content, 'notes-summary.txt');
                        }}
                        className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                        title="Download as text"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Key Points */}
                {result.key_points && result.key_points.length > 0 && (
                  <div>
                    <h3 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-2">Key Points</h3>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <ul className="space-y-2">
                        {result.key_points.map((point, index) => (
                          <li key={index} className="flex items-start">
                            <span className="flex-shrink-0 w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3"></span>
                            <span className="text-gray-700 dark:text-gray-300">{point}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="mt-2 flex justify-end">
                      <button
                        onClick={() => copyToClipboard(result.key_points.join('\n• '))}
                        className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Stats */}
                <div className="bg-primary-50 dark:bg-primary-900/20 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500 dark:text-gray-400">Original Words</p>
                      <p className="font-semibold text-gray-900 dark:text-gray-100">{text.split(' ').filter(word => word.length > 0).length}</p>
                    </div>
                    <div>
                      <p className="text-gray-500 dark:text-gray-400">Summary Words</p>
                      <p className="font-semibold text-gray-900 dark:text-gray-100">{result.word_count}</p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">Enter text and click summarize to see results</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Notes; 