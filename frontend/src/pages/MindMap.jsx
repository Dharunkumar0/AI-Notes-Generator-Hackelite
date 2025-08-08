import React, { useState } from 'react';
import { Brain, Network, Download, Loader, Plus, X, RefreshCw } from 'lucide-react';
import DownloadPdfButton from '../components/DownloadPdfButton';
import { mindmapService } from '../services/mindmapService';

const MindMap = () => {
  const [topic, setTopic] = useState('');
  const [subtopics, setSubtopics] = useState(['']);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [mindmap, setMindmap] = useState(null);

  const addSubtopic = () => {
    if (subtopics.length < 10) {
      setSubtopics([...subtopics, '']);
    }
  };

  const removeSubtopic = (index) => {
    const newSubtopics = subtopics.filter((_, i) => i !== index);
    setSubtopics(newSubtopics);
  };

  const updateSubtopic = (index, value) => {
    const newSubtopics = [...subtopics];
    newSubtopics[index] = value;
    setSubtopics(newSubtopics);
  };

  const generateMindMap = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic');
      return;
    }

    try {
      setIsGenerating(true);
      setError('');
      
      // Filter out empty subtopics
      const filteredSubtopics = subtopics.filter(st => st.trim());
      const result = await mindmapService.createMindMap(
        topic,
        filteredSubtopics.length > 0 ? filteredSubtopics : null
      );
      
      setMindmap(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create mind map');
    } finally {
      setIsGenerating(false);
    }
  };

  const resetMindMap = () => {
    setMindmap(null);
    setTopic('');
    setSubtopics(['']);
    setError('');
  };

  const exportMindMap = () => {
    if (!mindmap) return;

    // Create a text representation of the mind map
    let text = `# ${mindmap.topic}\n\n`;
    mindmap.branches.forEach(branch => {
      text += `## ${branch.name}\n`;
      branch.subtopics.forEach(subtopic => {
        text += `- ${subtopic.name}\n`;
        if (subtopic.details) {
          text += `  ${subtopic.details}\n`;
        }
      });
      text += '\n';
    });

    // Create and download the file
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mindmap-${topic.toLowerCase().replace(/\s+/g, '-')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Mind Map Creator</h1>
          <p className="text-gray-600 dark:text-gray-400">Create visual mind maps for complex topics</p>
        </div>
        <div className="flex items-center space-x-2">
          <Brain className="h-8 w-8 text-primary-600" />
        </div>
      </div>

      <div className="card">
        <div className="p-6">
          {!mindmap && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Main Topic
                </label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="Enter your main topic..."
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800"
                />
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Subtopics (Optional)
                  </label>
                  {subtopics.length < 10 && (
                    <button
                      onClick={addSubtopic}
                      className="text-primary-600 hover:text-primary-700 flex items-center text-sm"
                    >
                      <Plus className="h-4 w-4 mr-1" />
                      Add Subtopic
                    </button>
                  )}
                </div>
                {subtopics.map((subtopic, index) => (
                  <div key={index} className="flex space-x-2">
                    <input
                      type="text"
                      value={subtopic}
                      onChange={(e) => updateSubtopic(index, e.target.value)}
                      placeholder={`Subtopic ${index + 1}...`}
                      className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800"
                    />
                    {subtopics.length > 1 && (
                      <button
                        onClick={() => removeSubtopic(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="h-5 w-5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {error && (
                <div className="text-red-500 text-sm">
                  {error}
                </div>
              )}

              <button
                className="btn-primary w-full flex items-center justify-center"
                onClick={generateMindMap}
                disabled={isGenerating}
              >
                {isGenerating ? (
                  <>
                    <Loader className="h-4 w-4 mr-2 animate-spin" />
                    Generating Mind Map...
                  </>
                ) : (
                  <>
                    <Network className="h-4 w-4 mr-2" />
                    Create Mind Map
                  </>
                )}
              </button>
            </div>
          )}

          {mindmap && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold">{mindmap.topic}</h2>
                <div className="space-x-2">
                  <DownloadPdfButton
                    className="btn-secondary inline-flex items-center"
                    filename={`mindmap-${topic.toLowerCase().replace(/\s+/g, '-') || 'export'}.pdf`}
                    title={`Mind Map: ${mindmap.topic}`}
                    getHtml={() => `
                      <div class='section'>
                        <div class='meta'>Generated by AI Mind Map · ${new Date().toLocaleString()}</div>
                        <h1>${mindmap.topic.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</h1>
                        ${mindmap.branches.map(b => `
                          <div class='section'>
                            <h2>${b.name.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</h2>
                            <ul>
                              ${b.subtopics.map(st => `
                                <li>
                                  <strong>${st.name.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</strong>
                                  ${st.details ? `<div class='muted small'>${String(st.details).replace(/&/g, '&amp;').replace(/</g, '&lt;')}</div>` : ''}
                                </li>
                              `).join('')}
                            </ul>
                          </div>
                        `).join('')}
                      </div>
                    `}
                  />
                  <button
                    onClick={resetMindMap}
                    className="btn-secondary"
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    New Map
                  </button>
                </div>
              </div>

              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {mindmap.branches.map((branch, index) => (
                  <div
                    key={index}
                    className="p-4 border rounded-lg bg-gray-50 dark:bg-gray-800"
                  >
                    <h3 className="font-semibold mb-3 text-primary-600">
                      {branch.name}
                    </h3>
                    <ul className="space-y-2">
                      {branch.subtopics.map((subtopic, subIndex) => (
                        <li key={subIndex} className="text-sm">
                          <span className="font-medium">{subtopic.name}</span>
                          {subtopic.details && (
                            <p className="text-gray-600 dark:text-gray-400 ml-4 mt-1">
                              {subtopic.details}
                            </p>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MindMap; 