import React, { useState, useEffect, useRef } from "react";
import ChatMessage, { Avatar } from "./ChatMessage";
import ChatInput from "./ChatInput";
import { chatApi } from "../../utils/api";
import { Link, ScrollRestoration, useNavigate } from "react-router-dom";
import {
  BotMessageSquareIcon,
  GripVertical,
  PlusIcon,
  UploadCloudIcon,
  MessageSquare,
  Upload,
  Search,
} from "lucide-react";
import Tab from "./Tab";
import { useUser } from "../../context/UserContext";
import { motion } from "framer-motion";

import LogoWithoutText from "../../assets/logo-without-text.svg";

// Loading Animation Component
const LoadingDots = () => (
  <div className="flex space-x-2">
    <div
      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
      style={{ animationDelay: "0ms" }}
    />
    <div
      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
      style={{ animationDelay: "150ms" }}
    />
    <div
      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
      style={{ animationDelay: "300ms" }}
    />
  </div>
);

// Loading Message Component
const LoadingMessage = () => (
  <div className="flex flex-col items-start">
    <div className="flex items-center gap-2 mb-2">
      <Avatar isUser={false} />
      <span className="text-sm text-gray-500">Assistant</span>
    </div>
    <div className="bg-white rounded-lg shadow-sm p-4">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <LoadingDots />
      </motion.div>
    </div>
  </div>
);

// Empty State Component
const EmptyState = () => (
  <div className="h-full flex flex-col items-center justify-center text-center">
    <div className="max-w-2xl mx-auto px-4">
      <div className="mb-8">
        <img src={LogoWithoutText} alt="FinSight AI" className="w-24 h-24" />
        <h2 className="text-2xl font-semibold text-gray-800 mb-2">
          Welcome to FinSight AI
        </h2>
        <p className="text-gray-600">
          Your intelligent assistant for document analysis and insights
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center mb-4">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center mr-4">
              <MessageSquare className="w-5 h-5 text-blue-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-800">Chat</h3>
          </div>
          <p className="text-gray-600 text-sm">
            Ask questions about your documents and get instant, accurate
            responses with citations
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center mb-4">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center mr-4">
              <UploadCloudIcon className="w-5 h-5 text-blue-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-800">Upload</h3>
          </div>
          <p className="text-gray-600 text-sm">
            Share your documents securely and let AI analyze them for you
          </p>
        </div>
      </div>

      <div className="text-gray-500 text-sm">
        Start by typing a message below or uploading a document
      </div>
    </div>
  </div>
);

// Message Group Header Component
const MessageGroupHeader = ({ isUser }) => (
  <div
    className={`flex items-center gap-2 mb-2 ${
      isUser ? "flex-row-reverse" : "flex-row"
    }`}
  >
    <Avatar isUser={isUser} />
    <span className="text-sm text-gray-500">{isUser ? "You" : "FinSight"}</span>
  </div>
);

// Message Group Component
const MessageGroup = ({ group, onAnswerSubmit }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
    className={`flex flex-col ${group.isUser ? "items-end" : "items-start"}`}
  >
    <MessageGroupHeader isUser={group.isUser} />
    <div
      className={`flex flex-col ${
        group.isUser ? "items-end" : "items-start"
      } space-y-1 max-w-[80%]`}
    >
      <div className="w-full bg-blue-200 rounded-lg shadow-sm overflow-hidden">
        {group.messages.map((message, messageIndex) => (
          <ChatMessage
            key={message.id || messageIndex}
            {...message}
            isUser={group.isUser}
            isFirstInGroup={messageIndex === 0}
            isLastInGroup={messageIndex === group.messages.length - 1}
            onAnswerSubmit={onAnswerSubmit}
          />
        ))}
      </div>
    </div>
  </motion.div>
);

// Chat Messages Container Component
const ChatMessages = ({
  messages,
  isLoading,
  messageEndRef,
  onAnswerSubmit,
}) => (
  <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-gray-50">
    {messages.length === 0 ? (
      <EmptyState />
    ) : (
      <div className="pb-52">
        {messages.map((group, groupIndex) => (
          <MessageGroup
            key={groupIndex}
            group={group}
            onAnswerSubmit={onAnswerSubmit}
          />
        ))}
        {isLoading && <LoadingMessage />}
        <div ref={messageEndRef} />
      </div>
    )}
  </div>
);

// Resize Handle Component
const ResizeHandle = ({ onMouseDown }) => (
  <div
    className="w-1 border-l border-gray-200 hover:border-blue-400 transition-border-color duration-200 cursor-col-resize flex items-center justify-center"
    onMouseDown={onMouseDown}
  >
    <GripVertical size={20} className="text-gray-500" />
  </div>
);

// Main ChatContainer Component
const ChatContainer = ({ chatId }) => {
  const { currentSpace, createChat } = useUser();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [ws, setWs] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSetTitle, setHasSetTitle] = useState(false);
  const [loading, setLoading] = useState(false);
  const messageEndRef = useRef(null);
  const wsRef = useRef(null);
  const [chatWidth, setChatWidth] = useState(100);
  const isDraggingRef = useRef(false);
  const dragStartXRef = useRef(0);
  const initialWidthRef = useRef(0);
  const containerRef = useRef(null);
  const chatContainerRef = useRef(null);
  const pendingMessageRef = useRef(null);

  const scrollToBottom = () => {
    if (messageEndRef.current) {
      messageEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    const loadChat = async () => {
      try {
        if (!currentSpace?.id || !chatId) return;
        const chatData = await chatApi.getChat(currentSpace.id, chatId);
        setMessages(
          chatData.messages?.map((msg) => {
            // If the message has intermediate questions and no content, it's a clarification message
            // if (msg.intermediate_questions?.length > 0 && !msg.content) {
            //   return {
            //     id: msg.id,
            //     content: "", // Keep content empty for clarification messages
            //     isUser: false, // Force isUser to false for clarification messages
            //     mode: "chat",
            //     intermediate_questions: msg.intermediate_questions.map((q) => ({
            //       id: q.id,
            //       question: q.question,
            //       answer: q.answer,
            //       questionType: "clarification",
            //       options: q.options ? JSON.parse(q.options) : [],
            //     })),
            //   };
            // }
            // Regular message
            return {
              id: msg.id,
              content: msg.content,
              isUser: msg.is_user,
              mode: msg.mode,
              researchMode: msg.research_mode,
              // intermediate_questions:
              //   msg.intermediate_questions?.map((q) => ({
              //     id: q.id,
              //     question: q.question,
              //     answer: q.answer,
              //     questionType: q.question_type,
              //     options: q.options ? JSON.parse(q.options) : [],
              //   })) || [],
              kpiAnalysis: msg.kpi_analysis[0]?.data,
              charts:
                msg.charts?.map((chart) => ({
                  id: chart.id,
                  chart_type: chart.chart_type,
                  title: chart.title,
                  data:
                    typeof chart.data === "string"
                      ? JSON.parse(chart.data)
                      : chart.data,
                  description: chart.description,
                })) || [],
            };
          }) || []
        );
        setHasSetTitle(!!chatData.title);
        setError(null);
      } catch (error) {
        console.error("Error loading chat:", error);
        setError("Failed to load chat");
      }
    };

    loadChat();
  }, [chatId, currentSpace?.id]);

  useEffect(() => {
    const setupWebSocket = async () => {
      if (!currentSpace?.id || (!chatId && !pendingMessageRef.current)) return;

      try {
        // If there's no active chat but there's a pending message, create a new chat
        if (!chatId && pendingMessageRef.current) {
          setLoading(true);
          const newChat = await createChat();
          navigate(`/app/chat/${newChat.id}`);
          return;
        }

        const wsUrl = chatApi.getWebSocketUrl(currentSpace.id, chatId);
        const newWs = new WebSocket(wsUrl);

        newWs.onopen = () => {
          console.log("WebSocket connected");
          setError(null);

          // If there's a pending message, send it once connected
          if (pendingMessageRef.current) {
            newWs.send(JSON.stringify(pendingMessageRef.current));
            pendingMessageRef.current = null;
          }
        };

        newWs.onmessage = (event) => {
          const data = JSON.parse(event.data);
          console.log("Received WebSocket message:", data);

          if (data.type === "ping") {
            return;
          } else if (data.type === "message_received") {
            setMessages((prev) => [
              ...prev,
              {
                id: data.message_id,
                content: data.message,
                isUser: true,
                mode: "chat",
                intermediate_questions: [],
                charts: [],
              },
            ]);
            setIsLoading(true);
          } else if (data.type === "bot_response" || data.type === "response") {
            setIsLoading(false);
            setMessages((prev) => [
              ...prev,
              {
                id: data.message_id,
                content: data.message || data.content,
                isUser: false,
                mode: "chat",
                intermediate_questions: [],
                kpiAnalysis: data.kpi_analysis[0]?.data,
                charts:
                  data.charts?.map((chart) => ({
                    id: chart.id || Math.random().toString(36).substr(2, 9),
                    chart_type: chart.chart_type,
                    title: chart.title,
                    data:
                      typeof chart.data === "string"
                        ? JSON.parse(chart.data)
                        : chart.data,
                    description: chart.description,
                  })) || [],
              },
            ]);
          } else if (data.type === "clarification") {
            setMessages((prev) => [
              ...prev,
              {
                id: data.message_id,
                content: "",
                isUser: false,
                mode: "chat",
                intermediate_questions: [
                  {
                    id: data.message_id,
                    question: data.question,
                    options: data.options,
                    questionType: "clarification",
                  },
                ],
              },
            ]);
          } else if (data.type === "clarification_response") {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.intermediate_questions?.some(
                  (q) => q.id === data.question_id
                )
                  ? {
                      ...msg,
                      intermediate_questions: msg.intermediate_questions.map(
                        (q) =>
                          q.id === data.question_id
                            ? { ...q, answer: data.answer }
                            : q
                      ),
                    }
                  : msg
              )
            );
          } else if (data.type === "error") {
            setError(data.message);
            setMessages((prev) => prev.slice(0, -1));
          }
          scrollToBottom();
        };

        newWs.onerror = (error) => {
          console.error("WebSocket error:", error);
          setError("WebSocket connection error");
        };

        newWs.onclose = () => {
          console.log("WebSocket disconnected");
          setTimeout(() => {
            const wsUrl = chatApi.getWebSocketUrl(currentSpace.id, chatId);
            const newWs = new WebSocket(wsUrl);
            wsRef.current = newWs;
            setWs(newWs);
          }, 5000);
        };

        wsRef.current = newWs;
        setWs(newWs);
      } catch (err) {
        console.error("Error setting up WebSocket:", err);
        setError("Failed to connect to chat");
        setLoading(false);
      }
    };

    setupWebSocket();
  }, [chatId, currentSpace?.id]);

  useEffect(() => {
    const updateTitle = async () => {
      if (messages.length > 0 && !hasSetTitle && currentSpace?.id) {
        const firstUserMessage = messages.find((msg) => msg.isUser);
        if (firstUserMessage) {
          try {
            const title =
              firstUserMessage.content.slice(0, 50) +
              (firstUserMessage.content.length > 50 ? "..." : "");
            await chatApi.updateChatTitle(currentSpace.id, chatId, title);
            setHasSetTitle(true);
          } catch (error) {
            console.error("Error updating chat title:", error);
          }
        }
      }
    };
    updateTitle();
  }, [messages, hasSetTitle, chatId, currentSpace]);

  const handleAnswerSubmit = (questionId, answer) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "clarification_response",
          message_id: questionId,
          answer: answer,
        })
      );

      setMessages((prev) =>
        prev.map((msg) =>
          msg.intermediate_questions && msg.intermediate_questions.length > 0
            ? {
                ...msg,
                intermediate_questions: msg.intermediate_questions.map((q) =>
                  q.id === questionId ? { ...q, answer } : q
                ),
              }
            : msg
        )
      );
    }
  };

  const handleSendMessage = async (
    message,
    mode = "chat",
    researchMode = false,
    selectedFiles = [],
    selectedLLM
  ) => {
    if (!currentSpace?.id) {
      setError("Please select a space first");
      return;
    }

    const messageData = {
      message,
      mode,
      research_mode: researchMode,
      selected_files: selectedFiles,
      llm: selectedLLM,
    };

    try {
      // If there's no active chat, create one and send the message
      if (!chatId) {
        setLoading(true);
        const newChat = await createChat();

        // Set up WebSocket connection for the new chat
        const wsUrl = chatApi.getWebSocketUrl(currentSpace.id, newChat.id);
        const newWs = new WebSocket(wsUrl);

        newWs.onopen = () => {
          console.log("WebSocket connected for new chat");
          setError(null);
          // Send the message immediately after connection
          newWs.send(JSON.stringify(messageData));
        };

        // Set up other WebSocket handlers
        newWs.onmessage = (event) => {
          const data = JSON.parse(event.data);
          console.log("Received WebSocket message:", data);

          if (data.type === "ping") {
            return;
          } else if (data.type === "message_received") {
            setMessages((prev) => [
              ...prev,
              {
                id: data.message_id,
                content: data.message,
                isUser: true,
                mode: "chat",
                intermediate_questions: [],
                charts: [],
              },
            ]);
            setIsLoading(true);
          } else if (data.type === "bot_response" || data.type === "response") {
            setIsLoading(false);
            setMessages((prev) => [
              ...prev,
              {
                id: data.message_id,
                content: data.message || data.content,
                isUser: false,
                mode: "chat",
                intermediate_questions: [],
                charts:
                  data.charts?.map((chart) => ({
                    id: chart.id || Math.random().toString(36).substr(2, 9),
                    chart_type: chart.chart_type,
                    title: chart.title,
                    data:
                      typeof chart.data === "string"
                        ? JSON.parse(chart.data)
                        : chart.data,
                    description: chart.description,
                  })) || [],
              },
            ]);
          }
          scrollToBottom();
        };

        newWs.onerror = (error) => {
          console.error("WebSocket error:", error);
          setError("WebSocket connection error");
        };

        wsRef.current = newWs;
        setWs(newWs);

        // Navigate to the new chat
        navigate(`/app/chat/${newChat.id}`);
      } else {
        // If there's an active WebSocket connection, send the message
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify(messageData));
        } else {
          setError("Connection lost. Please refresh the page.");
        }
      }
    } catch (err) {
      setError("Failed to send message");
      console.error("Error sending message:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleMouseDown = (e) => {
    e.preventDefault();
    isDraggingRef.current = true;
    dragStartXRef.current = e.clientX;
    initialWidthRef.current = chatWidth;
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    document.body.style.cursor = "col-resize";
  };

  const handleMouseMove = (e) => {
    if (!isDraggingRef.current) return;
    const containerRect = containerRef.current.getBoundingClientRect();
    const deltaX = e.clientX - containerRect.left;
    const newWidth = (deltaX / containerRect.width) * 100;
    setChatWidth(Math.min(Math.max(newWidth, 20), 80));
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
    document.removeEventListener("mousemove", handleMouseMove);
    document.removeEventListener("mouseup", handleMouseUp);
    document.body.style.cursor = "default";
  };

  const handleNewChat = async () => {
    if (!currentSpace?.id) {
      setError("Please select a space first");
      return;
    }

    try {
      setLoading(true);
      const newChat = await createChat();
      navigate(`/app/chat/${newChat.id}`);
    } catch (err) {
      setError("Failed to create new chat");
      console.error("Error creating new chat:", err);
    } finally {
      setLoading(false);
    }
  };

  const navigateToStorage = () => {
    navigate(`/spaces/${currentSpace.id}/storage`);
  };

  const groupMessages = (messages) => {
    return messages.reduce((groups, message, index) => {
      const prevMessage = messages[index - 1];
      const isSameSender = prevMessage && prevMessage.isUser === message.isUser;

      if (isSameSender) {
        const lastGroup = groups[groups.length - 1];
        lastGroup.messages.push(message);
      } else {
        groups.push({
          isUser: message.isUser,
          messages: [message],
        });
      }

      return groups;
    }, []);
  };

  return (
    <div className="flex flex-row h-full relative" ref={containerRef}>
      <div
        ref={chatContainerRef}
        className="flex-1 h-full flex flex-col overflow-hidden relative"
        style={{ width: `${chatWidth}%` }}
      >
        <ChatMessages
          messages={groupMessages(messages)}
          isLoading={isLoading}
          messageEndRef={messageEndRef}
          onAnswerSubmit={handleAnswerSubmit}
        />
        <div className="absolute w-full bottom-0">
          <ChatInput
            ws={ws}
            setError={setError}
            chatId={chatId}
            messages={messages}
            onSendMessage={handleSendMessage}
          />
        </div>
      </div>
      <ResizeHandle onMouseDown={handleMouseDown} />
      <div className="h-full" style={{ width: `${100 - chatWidth}%` }}>
        <Tab />
      </div>
    </div>
  );
};

export default ChatContainer;
