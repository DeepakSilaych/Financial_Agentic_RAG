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
  createChat: async (spaceId) => {
    try {
      return await api.post(`/spaces/${spaceId}/chats/`, { space_id: spaceId });
    } catch (error) {
      console.error('Error creating chat:', error);
      throw error;
    }
  },

  // Get all chat sessions for a space
  getAllChats: async (spaceId) => {
    try {
      const chats = await api.get(`/spaces/${spaceId}/chats/`);
      // Transform chart data for each message
      return chats.map(chat => ({
        ...chat,
        messages: chat.messages?.map(msg => ({
          ...msg,
          charts: msg.charts?.map(chart => ({
            ...chart,
            data: typeof chart.data === 'string' ? JSON.parse(chart.data) : chart.data
          }))
        }))
      }));
    } catch (error) {
      console.error('Error fetching chats:', error);
      throw error;
    }
  },

  // Get a specific chat session and its messages
  getChat: async (spaceId, chatId) => {
    try {
      const chat = await api.get(`/spaces/${spaceId}/chats/${chatId}`);
      const history = await api.get(`/spaces/${spaceId}/chats/${chatId}/history`);

      // Transform chart data for each message
      const transformedHistory = history.map(msg => ({
        ...msg,
        charts: msg.charts?.map(chart => ({
          ...chart,
          data: typeof chart.data === 'string' ? JSON.parse(chart.data) : chart.data
        }))
      }));

      return { ...chat, messages: transformedHistory };
    } catch (error) {
      console.error(`Error fetching chat ${chatId}:`, error);
      throw error;
    }
  },

  // Update chat title
  updateChatTitle: async (spaceId, chatId, title) => {
    try {
      return await api.patch(`/spaces/${spaceId}/chats/${chatId}`, { title });
    } catch (error) {
      console.error('Error updating chat title:', error);
      throw error;
    }
  },

  // Get WebSocket URL for chat
  getWebSocketUrl: (spaceId, chatId) => `${WS_BASE_URL}/ws/${spaceId}/${chatId}`,

  // Handle WebSocket message processing
  processWebSocketMessage: (message) => {
    // Parse chart data if present
    if (message.charts) {
      message.charts = message.charts.map(chart => ({
        ...chart,
        data: typeof chart.data === 'string' ? JSON.parse(chart.data) : chart.data
      }));
    }
    return message;
  }
};

// Space related API calls
export const spaceApi = {
  // Get all spaces
  getSpaces: async () => {
    try {
      return await api.get('/spaces/');
    } catch (error) {
      console.error('Error fetching spaces:', error);
      throw error;
    }
  },

  // Create a new space
  createSpace: async (spaceData) => {
    try {
      return await api.post('/spaces/', spaceData);
    } catch (error) {
      console.error('Error creating space:', error);
      throw error;
    }
  },

  // Get a specific space
  getSpace: async (spaceId) => {
    try {
      return await api.get(`/spaces/${spaceId}`);
    } catch (error) {
      console.error(`Error fetching space ${spaceId}:`, error);
      throw error;
    }
  },

  // Update a space
  updateSpace: async (spaceId, spaceData) => {
    try {
      return await api.patch(`/spaces/${spaceId}`, spaceData);
    } catch (error) {
      console.error(`Error updating space ${spaceId}:`, error);
      throw error;
    }
  },

  // Delete a space
  deleteSpace: async (spaceId) => {
    try {
      return await api.delete(`/spaces/${spaceId}`);
    } catch (error) {
      console.error(`Error deleting space ${spaceId}:`, error);
      throw error;
    }
  },
};

// File related API calls
export const fileApi = {
  // List files and folders in a path
  fetchFiles: async (spaceId, path = '') => {
    try {
      const response = await api.get(`/spaces/${spaceId}/files/${path}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching files:', error);
      throw error;
    }
  },

  // Create a new folder
  addFolder: async (spaceId, path = '', name) => {
    try {
      const response = await api.post(`/spaces/${spaceId}/files/${path}`, { name });
      return response.data;
    } catch (error) {
      console.error('Error creating folder:', error);
      throw error;
    }
  },

  // Delete a file or folder
  deleteItem: async (spaceId, path = '', name) => {
    try {
      const response = await api.delete(`/spaces/${spaceId}/files/${path}`, {
        data: name,
        headers: { 'Content-Type': 'application/json' }
      });
      return response.data;
    } catch (error) {
      console.error('Error deleting item:', error);
      throw error;
    }
  },

  // Upload a file
  uploadFile: async (file, spaceId, path = '') => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post(`/spaces/${spaceId}/files/${path}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading file:', error);
      throw error;
    }
  },

  // Download a file
  downloadFile: async (spaceId, path = '', filename) => {
    try {
      const response = await api.get(`/spaces/${spaceId}/files/${filename}`, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('Error downloading file:', error);
      throw error;
    }
  }
};

// Auto-completion related API calls
export const autoCompleteApi = {
  // Get auto-completion suggestions
  getSuggestions: async (query) => {
    try {
      return await api.post('/api/auto-complete', { query });
    } catch (error) {
      console.error('Error getting auto-completion suggestions:', error);
      throw error;
    }
  },
};