import { BotMessageSquareIcon, CheckSquare, Square, ExternalLink, FileText, Check, User, BarChart2, LineChart, PieChart, BookmarkPlus } from 'lucide-react';
import React, { useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import { Bar, Line, Pie } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Dialog } from '@headlessui/react';
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

// Message Content Component
const MessageContent = ({ content, isUser, processBotMessage, isFirstInGroup, isLastInGroup }) => {
  const { text, citations } = processBotMessage();
  const [selectedText, setSelectedText] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleMouseUp = useCallback(() => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim().length > 0) {
      setSelectedText(selection.toString().trim());
    }
  }, []);

  const handleAddToNotes = useCallback(() => {
    setIsDialogOpen(true);
  }, []);

  const handleSaveNote = useCallback(async () => {
    if (selectedFile) {
      try {
        await notesApi.createNote(selectedFile, selectedText);
        setIsDialogOpen(false);
        setSelectedText('');
        setSelectedFile(null);
      } catch (error) {
        console.error('Error saving note:', error);
      }
    }
  }, [selectedFile, selectedText]);

  return (
    <div className="space-y-2 p-4" onMouseUp={handleMouseUp}>
      <div className="prose prose-sm max-w-none relative">
        <ReactMarkdown>{text}</ReactMarkdown>
        {selectedText && (
          <motion.button
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute top-0 right-0 p-2 bg-blue-500 text-white rounded-md flex items-center"
            onClick={handleAddToNotes}
          >
            <BookmarkPlus size={16} className="mr-1" />
            Add to Notes
          </motion.button>
        )}
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
                className="inline-flex items-center px-2 py-1 text-sm bg-gray-50 text-gray-600 rounded-md cursor-pointer"
                whileHover={{ scale: 1.02 }}
                onClick={() => setSelectedFile(rest)}
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
  const [selectedOption, setSelectedOption] = useState(null);
  const [customAnswer, setCustomAnswer] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      const answer = selectedOption || customAnswer;
      await onAnswerSubmit(question.id, answer);
      setIsSubmitting(false);
    } catch (error) {
      console.error('Error submitting answer:', error);
      setIsSubmitting(false);
    }
  };

  if (question.answer) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gray-50 rounded-lg p-4 my-2"
      >
        <div className="text-sm text-gray-600 mb-2">{question.question}</div>
        <div className="flex items-center gap-2">
          <Check size={16} className="text-green-500" />
          <span className="text-sm font-medium">{question.answer}</span>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-blue-50 rounded-lg p-4 my-2"
    >
      <div className="text-sm text-gray-700 mb-3">{question.question}</div>
      
      {question.options && question.options.length > 0 ? (
        <div className="space-y-2">
          {question.options.map((option, index) => (
            <motion.button
              key={index}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              onClick={() => setSelectedOption(option)}
              className={`w-full text-left p-3 rounded-md text-sm transition-colors ${
                selectedOption === option
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2">
                {selectedOption === option ? (
                  <CheckSquare size={16} />
                ) : (
                  <Square size={16} />
                )}
                {option}
              </div>
            </motion.button>
          ))}
          
          {selectedOption && (
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className={`mt-4 px-4 py-2 rounded-md text-sm font-medium text-white transition-colors ${
                isSubmitting ? 'bg-blue-400' : 'bg-blue-500 hover:bg-blue-600'
              }`}
              onClick={handleSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Submitting...' : 'Submit Answer'}
            </motion.button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          <input
            type="text"
            value={customAnswer}
            onChange={(e) => setCustomAnswer(e.target.value)}
            placeholder="Type your answer..."
            className="w-full p-2 rounded-md border border-gray-200 text-sm"
          />
          {customAnswer && (
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className={`px-4 py-2 rounded-md text-sm font-medium text-white transition-colors ${
                isSubmitting ? 'bg-blue-400' : 'bg-blue-500 hover:bg-blue-600'
              }`}
              onClick={handleSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Submitting...' : 'Submit Answer'}
            </motion.button>
          )}
        </div>
      )}
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

  const getChartOptions = (type) => {
    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          align: 'center',
          labels: {
            padding: 8,
            usePointStyle: true,
            pointStyle: 'circle',
            boxWidth: 6,
            boxHeight: 6,
            font: {
              size: 10,
              family: "'Inter', sans-serif"
            }
          }
        },
        title: {
          display: false
        },
        tooltip: {
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          titleColor: '#1f2937',
          bodyColor: '#4b5563',
          borderColor: 'rgba(0, 0, 0, 0.1)',
          borderWidth: 1,
          padding: 8,
          boxPadding: 3,
          usePointStyle: true,
          bodyFont: {
            size: 10,
            family: "'Inter', sans-serif"
          },
          titleFont: {
            size: 11,
            family: "'Inter', sans-serif",
            weight: '600'
          }
        }
      },
      animation: {
        duration: 500,
        easing: 'easeOutQuart'
      }
    };

    if (type === 'bar' || type === 'line') {
      return {
        ...baseOptions,
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              maxRotation: 45,
              minRotation: 45,
              padding: 5,
              font: {
                size: 10,
                family: "'Inter', sans-serif"
              }
            }
          },
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.06)',
              drawBorder: false
            },
            ticks: {
              padding: 5,
              font: {
                size: 10,
                family: "'Inter', sans-serif"
              }
            }
          }
        }
      };
    }

    if (type === 'pie') {
      return {
        ...baseOptions,
        plugins: {
          ...baseOptions.plugins,
          legend: {
            ...baseOptions.plugins.legend,
            position: 'right',
            labels: {
              ...baseOptions.plugins.legend.labels,
              padding: 10
            }
          }
        }
      };
    }

    return baseOptions;
  };

  const getDatasetStyle = (index, type) => {
    const colors = [
      'rgba(66, 133, 244, 0.8)',   // Google Blue
      'rgba(234, 67, 53, 0.8)',    // Google Red
      'rgba(251, 188, 4, 0.8)',    // Google Yellow
      'rgba(52, 168, 83, 0.8)',    // Google Green
      'rgba(103, 58, 183, 0.8)',   // Purple
      'rgba(255, 152, 0, 0.8)',    // Orange
    ];

    const baseStyle = {
      backgroundColor: colors[index % colors.length],
      borderColor: colors[index % colors.length].replace('0.8', '1'),
      borderWidth: 1.5,
      hoverBackgroundColor: colors[index % colors.length].replace('0.8', '0.9'),
      hoverBorderColor: colors[index % colors.length].replace('0.8', '1'),
      hoverBorderWidth: 2
    };

    if (type === 'line') {
      return {
        ...baseStyle,
        fill: false,
        tension: 0.3,
        pointRadius: 3,
        pointHoverRadius: 5,
        pointBackgroundColor: colors[index % colors.length].replace('0.8', '1'),
        pointBorderColor: '#fff',
        pointBorderWidth: 1.5,
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: colors[index % colors.length].replace('0.8', '1')
      };
    }

    if (type === 'pie') {
      return {
        backgroundColor: colors.map(color => color.replace('0.8', '0.75')),
        borderColor: colors.map(color => color.replace('0.8', '1')),
        borderWidth: 1,
        hoverBackgroundColor: colors.map(color => color.replace('0.8', '0.85')),
        hoverBorderColor: colors.map(color => color.replace('0.8', '1')),
        hoverBorderWidth: 2,
        hoverOffset: 4
      };
    }

    return baseStyle;
  };

  const getChartComponent = () => {
    const chartData = {
      ...chart.data,
      datasets: chart.data.datasets.map((dataset, index) => ({
        ...dataset,
        ...getDatasetStyle(index, chart.chart_type)
      }))
    };

    const commonProps = {
      options: getChartOptions(chart.chart_type),
      data: chartData
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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-lg mx-auto my-2 bg-white rounded-lg shadow-sm overflow-hidden"
    >
      <div className="p-2 border-b flex items-center gap-2">
        {chartIcons[chart.chart_type]}
        <span className="font-medium text-gray-700 text-xs">{chart.title || `${chart.chart_type.charAt(0).toUpperCase() + chart.chart_type.slice(1)} Chart`}</span>
      </div>
      <div className="p-2">
        <div className="aspect-[16/9] w-full" style={{ height: '200px' }}>
          {getChartComponent()}
        </div>
      </div>
    </motion.div>
  );
};

// KPI Component
const KPIComponent = ({ kpi }) => {
  if (!kpi) return null;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mt-4"
    >
      <div className="flex items-center gap-2 mb-2">
        <BarChart2 className="text-blue-500" size={20} />
        <h3 className="font-semibold text-gray-800">{kpi.title}</h3>
      </div>
      <div className="text-2xl font-bold text-blue-600">{kpi.value}</div>
      {kpi.change && (
        <div className={`text-sm mt-1 ${kpi.change > 0 ? 'text-green-600' : 'text-red-600'}`}>
          {kpi.change > 0 ? '↑' : '↓'} {Math.abs(kpi.change)}% from previous period
        </div>
      )}
    </motion.div>
  );
};

// Insights Component
const InsightsComponent = ({ insights }) => {
  if (!insights || insights.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mt-4"
    >
      <div className="flex items-center gap-2 mb-3">
        <LineChart className="text-purple-500" size={20} />
        <h3 className="font-semibold text-gray-800">Key Insights</h3>
      </div>
      <ul className="space-y-2">
        {insights.map((insight, index) => (
          <li key={index} className="flex items-start gap-2">
            <div className="min-w-[24px] h-6 flex items-center justify-center rounded-full bg-purple-100 text-purple-600 text-sm">
              {index + 1}
            </div>
            <p className="text-gray-700">{insight}</p>
          </li>
        ))}
      </ul>
    </motion.div>
  );
};

// Message Group Header Component
const MessageGroupHeader = ({ isUser }) => {
  return (
    <div className="flex items-center mb-2 text-sm text-gray-500">
      {isUser ? 'You' : 'Assistant'}
    </div>
  );
};

// Main ChatMessage Component
const ChatMessage = ({ 
  content, 
  isUser, 
  intermediate_questions = [], 
  charts = [], 
  kpi = null,
  insights = [],
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
    <div className={`flex flex-col ${isFirstInGroup ? 'mt-6' : 'mt-2'} ${isLastInGroup ? 'mb-6' : 'mb-2'}`}>
      {/* {isFirstInGroup && <MessageGroupHeader isUser={isUser} />} */}
      <div className="flex items-start gap-4">
            <MessageContent 
              content={content} 
              isUser={isUser} 
              processBotMessage={processBotMessage}
              isFirstInGroup={isFirstInGroup}
              isLastInGroup={isLastInGroup}
            />
      </div>
    </div>
  );
};

export default ChatMessage;