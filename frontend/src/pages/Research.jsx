import React, { useState } from 'react';
import { 
  Search, BookOpen, Copy, Download, Clock, 
  Users, Award, FileText, ArrowRight, Sparkles 
} from 'lucide-react';
import { researchService } from '../services/researchService';
import toast from 'react-hot-toast';

const Research = () => {
  const [topic, setTopic] = useState('');
  const [numPapers, setNumPapers] = useState(5);
  const [summarizationType, setSummarizationType] = useState('abstractive');
  const [summaryMode, setSummaryMode] = useState('technical');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  const handleSearch = async () => {
    if (!topic.trim()) {
      toast.error('Please enter a research topic');
      return;
    }

    try {
      setLoading(true);
      const response = await researchService.searchPapers({
        topic,
        num_papers: numPapers,
        summarization_type: summarizationType,
        summary_mode: summaryMode
      });
      setResults(response);
      toast.success('Research papers found and analyzed!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to search papers');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Research Paper Search
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Search and analyze research papers with AI-powered summaries
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <BookOpen className="h-8 w-8 text-primary-600" />
        </div>
      </div>

      {/* Search Section */}
      <div className="card">
        <div className="space-y-4">
          <div>
            <label htmlFor="topic" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Research Topic
            </label>
            <input
              type="text"
              id="topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter your research topic..."
              className="input-field w-full"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="numPapers" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Number of Papers
              </label>
              <input
                type="number"
                id="numPapers"
                min="1"
                max="10"
                value={numPapers}
                onChange={(e) => setNumPapers(Number(e.target.value))}
                className="input-field w-full"
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

            <div>
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
          </div>

          <div>
            <button
              onClick={handleSearch}
              disabled={loading}
              className="btn-primary flex items-center"
            >
              {loading ? (
                <div className="loading-spinner mr-2" />
              ) : (
                <Search className="h-4 w-4 mr-2" />
              )}
              Search Papers
            </button>
          </div>
        </div>
      </div>

      {/* Results Section */}
      {results && (
        <div className="space-y-6">
          {/* Papers */}
          <div className="space-y-4">
            {results.papers.map((paper, index) => (
              <div key={index} className="card">
                <div className="space-y-4">
                  {/* Paper Header */}
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {paper.title}
                      </h3>
                      <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400 mt-1">
                        <div className="flex items-center">
                          <Users className="h-4 w-4 mr-1" />
                          {paper.authors.join(', ')}
                        </div>
                        <div className="flex items-center">
                          <Clock className="h-4 w-4 mr-1" />
                          {paper.year}
                        </div>
                        <div className="flex items-center">
                          <Award className="h-4 w-4 mr-1" />
                          {paper.citations} citations
                        </div>
                      </div>
                    </div>
                    <a
                      href={paper.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary flex items-center"
                    >
                      <FileText className="h-4 w-4 mr-2" />
                      View Paper
                    </a>
                  </div>

                  {/* Summary */}
                  <div>
                    <h4 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-2">
                      AI Summary
                    </h4>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <p className="text-gray-700 dark:text-gray-300">
                        {paper.summary.summary}
                      </p>
                    </div>
                  </div>

                  {/* Key Findings */}
                  <div>
                    <h4 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-2">
                      Key Findings
                    </h4>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <ul className="space-y-2">
                        {paper.summary.key_findings.map((finding, idx) => (
                          <li key={idx} className="flex items-start">
                            <ArrowRight className="h-5 w-5 text-primary-500 mr-2 flex-shrink-0 mt-0.5" />
                            <span className="text-gray-700 dark:text-gray-300">{finding}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Citations */}
                  <div className="flex flex-col space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        APA Citation
                      </span>
                      <button
                        onClick={() => copyToClipboard(paper.citations_format.apa)}
                        className="text-primary-600 hover:text-primary-700"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        IEEE Citation
                      </span>
                      <button
                        onClick={() => copyToClipboard(paper.citations_format.ieee)}
                        className="text-primary-600 hover:text-primary-700"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Comparative Analysis */}
          {results.comparative_analysis && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Comparative Analysis
              </h3>
              <div className="space-y-4">
                {/* Common Themes */}
                <div>
                  <h4 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-2">
                    Common Themes
                  </h4>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <ul className="space-y-2">
                      {results.comparative_analysis.common_themes.map((theme, idx) => (
                        <li key={idx} className="flex items-start">
                          <Sparkles className="h-5 w-5 text-primary-500 mr-2 flex-shrink-0 mt-0.5" />
                          <span className="text-gray-700 dark:text-gray-300">{theme}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Research Trends */}
                <div>
                  <h4 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-2">
                    Research Trends
                  </h4>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-700 dark:text-gray-300">
                      {results.comparative_analysis.research_trends}
                    </p>
                  </div>
                </div>

                {/* Gaps and Opportunities */}
                <div>
                  <h4 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-2">
                    Future Research Opportunities
                  </h4>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <p className="text-gray-700 dark:text-gray-300">
                      {results.comparative_analysis.gaps_and_opportunities}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Research;
