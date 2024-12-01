  import { Bot, BotMessageSquare, BotMessageSquareIcon, CheckSquare, KeyboardMusicIcon } from 'lucide-react';
import { ArrowUp, Check, Square, ExternalLink, FileText } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';

const ChatMessage = ({ content, isUser, mode, intermediate_questions = [], onAnswerSubmit }) => {
  const [answer, setAnswer] = useState('');
  const [selectedOptions, setSelectedOptions] = useState([]);

  useEffect(() => {
    console.log({
      "questions" : intermediate_questions
    })
  }, [intermediate_questions]);

  const handleSubmitAnswer = (e, questionId) => {
    e.preventDefault();
    if (answer.trim() || selectedOptions.length > 0) {
      onAnswerSubmit(questionId, answer.trim() || selectedOptions);
      setAnswer('');
      setSelectedOptions([]);
    }
  };

  const handleOptionClick = (option, questionId) => {
    if (selectedOptions.includes(option)) {
      setSelectedOptions(prev => prev.filter(item => item !== option));
    } else {
      setSelectedOptions(prev => [...prev, option]);
    }
  };

  // Extract citations from content if it's a bot message
  const processBotMessage = () => {
    if (isUser) return { text: content, citations: [] };

    const citations = [];
    // Split content into text and citations while preserving order
    const segments = content.split(/(\[\[.+?\]\])/g);
    const processedSegments = segments.map(segment => {
      if (segment.startsWith('[[') && segment.endsWith(']]')) {
        const citation = segment.slice(2, -2);
        citations.push(citation);
        
        // First, get the ID
        const idMatch = citation.match(/^(\d+)\/(.*)/);
        if (!idMatch) return segment; // Invalid citation format
        
        const [_, id, rest] = idMatch;
        const isUrl = rest.includes('://');
        
        if (isUrl) {
          return (
            <a
              key={id}
              href={rest}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline inline-flex items-center"
            >
              <ExternalLink size={16} className="mr-1" />
              Source {id}
            </a>
          );
        } else {
          return (
            <span key={id} className="inline-flex items-center text-gray-600">
              <FileText size={16} className="mr-1" />
              Source {id}
            </span>
          );
        }
      }
      return <ReactMarkdown className="prose dark:prose-invert max-w-none">{segment}</ReactMarkdown>;
    });

    return { text: processedSegments, citations };
  };

  const { text, citations } = processBotMessage();

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div 
        className={`max-w-[80%] ${
          isUser 
            ? 'bg-pink-600 text-white rounded-tr-none' 
            : 'bg-gray-100 rounded-tl-none'
        } rounded-2xl px-6 py-4 shadow-sm hover:shadow-md transition-shadow duration-200`}
      >
        <div className="flex items-center gap-2 mb-2">
          {!isUser && (
            <BotMessageSquareIcon size={20} className="text-pink-600" />
          )}
          <span className="text-sm font-medium">
            {isUser ? 'You' : 'Pathway AI'}
          </span>
        </div>
        
        <div className={`text-md ${isUser ? 'text-white' : 'text-gray-800'}`}>
          {Array.isArray(text) ? text : text}
        </div>

        {!isUser && citations.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm font-medium mb-2 text-gray-700">Sources:</p>
            <div className="space-y-2">
              {citations.map((citation, index) => {
                // Parse citation with regex to handle URLs properly
                const match = citation.match(/^(\d+)\/(.*?)(?:\/(\d+))?$/);
                if (!match) return null;
                
                const [_, id, link, page] = match;
                const isUrl = link.includes('://');
                
                return (
                  <div 
                    key={index}
                    onClick={() => isUrl && window.open(link, '_blank')}
                    className={`flex items-center space-x-2 text-sm ${isUrl ? 'cursor-pointer hover:text-blue-600' : ''}`}
                  >
                    {isUrl ? (
                      <ExternalLink size={16} className="text-gray-500" />
                    ) : (
                      <FileText size={16} className="text-gray-500" />
                    )}
                    <span>
                      [{id}] {isUrl ? link : `${link} (Page ${page})`}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {intermediate_questions && intermediate_questions.length > 0 && (
          intermediate_questions.map((question, index) => (
            <div key={index} className="mb-4">
              {!question.answer ? (
                question.type === 'single-choice' || question.type === 'multiple-choice' ? (
                  <form onSubmit={(e) => handleSubmitAnswer(e, question.id)} className="mt-3 border border-blackcolor rounded-lg p-6 h-full">
                    <p className="text-sm mb-2">Please select {question.type === 'single-choice' ? 'one option' : 'at least one option'}</p>
                    <p className="text-sm mb-4 font-medium">{question.question}</p>
                    <div className="space-y-2">
                      {question.options.map((option, optionIndex) => (
                        <button
                          type="button"
                          key={optionIndex}
                          onClick={() => handleOptionClick(option, question.id)}
                          className={`w-full p-2 text-left rounded-lg ${
                            selectedOptions.includes(option) ? 'bg-gray-300' : 'bg-gray-200'
                          } text-blackcolor transition-colors flex justify-between items-center`}
                        >
                          <span>{option}</span>
                          {selectedOptions.includes(option) ? (
                            <CheckSquare size={20} className="text-blackcolor" />
                          ) : (
                            <Square size={20} className="text-blackcolor" />
                          )}
                        </button>
                      ))}
                      <input 
                        type="text"
                        value={selectedOptions}
                        onChange={(e) => setSelectedOptions(e.target.value)}
                        className="w-full p-2 border border-gray-300 rounded-lg mb-4"
                        placeholder="If none of the above, type your answer here..."
                      />
                    </div>
                    <button
                      type="submit"
                      className="mt-4 p-2 bg-blackcolor text-white rounded-lg hover:bg-black transition-colors w-full"
                      disabled={selectedOptions.length === 0}
                    >
                      Submit
                    </button>
                  </form>
                ) : (
                  <form onSubmit={(e) => handleSubmitAnswer(e, question.id)} className="mt-3 border border-blackcolor rounded-lg p-6">
                    <p className="text-sm mb-4 font-medium">{question.question}</p>
                    <input
                      type="text"
                      value={answer}
                      onChange={(e) => setAnswer(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-lg mb-4"
                      placeholder="Type your answer here..."
                    />
                    <button
                      type="submit"
                      className="w-full p-2 bg-blackcolor text-white rounded-lg hover:bg-black transition-colors"
                      disabled={!answer.trim()}
                    >
                      Submit
                    </button>
                  </form>
                )
              ) : (
                <div className="mt-3 border border-blackcolor rounded-lg p-6">
                  <div className="flex justify-between items-start mb-4">
                    <p className="text-sm font-medium">{question.question}</p>
                    <Check size={20} className="text-green-500 ml-2 flex-shrink-0" />
                  </div>
                  <div className="mt-2 p-3 bg-gray-100 rounded-lg">
                    <p className="text-sm text-gray-700">
                      {Array.isArray(question.answer) 
                        ? question.answer.join(', ') 
                        : question.answer}
                    </p>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ChatMessage;