import { BotMessageSquareIcon, CheckSquare, Square, ExternalLink, FileText, Check, User, BarChart2, LineChart, PieChart } from 'lucide-react';
import React, { useState } from 'react';
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

// Message Content Component
const MessageContent = ({ content, isUser, processBotMessage, isFirstInGroup, isLastInGroup }) => {
  const { text, citations } = processBotMessage();
  
  return (
    <div className="space-y-2 p-4">
      <div className="prose prose-sm max-w-none">
        <ReactMarkdown>{text}</ReactMarkdown>
      </div>
      {citations.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {citations.map((citation, index) => {
            const [_, id, rest] = citation.match(/^(\d+)\/(.*)/) || [];
            const isUrl = rest && rest.includes('://');
            
            return isUrl ? (
              <motion.a
                key={index}
                href={rest}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-2 py-1 text-sm bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 transition-colors"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <ExternalLink size={14} className="mr-1" />
                Source {id}
              </motion.a>
            ) : (
              <motion.span
                key={index}
                className="inline-flex items-center px-2 py-1 text-sm bg-gray-50 text-gray-600 rounded-md"
                whileHover={{ scale: 1.02 }}
              >
                <FileText size={14} className="mr-1" />
                Source {id}
              </motion.span>
            );
          })}
        </div>
      )}
    </div>
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
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-3">
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
const ChartComponent = ({ chart }) => {
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
    <div className="w-full max-w-xl mx-auto p-2 bg-gray-50 rounded-md">
      <div className="aspect-[4/3] w-full max-h-[300px]">
        {getChartComponent()}
      </div>
    </div>
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
  isLastInGroup
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
      <MessageContent 
        content={content} 
        isUser={isUser} 
        processBotMessage={processBotMessage}
        isFirstInGroup={isFirstInGroup}
        isLastInGroup={isLastInGroup}
      />
      
      {charts && charts.length > 0 && (
        <div className="px-4 pb-4 space-y-3">
          {charts.map((chart, index) => (
            <ChartComponent key={index} chart={chart} />
          ))}
        </div>
      )}
      
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