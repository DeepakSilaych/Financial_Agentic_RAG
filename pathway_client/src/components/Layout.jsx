import React, { useState, useEffect } from "react";
import { Outlet, useLocation, useNavigate, Link } from "react-router-dom";
import {
  Menu,
  PanelLeftClose,
  PanelLeft,
  Search,
  Bell,
  HelpCircle,
  FileText,
  MessageSquare,
  ChevronRight,
  UserCircle,
  Plus,
  X,
} from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";
import Sidebar from "./app/Sidebar";
import SpaceSwitcher from "./space/SpaceSwitcher";
import SpaceMembers from "./space/SpaceMembers";
import { useUser } from "../context/UserContext";
import { spaceApi } from "../utils/api";
import { motion } from "framer-motion";
import ChatInput from "./app/ChatInput";

import { API_BASE_URL } from "../utils/api";

const getBreadcrumbs = (pathname) => {
  const parts = pathname.split("/").filter(Boolean);
  if (parts.length === 0) return [{ name: "Chat", path: "/chat" }];

  return parts.map((part, index) => {
    const path = "/" + parts.slice(0, index + 1).join("/");
    let name = part.charAt(0).toUpperCase() + part.slice(1);
    if (name.length === 24 && /^[0-9a-f]{24}$/.test(part)) {
      name = "Chat Session";
    }
    return { name, path };
  });
};

const NewChatDialog = ({ isOpen, onOpenChange, currentSpaceId }) => {
  const navigate = useNavigate();
  const [message, setMessage] = useState("");

  return (
    <Dialog.Root open={isOpen} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        <Dialog.Content className="fixed top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%] bg-white rounded-xl p-6 w-[95vw] max-w-[650px] shadow-lg">
          <Dialog.Title className="text-xl font-semibold mb-4 text-gray-800">
            New Chat
          </Dialog.Title>
          <form
            className="mb-4 flex flex-col space-y-4 justify-center"
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                const response = await fetch(
                  `${API_BASE_URL}/spaces/${currentSpaceId}/chats`,
                  {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                      space_id: currentSpaceId,
                      title:
                        message.slice(0, 50) +
                        (message.length > 50 ? "..." : ""),
                      first_message: message,
                    }),
                  }
                );

                if (!response.ok) {
                  throw new Error("Failed to create chat");
                }

                const newChat = await response.json();
                onOpenChange(false);

                // Wait a bit for the chat to be fully created before navigating
                await new Promise((resolve) => setTimeout(resolve, 500));
                navigate(`/app/chat/${newChat.id}`);
              } catch (error) {
                console.error("Error creating chat:", error);
              }
            }}
          >
            <input
              type="text"
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
              }}
              placeholder="Enter chat title..."
              className="w-full p-2 bg-gray-50 rounded-xl border-none outline-none text-gray-800 placeholder:text-gray-400 resize-none transition-all duration-500 focus:bg-gray-100"
              style={{ height: "40px" }}
            />
            <button className="bg-bluecolor text-white px-6 py-2 rounded-md ml-auto">
              Create
            </button>
          </form>
          <Dialog.Close asChild>
            <button
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
              aria-label="Close"
            >
              <X size={20} />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

const Layout = () => {
  const [isCreateSpaceOpen, setIsCreateSpaceOpen] = useState(false);
  const [isNewChatDialogOpen, setIsNewChatDialogOpen] = useState(false);
  const [newSpaceName, setNewSpaceName] = useState("");
  const [newSpaceDescription, setNewSpaceDescription] = useState("");
  const [isCreatingSpace, setIsCreatingSpace] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const { user, setUser, currentSpace } = useUser();
  const navigate = useNavigate();

  const location = useLocation();
  const [isSidebarOpen, setSidebarOpen] = useState(true);

  const breadcrumbs = getBreadcrumbs(location.pathname);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.key === "k") {
        e.preventDefault();
        setIsNewChatDialogOpen(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (!user) {
    navigate("/login");
  }

  const handleCreateSpace = async (e) => {
    e.preventDefault();
    if (!newSpaceName.trim() || !currentSpace) return;

    setIsCreatingSpace(true);
    try {
      await spaceApi.createSpace({
        name: newSpaceName.trim(),
        space_id: currentSpace.id,
        description: newSpaceDescription.trim() || null,
      });
      setNewSpaceName("");
      setNewSpaceDescription("");
      setIsCreateSpaceOpen(false);
      // Refresh spaces in the parent component
      if (currentSpace) {
        await fetchSpaces(currentSpace.id);
      }
    } catch (error) {
      console.error("Error creating space:", error);
      // You might want to show an error message to the user here
    } finally {
      setIsCreatingSpace(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="h-screen relative flex bg-graycolor overflow-hidden bg-custom-gray"
    >
      <motion.div
        initial={{ x: -300, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: -300, opacity: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        <aside
          className={`
            fixed lg:relative inset-y-0 left-0 
            transform transition-all duration-300 ease-in-out
            ${
              isSidebarOpen
                ? "translate-x-0 w-72"
                : "-translate-x-full lg:translate-x-0 lg:w-20"
            }
          `}
        >
          <Sidebar isCollapsed={!isSidebarOpen} />
        </aside>
      </motion.div>

      <motion.main
        initial={{ y: 1000, opacity: 1 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 100, opacity: 0 }}
        transition={{ duration: 0.5 }}
        className="flex-1 flex flex-col mt-8 mr-6 transition-all duration-500 ease-in-out hover:shadow-none bg-white shadow-xl border-2 border-gray-200 rounded-t-xl min-w-0"
      >
        <div className="h-16 border-b flex items-center justify-between px-4 transition-all duration-700 ease-in-out">
          <div className="flex items-center space-x-4 transition-all duration-500 ease-in-out">
            <button
              onClick={() => setSidebarOpen(!isSidebarOpen)}
              className="lg:hidden text-gray-500 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 p-2 rounded-md"
            >
              <Menu
                size={20}
                className="transition-transform duration-200 ease-in-out"
              />
            </button>

            <button
              onClick={() => setSidebarOpen(!isSidebarOpen)}
              className={`
                hidden lg:flex items-center justify-center w-8 h-8 rounded-lg
                text-gray-500 hover:text-gray-600 hover:bg-gray-100
                focus:outline-none focus:ring-2 focus:ring-blue-500
                transition-all duration-200 ease-in-out
                ${isSidebarOpen ? "transform rotate-0" : "transform rotate-180"}
              `}
              title={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
            >
              {isSidebarOpen ? (
                <PanelLeftClose
                  size={18}
                  className="transition-transform duration-200"
                />
              ) : (
                <PanelLeft
                  size={18}
                  className="transition-transform duration-200"
                />
              )}
            </button>

            <nav className="hidden md:flex items-center space-x-1">
              {breadcrumbs.map((crumb, index) => (
                <React.Fragment key={crumb.path}>
                  {index > 0 && (
                    <ChevronRight size={16} className="text-gray-400" />
                  )}
                  <a
                    href={crumb.path}
                    className="text-sm text-gray-600 hover:text-blue-600 font-medium"
                  >
                    {crumb.name}
                  </a>
                </React.Fragment>
              ))}
            </nav>
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Link
                to="/app/documentation"
                className="p-2 text-gray-500 hover:text-gray-600 hover:bg-gray-100 rounded-lg group relative"
                title="Documentation"
              >
                <FileText size={18} />
                <span className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 text-white px-2 py-1 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                  Docs
                </span>
              </Link>
              <Link
                to="/app/help"
                className="p-2 text-gray-500 hover:text-gray-600 hover:bg-gray-100 rounded-lg group relative"
                title="Help & Support"
              >
                <HelpCircle size={18} />
                <span className="absolute -bottom-8 left-1/2 transform -translate-x-1/2  text-white px-2 py-1 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                  Help
                </span>
              </Link>
              <Link
                to="/app/notifications"
                className="p-2 text-gray-500 hover:text-gray-600 hover:bg-gray-100 rounded-lg group relative"
                title="Notifications"
              >
                <Bell size={18} />
                <span className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 text-white px-2 py-1 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                  Notifications
                </span>
              </Link>
            </div>

            <SpaceSwitcher />
            <SpaceMembers />

            <button className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500">
              <UserCircle
                size={18}
                className="text-gray-500 hover:text-gray-600"
              />
              <span className="text-sm font-medium text-gray-700">
                {user.name}
              </span>
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          <Outlet />
        </div>
      </motion.main>

      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 lg:hidden z-20"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {isCreateSpaceOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Create New Space</h2>
              <button
                onClick={() => setIsCreateSpaceOpen(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCreateSpace}>
              <div className="mb-4">
                <label
                  htmlFor="spaceName"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Space Name *
                </label>
                <input
                  type="text"
                  id="spaceName"
                  value={newSpaceName}
                  onChange={(e) => setNewSpaceName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter space name"
                  required
                />
              </div>
              <div className="mb-6">
                <label
                  htmlFor="spaceDescription"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Description (optional)
                </label>
                <textarea
                  id="spaceDescription"
                  value={newSpaceDescription}
                  onChange={(e) => setNewSpaceDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter space description"
                  rows={3}
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setIsCreateSpaceOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreatingSpace || !newSpaceName.trim()}
                  className={`px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md
                    ${
                      isCreatingSpace || !newSpaceName.trim()
                        ? "opacity-50 cursor-not-allowed"
                        : "hover:bg-blue-700"
                    }`}
                >
                  {isCreatingSpace ? "Creating..." : "Create Space"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      <NewChatDialog
        isOpen={isNewChatDialogOpen}
        onOpenChange={setIsNewChatDialogOpen}
        currentSpaceId={currentSpace?.id}
      />
    </motion.div>
  );
};

export default Layout;
