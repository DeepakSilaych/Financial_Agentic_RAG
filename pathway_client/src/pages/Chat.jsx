import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ChatContainer from '../components/app/ChatContainer';
import Sidebar from '../components/app/Sidebar';
import { chatApi } from '../utils/api';
import { useUser } from '../context/UserContext';

const Chat = () => {
  const { id } = useParams();
  const { currentSpace } = useUser();
  const [chat, setChat] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadChat = async () => {
      try {
        if (!currentSpace?.id || !id) {
          // Don't show error, just wait for space and chat id
          return;
        }
        const chatData = await chatApi.getChat(currentSpace.id, id);
        console.log('Loaded chat:', chatData);
        setChat(chatData);
      } catch (err) {
        setError('Failed to load chat');
        console.error('Error loading chat:', err);
      }
    };

    loadChat();
  }, [id, currentSpace]);

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <>
      {id && <ChatContainer chatId={id} />}
    </>
  );
};

export default Chat;
