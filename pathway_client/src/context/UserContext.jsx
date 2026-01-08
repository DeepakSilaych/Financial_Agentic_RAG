import React, { createContext, useContext, useState, useEffect } from "react";
import { spaceApi, chatApi, authApi } from "../utils/api";

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const [spaces, setSpaces] = useState([]);
  const [currentSpace, setCurrentSpace] = useState(null);
  const [spaceMembers, setSpaceMembers] = useState([]);

  const [chats, setChats] = useState([]);
  const [currentChat, setCurrentChat] = useState(null);

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (user) {
      fetchSpaces();
    }
  }, [user]);

  useEffect(() => {
    if (currentSpace?.id) {
      fetchSpaceMembers(currentSpace.id);
      fetchChats(currentSpace.id);
    } else {
      setChats([]);
      setCurrentChat(null);
    }
  }, [currentSpace]);

  const checkAuth = async () => {
    try {
      const storedUser = localStorage.getItem("finsight_user");
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      }
      setLoading(false);
    } catch (error) {
      console.error("Auth check failed:", error);
      localStorage.removeItem("finsight_user");
      setLoading(false);
    }
  };

  const fetchSpaces = async () => {
    if (!user) return;

    try {
      const spacesData = await spaceApi.getSpaces();
      setSpaces(spacesData);
      if (spacesData.length > 0 && !currentSpace) {
        setCurrentSpace(spacesData[0]);
      }
    } catch (error) {
      console.error("Failed to fetch spaces:", error);
    }
  };

  const fetchSpaceMembers = async (spaceId) => {
    if (!user || !spaceId) return;

    try {
      // For development, using hardcoded space members
      const membersData = [
        {
          id: "1",
          name: "John Doe",
          avatar: "J",
          role: "admin",
          status: "online",
        },
        {
          id: "2",
          name: "Jane Doe",
          avatar: "J",
          role: "member",
          status: "offline",
        },
      ];
      setSpaceMembers(membersData);
    } catch (error) {
      console.error("Failed to fetch space members:", error);
    }
  };

  const fetchChats = async (spaceId) => {
    if (!user || !spaceId) return;

    try {
      const chatsData = await chatApi.getAllChats(spaceId);
      setChats(chatsData);
      if (chatsData.length > 0 && !currentChat) {
        setCurrentChat(chatsData[0]);
      }
    } catch (error) {
      console.error("Failed to fetch chats:", error);
    }
  };

  const createChat = async () => {
    if (!currentSpace?.id) {
      throw new Error("No space selected");
    }

    try {
      const newChat = await chatApi.createChat(currentSpace.id);
      setChats((prevChats) => [...prevChats, newChat]);
      setCurrentChat(newChat);
      return newChat;
    } catch (error) {
      console.error("Failed to create chat:", error);
      throw error;
    }
  };

  const updateChatTitle = async (chatId, title) => {
    if (!currentSpace?.id) {
      throw new Error("No space selected");
    }

    try {
      const updatedChat = await chatApi.updateChatTitle(
        currentSpace.id,
        chatId,
        title
      );
      setChats((prevChats) =>
        prevChats.map((chat) => (chat.id === chatId ? updatedChat : chat))
      );
      if (currentChat?.id === chatId) {
        setCurrentChat(updatedChat);
      }
      return updatedChat;
    } catch (error) {
      console.error("Failed to update chat title:", error);
      throw error;
    }
  };

  const getChat = async (chatId) => {
    if (!currentSpace?.id) {
      throw new Error("No space selected");
    }

    try {
      const chat = await chatApi.getChat(currentSpace.id, chatId);
      return chat;
    } catch (error) {
      console.error("Failed to get chat:", error);
      throw error;
    }
  };

  const login = async (email, password) => {
    try {
      const response = await authApi.login(email, password);
      const userData = response.user;
      localStorage.setItem("finsight_user", JSON.stringify(userData));
      setUser(userData);
      return { success: true };
    } catch (error) {
      console.error("Login failed:", error);
      const message = error.response?.data?.detail || "Invalid email or password";
      return { success: false, error: message };
    }
  };

  const signup = async (name, email, password) => {
    try {
      const response = await authApi.signup(name, email, password);
      const userData = response.user;
      localStorage.setItem("finsight_user", JSON.stringify(userData));
      setUser(userData);
      return { success: true };
    } catch (error) {
      console.error("Signup failed:", error);
      const message = error.response?.data?.detail || "Registration failed";
      return { success: false, error: message };
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error("Logout error:", error);
    }
    localStorage.removeItem("finsight_user");
    setUser(null);
    setSpaces([]);
    setCurrentSpace(null);
    setSpaceMembers([]);
    setChats([]);
    setCurrentChat(null);
  };

  const value = {
    user,
    loading,
    login,
    signup,
    logout,

    spaces,
    currentSpace,
    spaceMembers,

    setCurrentSpace,

    chats,
    currentChat,
    setCurrentChat,

    fetchSpaces,
    fetchSpaceMembers,
    fetchChats,

    createChat,
    updateChatTitle,
    getChat,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
};

export default UserContext;
