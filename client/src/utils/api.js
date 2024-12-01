import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor to handle data extraction
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Chat related API calls
export const chatApi = {
  // Create a new chat session
  createChat: async () => {
    try {
      return await api.post('/chats/');
    } catch (error) {
      console.error('Error creating chat:', error);
      throw error;
    }
  },

  // Get all chat sessions
  getAllChats: async () => {
    try {
      return await api.get('/chats/');
    } catch (error) {
      console.error('Error fetching chats:', error);
      throw error;
    }
  },

  // Get a specific chat session
  getChat: async (chatId) => {
    try {
      return await api.get(`/chats/${chatId}`);
    } catch (error) {
      console.error(`Error fetching chat ${chatId}:`, error);
      throw error;
    }
  },

  // Get WebSocket URL for chat
  getWebSocketUrl: (chatId) => `${WS_BASE_URL}/ws/${chatId}`,
};

// File related API calls
export const fileApi = {
  // Upload a file
  uploadFile: async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      return await api.post('/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
    } catch (error) {
      console.error('Error uploading file:', error);
      throw error;
    }
  },

  // List all files
  listFiles: async () => {
    try {
      return await api.get('/files/');
    } catch (error) {
      console.error('Error listing files:', error);
      throw error;
    }
  },

  // Delete a file
  deleteFile: async (filename) => {
    try {
      return await api.delete(`/files/${filename}`);
    } catch (error) {
      console.error(`Error deleting file ${filename}:`, error);
      throw error;
    }
  },
};
