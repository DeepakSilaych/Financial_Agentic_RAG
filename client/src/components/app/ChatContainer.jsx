import React, { useState, useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { chatApi } from '../../utils/api';
import { ScrollRestoration } from 'react-router-dom';
import { BotMessageSquareIcon } from 'lucide-react';

const ChatContainer = ({ chatId }) => {
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [ws, setWs] = useState(null);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);


  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const loadChat = async () => {
      try {
        const chatData = await chatApi.getChat(chatId);
        setMessages(chatData.messages?.map(msg => ({
          id: msg.id,
          content: msg.content,
          isUser: msg.role === 'user',
          mode: msg.mode,
          researchMode: msg.research_mode,
          intermediate_questions: msg.intermediate_questions?.map(q => ({
            id: q.id,
            question: q.question,
            answer: q.answer,
            type: q.question_type,
            options: q.options
          })) || []
        })) || []);
        setError(null);
      } catch (err) {
        setError('Failed to load chat history');
        console.error('Error loading chat:', err);
      }
    };

    const connectWebSocket = () => {
      const websocket = new WebSocket(chatApi.getWebSocketUrl(chatId));

      websocket.onopen = () => {
        console.log('WebSocket connected');
        setError(null);
      };

      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received WebSocket message:', data);
        
        if (data.type === 'ping') {
          return;
        } else if (data.type === 'message_received') {
          // Show user message instantly
          setMessages(prev => [...prev, {
            id: data.message_id,
            content: data.message,
            isUser: true,
            mode: 'chat',
            intermediate_questions: []
          }]);
        } else if (data.type === 'response') {
          // Show AI response
          setMessages(prev => [...prev, {
            id: data.message_id,
            content: data.content,
            isUser: data.is_user,
            mode: 'chat',
            intermediate_questions: []
          }]);
        } else if (data.type === 'clarification') {
          console.log("clarification-----------------------------------------", data);
          setMessages(prev => [...prev, {
            id: data.message_id,
            content: '',
            isUser: false,
            mode: 'clarification',
            intermediate_questions: [
              {
                id: data.message_id,
                question: data.question,
                type: data.question_type,
                options: data.options
              }
            ]
          }]);

        } else if (data.type === 'clarification_response') {
          console.log("clarification_response-----------------------------------------");
          setMessages(prev => {
            return prev.map(msg => {
              if (msg.id === data.message_id) {
                return { ...msg, intermediate_questions: msg.intermediate_questions.map(q => {
                  if (q.id === data.message_id) {
                    return { ...q, answer: data.answer };
                  }
                  return q;
                }) };
              }
              return msg;
            });
          });
        } else if (data.type === 'error') {
          setError(data.message);
          setMessages(prev => {
            prev.pop();
            return prev;
          });
        }
        scrollToBottom();
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
      };

      websocket.onclose = () => {
        console.log('WebSocket disconnected');
        setTimeout(connectWebSocket, 5000);
      };

      wsRef.current = websocket;
      setWs(websocket);
    };

    if (chatId) {
      loadChat();
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [chatId]);

  const handleAnswerSubmit = (questionId, answer) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'clarification_response',
        message_id: questionId,
        answer: answer
      }));

      setMessages(prev => {
        return prev.map(msg => {
          if (msg.intermediate_questions && msg.intermediate_questions.length > 0) {
            const updatedQuestions = msg.intermediate_questions.map(q => {
              if (q.id === questionId) {
                return { ...q, answer };
              }
              return q;
            });
            return { ...msg, intermediate_questions: updatedQuestions };
          }
          return msg;
        });
      });
    }
  };


  return (
    <div className='w-full h-[calc(100vh-4rem)]' style={{ scrollbarColor: 'rgba(0, 0, 0, 0) rgba(0, 0, 0, 0)' }}>
      <div className="max-w-7xl mx-auto flex-1 flex flex-col h-full">
        <div className="flex-1 overflow-y-auto px-4 py-6">
          {error ? (
            <div className="text-red-500">{error}</div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full space-y-6 px-4">
              <div className="w-24 h-24 rounded-full bg-pink-100 flex items-center justify-center">
                <BotMessageSquareIcon size={48} className="text-pink-600" />
              </div>
              <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold text-gray-900">Welcome to Pathway</h2>
                <p className="text-gray-600 max-w-md">
                  Your AI-powered research assistant. Ask questions about your documents or start a conversation to explore your data.
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl">
                <div className="p-4 bg-white rounded-lg border border-gray-200 hover:border-pink-400 transition-colors">
                  <h3 className="font-semibold mb-2 text-gray-900">💡 Ask Questions</h3>
                  <p className="text-sm text-gray-600">
                    "What are the key findings in the latest research paper?"
                  </p>
                </div>
                <div className="p-4 bg-white rounded-lg border border-gray-200 hover:border-pink-400 transition-colors">
                  <h3 className="font-semibold mb-2 text-gray-900">🔍 Analyze Documents</h3>
                  <p className="text-sm text-gray-600">
                    "Compare the methodology between these two studies"
                  </p>
                </div>
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <ChatMessage key={message.id} {...message} onAnswerSubmit={handleAnswerSubmit} />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
        <div className="p-4 border-t border-gray-200">
          <ChatInput ws={ws} setError={setError} />
        </div>
      </div>
    </div>
  );
};

export default ChatContainer;