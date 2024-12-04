import { BotMessageSquareIcon, CheckSquare, Square, ExternalLink, FileText, Check, User, BarChart2, LineChart, PieChart } from 'lucide-react';
import React, { useState, useEffect, useRef, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import { Bar, Line, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { notesApi } from '../../utils/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

// Avatar Component
export const Avatar = ({ isUser }) => (
  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${isUser ? 'bg-blue-500' : 'bg-purple-500'}`}>
    {isUser ? (
      <User size={18} className="text-white" />
    ) : (
      <BotMessageSquareIcon size={18} className="text-white" />
    )}
  </div>
);

const MessageContent = ({ content, isUser, processBotMessage, isFirstInGroup, isLastInGroup, isWebSocketResponse }) => {
  const { text, citations } = processBotMessage();
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(isWebSocketResponse);
  const [textSelection, setTextSelection] = useState('');
  const [showAddToNote, setShowAddToNote] = useState(false);
  const [noteButtonPosition, setNoteButtonPosition] = useState({ top: 0, left: 0 });
  const [showFileDialog, setShowFileDialog] = useState(false);
  const contentRef = useRef(null);

  useEffect(() => {
    const handleSelectionChange = () => {
      const selection = window.getSelection();
      const selectedText = selection?.toString().trim();
      setTextSelection(selectedText);

      if (selectedText && contentRef.current) {
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        const contentRect = contentRef.current.getBoundingClientRect();

        setNoteButtonPosition({
          top: rect.bottom - contentRect.top + 5,
          left: rect.left + (rect.width / 2) - contentRect.left
        });
        setShowAddToNote(true);
      } else {
        setShowAddToNote(false);
      }
    };

    document.addEventListener('selectionchange', handleSelectionChange);
    return () => {
      document.removeEventListener('selectionchange', handleSelectionChange);
    };
  }, []);

  useEffect(() => {
    if (!isWebSocketResponse) {
      setDisplayedText(text);
      setIsTyping(false);
      return;
    }

    let currentIndex = 0;
    const typingInterval = setInterval(() => {
      if (currentIndex < text.length) {
        setDisplayedText(prevText => prevText + text[currentIndex]);
        currentIndex++;
      } else {
        setIsTyping(false);
        clearInterval(typingInterval);
      }
    }, 20);

    return () => clearInterval(typingInterval);
  }, [text, isWebSocketResponse]);

  const containerWidth = useMemo(() => {
    const baseWidth = 300;
    const charWidth = 8;
    const contentLength = text.length;
    return Math.min(Math.max(baseWidth, contentLength * charWidth), 800);
  }, [text]);

  const handleAddToNote = () => {
    setShowFileDialog(true);
    setShowAddToNote(false);
  };

  const handleFileSelect = (file) => {
    const filename = file.split('/')[0];
    notesApi.createNote(filename, textSelection)
      .then(() => {
        console.log('Note added successfully to:', filename);
        setShowFileDialog(false);
      })
      .catch((error) => {
        console.error('Failed to add note:', error);
        // You might want to show an error message to the user here
      });
  };
  
  return (
    <motion.div 
      className="space-y-2 p-4 relative"
      initial={isWebSocketResponse ? { width: 0, opacity: 0 } : false}
      animate={{ width: isWebSocketResponse ? containerWidth : '100%', opacity: 1 }}
      transition={{ duration: 0.5 }}
      ref={contentRef}
    >
      <div className="prose prose-sm max-w-none">
        <ReactMarkdown>{displayedText}</ReactMarkdown>
      </div>
      <AnimatePresence>
        {showAddToNote && (
          <motion.button
            className="absolute bg-blue-500 text-white px-2 py-1 rounded-md text-sm z-10 flex items-center shadow-md hover:bg-blue-600 transition-colors"
            style={{ top: noteButtonPosition.top, left: noteButtonPosition.left, transform: 'translateX(-50%)' }}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            onClick={handleAddToNote}
          >
            <FileText size={14} className="mr-1" />
            Add to Note
          </motion.button>
        )}
      </AnimatePresence>
      {showFileDialog && (
        <div className="fixed left-0 -top-10 h-[110vh] w-[110vw] inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-md">
            <h3 className="text-lg font-semibold mb-2">Select a file to add the note:</h3>
            {citations.map((citation, index) => {
              const [_, id, rest] = citation.match(/^(\d+)\/(.*)/) || [];
              return (
                <button
                  key={index}
                  className="block w-full text-left px-2 py-1 hover:bg-gray-100 rounded-md"
                  onClick={() => handleFileSelect(rest)}
                >
                  Source {id}: {rest}
                </button>
              );
            })}
            <button
              className="mt-4 bg-red-500 text-white px-2 py-1 rounded-md"
              onClick={() => setShowFileDialog(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      {!isTyping && citations.length > 0 && (
        <motion.div 
          className="flex flex-wrap gap-2 mt-2"
          initial={isWebSocketResponse ? { opacity: 0, y: 20 } : false}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          {citations.map((citation, index) => {
            const [_, id, rest] = citation.match(/^(\d+)\/(.*)/) || [];
            const isUrl = rest && rest.includes('://');
            
            const CitationComponent = isUrl ? motion.a : motion.span;
            const props = isUrl ? {
              href: rest,
              target: "_blank",
              rel: "noopener noreferrer",
              className: "inline-flex items-center px-2 py-1 text-sm bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 transition-colors"
            } : {
              className: "inline-flex items-center px-2 py-1 text-sm bg-gray-50 text-gray-600 rounded-md"
            };

            return (
              <CitationComponent
                key={index}
                {...props}
                initial={isWebSocketResponse ? { opacity: 0, x: -20 } : false}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + index * 0.1 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                {isUrl ? <ExternalLink size={14} className="mr-1" /> : <FileText size={14} className="mr-1" />}
                Source {id}
              </CitationComponent>
            );
          })}
        </motion.div>
      )}
    </motion.div>
  );
};

// Intermediate Question Component
const IntermediateQuestion = ({ question, onAnswerSubmit }) => {
  const [answer, setAnswer] = useState('');
  const [selectedOptions, setSelectedOptions] = useState([]);
  const isMultipleChoice = Array.isArray(question.options) && question.options.length > 0;
  const isAnswered = question.answer !== undefined;

  const handleOptionClick = (option) => {
    setSelectedOptions(prev => 
      prev.includes(option) ? prev.filter(item => item !== option) : [...prev, option]
    );
  };

  const handleSubmitAnswer = (e) => {
    e.preventDefault();
    if (answer.trim() || selectedOptions.length > 0) {
      onAnswerSubmit(question.id, answer.trim() || selectedOptions);
      setAnswer('');
      setSelectedOptions([]);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="mt-4 bg-white border border-gray-200 rounded-lg overflow-hidden"
    >
      <div className="flex items-start p-4">
        <div className="flex-shrink-0 w-s interesting patterns. Th8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-3">
          <BotMessageSquareIcon size={18} className="text-blue-600" />
        </div>
        <div className="flex-1">
          <h4 className="text-gray-700 mb-3">{question.question}</h4>
          
          {isAnswered ? (
            <div className="bg-gray-50 p-3 rounded-md border border-gray-200">
              <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                <Check size={16} className="text-green-500" />
                <span>Answered</span>
              </div>
              <div className="text-gray-700">
                {Array.isArray(question.answer) 
                  ? question.answer.join(', ')
                  : question.answer
                }
              </div>
            </div>
          ) : isMultipleChoice ? (
            <div className="space-y-2">
              {question.options.map((option, idx) => (
                <button
                  key={idx}
                  onClick={() => handleOptionClick(option)}
                  className="flex items-center w-full p-3 text-left border rounded-md hover:bg-gray-50 transition-colors"
                >
                  {selectedOptions.includes(option) ? (
                    <CheckSquare size={18} className="text-blue-500 mr-2" />
                  ) : (
                    <Square size={18} className="text-gray-400 mr-2" />
                  )}
                  {option}
                </button>
              ))}
              {selectedOptions.length > 0 && (
                <button
                  onClick={handleSubmitAnswer}
                  className="mt-3 w-full py-2 px-4 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                >
                  Submit Answer
                </button>
              )}
            </div>
          ) : (
            <form onSubmit={handleSubmitAnswer} className="space-y-3">
              <input
                type="text"
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                className="w-full p-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="Type your answer..."
              />
              <button
                type="submit"
                className="w-full py-2 px-4 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                disabled={!answer.trim()}
              >
                Submit Answer
              </button>
            </form>
          )}
        </div>
      </div>
    </motion.div>
  );
};

// Chart Component
const ChartComponent = ({ chart, index, isWebSocketResponse }) => {
  const [isVisible, setIsVisible] = useState(!isWebSocketResponse);

  useEffect(() => {
    if (!isWebSocketResponse) {
      setIsVisible(true);
      return;
    }

    const timer = setTimeout(() => {
      setIsVisible(true);
    }, index * 500);

    return () => clearTimeout(timer);
  }, [index, isWebSocketResponse]);

  const chartIcons = {
    'bar': <BarChart2 size={18} className="text-blue-600" />,
    'line': <LineChart size={18} className="text-blue-600" />,
    'pie': <PieChart size={18} className="text-blue-600" />
  };

  const getChartOptions = () => ({
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: false,
      },
    },
    animation: {
      duration: 1000,
      easing: 'easeInOutQuart'
    }
  });

  const getChartComponent = () => {
    const commonProps = {
      options: getChartOptions(),
      data: chart.data
    };

    switch (chart.chart_type) {
      case 'bar':
        return <Bar {...commonProps} />;
      case 'line':
        return <Line {...commonProps} />;
      case 'pie':
        return <Pie {...commonProps} />;
      default:
        return null;
    }
  };

  return (
    <motion.div 
      className="w-full max-w-xl mx-auto p-2 bg-gray-50 rounded-md"
      initial={isWebSocketResponse ? { opacity: 0, y: 20 } : false}
      animate={{ opacity: isVisible ? 1 : 0, y: isVisible ? 0 : 20 }}
      transition={{ duration: 0.5 }}
    >
      <div className="aspect-[4/3] w-full max-h-[300px]">
        {isVisible && getChartComponent()}
      </div>
    </motion.div>
  );
};

// Main ChatMessage Component
const ChatMessage = ({ 
  content, 
  isUser, 
  intermediate_questions = [], 
  charts = [], 
  onAnswerSubmit,
  isFirstInGroup,
  isLastInGroup,
  isWebSocketResponse = false
}) => {
  const processBotMessage = () => {
    if (!content) return { text: '', citations: [] };

    const citations = [];
    const segments = content.split(/(\[\[.+?\]\])/g);
    const text = segments.map(segment => {
      if (segment.startsWith('[[') && segment.endsWith(']]')) {
        const citation = segment.slice(2, -2);
        citations.push(citation);
        return '';
      }
      return segment;
    }).join('');
    
    return { text, citations };
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex flex-col ${isUser ? 'text-gray-800' : 'text-gray-800'} w-full`}
    >
      {/* Show charts above text */}
      {charts && charts.length > 0 && (
        <div className="px-4 pb-4 space-y-3">
          {charts.map((chart, index) => (
            <ChartComponent 
              key={index} 
              chart={chart} 
              index={index}
              isWebSocketResponse={isWebSocketResponse}
            />
          ))}
        </div>
      )}
      
      <MessageContent 
        content={content} 
        isUser={isUser} 
        processBotMessage={processBotMessage}
        isFirstInGroup={isFirstInGroup}
        isLastInGroup={isLastInGroup}
        isWebSocketResponse={isWebSocketResponse}
      />
      
      {intermediate_questions && intermediate_questions.length > 0 && (
        <div className="px-4 pb-4">
          {intermediate_questions.map((question, index) => (
            <IntermediateQuestion
              key={index}
              question={question}
              onAnswerSubmit={onAnswerSubmit}
            />
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default ChatMessage;