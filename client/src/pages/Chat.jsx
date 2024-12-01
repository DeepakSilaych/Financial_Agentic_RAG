import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ChatContainer from '../components/app/ChatContainer';
import Sidebar from '../components/app/Sidebar';
import { chatApi } from '../utils/api';

const Chat = () => {
  const { id } = useParams();
  const [chat, setChat] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadChat = async () => {
      try {
        const chatData = await chatApi.getChat(id);
        setChat(chatData);
      } catch (err) {
        setError('Failed to load chat');
        console.error('Error loading chat:', err);
      }
    };

    if (id) {
      loadChat();
    }
  }, [id]);

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <>
      <ChatContainer chatId={id} />
    </>
  );
};

export default Chat;
