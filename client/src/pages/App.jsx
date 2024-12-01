import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ChatContainer from '../components/app/ChatContainer';
import Sidebar from '../components/app/Sidebar';
import { chatApi } from '../utils/api';

const App = () => {
  const [chat, setChat] = useState(null);
  const [error, setError] = useState(null);

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
      <ChatContainer/>
  );
};

export default App;
