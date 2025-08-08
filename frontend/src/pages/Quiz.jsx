import React, { useState } from 'react';
import { HelpCircle, Plus, Play, Loader, Check, X, ChevronRight, RefreshCw } from 'lucide-react';
import DownloadPdfButton from '../components/DownloadPdfButton';
import { quizService } from '../services/quizService';

const Quiz = () => {
  const [text, setText] = useState('');
  const [numQuestions, setNumQuestions] = useState(5);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [quiz, setQuiz] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [score, setScore] = useState(0);
  const [quizCompleted, setQuizCompleted] = useState(false);

  const generateQuiz = async () => {
    if (!text.trim()) {
      setError('Please enter some text to generate a quiz from');
      return;
    }

    try {
      setIsGenerating(true);
      setError('');
      const result = await quizService.generateQuiz(text, numQuestions);
      setQuiz(result);
      setCurrentQuestion(0);
      setSelectedAnswer(null);
      setShowExplanation(false);
      setScore(0);
      setQuizCompleted(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate quiz');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleAnswerSelect = (answer) => {
    if (!showExplanation) {
      setSelectedAnswer(answer);
    }
  };

  const checkAnswer = () => {
    if (selectedAnswer === quiz.questions[currentQuestion].correct_answer) {
      setScore(score + 1);
    }
    setShowExplanation(true);
  };

  const nextQuestion = () => {
    if (currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
      setSelectedAnswer(null);
      setShowExplanation(false);
    } else {
      setQuizCompleted(true);
    }
  };

  const resetQuiz = () => {
    setQuiz(null);
    setText('');
    setSelectedAnswer(null);
    setShowExplanation(false);
    setScore(0);
    setQuizCompleted(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Quiz Generator</h1>
          <p className="text-gray-600 dark:text-gray-400">Generate quizzes from study materials with AI</p>
        </div>
        <div className="flex items-center space-x-2">
          <HelpCircle className="h-8 w-8 text-primary-600" />
        </div>
      </div>

      <div className="card">
        <div className="p-6">
          {!quiz && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Study Material
                </label>
                <textarea
                  className="w-full h-40 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800"
                  placeholder="Paste your study material here..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Number of Questions
                </label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={numQuestions}
                  onChange={(e) => setNumQuestions(parseInt(e.target.value))}
                  className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800"
                />
              </div>
              {error && (
                <div className="text-red-500 text-sm">
                  {error}
                </div>
              )}
              <button
                className="btn-primary w-full flex items-center justify-center"
                onClick={generateQuiz}
                disabled={isGenerating}
              >
                {isGenerating ? (
                  <>
                    <Loader className="h-4 w-4 mr-2 animate-spin" />
                    Generating Quiz...
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4 mr-2" />
                    Generate Quiz
                  </>
                )}
              </button>
            </div>
          )}

          {quiz && !quizCompleted && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-500">
                  Question {currentQuestion + 1} of {quiz.questions.length}
                </div>
                <div className="text-sm text-gray-500">
                  Score: {score}/{currentQuestion + (showExplanation ? 1 : 0)}
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-medium">
                  {quiz.questions[currentQuestion].question}
                </h3>

                <div className="space-y-2">
                  {quiz.questions[currentQuestion].options.map((option, index) => (
                    <button
                      key={index}
                      className={`w-full p-3 text-left border rounded-lg transition-colors ${
                        selectedAnswer === option
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                          : 'hover:border-gray-400'
                      } ${
                        showExplanation
                          ? option === quiz.questions[currentQuestion].correct_answer
                            ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                            : selectedAnswer === option
                            ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                            : ''
                          : ''
                      }`}
                      onClick={() => handleAnswerSelect(option)}
                      disabled={showExplanation}
                    >
                      {option}
                      {showExplanation && option === quiz.questions[currentQuestion].correct_answer && (
                        <Check className="h-5 w-5 text-green-500 inline ml-2" />
                      )}
                      {showExplanation && option === selectedAnswer && option !== quiz.questions[currentQuestion].correct_answer && (
                        <X className="h-5 w-5 text-red-500 inline ml-2" />
                      )}
                    </button>
                  ))}
                </div>

                {showExplanation && (
                  <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <h4 className="font-medium mb-2">Explanation:</h4>
                    <p>{quiz.questions[currentQuestion].explanation}</p>
                  </div>
                )}

                {!showExplanation && selectedAnswer && (
                  <button
                    className="btn-primary w-full"
                    onClick={checkAnswer}
                  >
                    Check Answer
                  </button>
                )}

                {showExplanation && (
                  <button
                    className="btn-primary w-full flex items-center justify-center"
                    onClick={nextQuestion}
                  >
                    {currentQuestion < quiz.questions.length - 1 ? (
                      <>
                        Next Question
                        <ChevronRight className="h-4 w-4 ml-2" />
                      </>
                    ) : (
                      'Complete Quiz'
                    )}
                  </button>
                )}
              </div>
            </div>
          )}

          {quizCompleted && (
            <div className="text-center space-y-6">
              <h3 className="text-2xl font-bold">Quiz Complete!</h3>
              <div className="text-4xl font-bold text-primary-600">
                {score}/{quiz.questions.length}
              </div>
              <p className="text-gray-600">
                {score === quiz.questions.length
                  ? 'Perfect score! Amazing work! 🎉'
                  : score >= quiz.questions.length * 0.7
                  ? 'Great job! Keep it up! 👏'
                  : 'Good effort! Try again to improve! 💪'}
              </p>
              <div className="flex items-center justify-center gap-2">
                <DownloadPdfButton
                  className="btn-secondary"
                  filename="quiz.pdf"
                  title="Quiz"
                  getHtml={() => `
                    <div class='section'>
                      <div class='meta'>Generated by AI Quiz · ${new Date().toLocaleString()}</div>
                      <h1>Quiz</h1>
                      <div class='section'>
                        <span class='pill'>Score: ${score}/${quiz.questions.length}</span>
                      </div>
                      ${quiz.questions.map((q, i) => `
                        <div class='section'>
                          <h2>Question ${i + 1}</h2>
                          <p>${q.question.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</p>
                          <ul>
                            ${q.options.map(opt => `<li>${opt.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</li>`).join('')}
                          </ul>
                          <p><strong>Correct:</strong> ${q.correct_answer.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</p>
                          <p class='muted small'><strong>Explanation:</strong> ${q.explanation.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</p>
                        </div>
                      `).join('')}
                    </div>
                  `}
                />
                <button
                  className="btn-primary flex items-center justify-center"
                  onClick={resetQuiz}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Generate New Quiz
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Quiz; 