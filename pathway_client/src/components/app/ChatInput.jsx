import React, { useState, useRef, useEffect } from "react";
import {
  Paperclip,
  ArrowUp,
  Zap,
  Sparkles,
  Target,
  X,
  File,
  Folder,
  ChevronLeft,
  Loader2,
  AlertCircle,
  Image,
  FileText,
  Music,
  Video,
  Archive,
  Search,
} from "lucide-react";
import { chatApi, fileApi } from "../../utils/api";
import * as Dialog from "@radix-ui/react-dialog";
import { useUser } from "../../context/UserContext";
import { format } from "date-fns";
import * as Select from "@radix-ui/react-select";
import { ChevronDown } from "lucide-react";

import { API_BASE_URL } from "../../utils/api";

const LLMSelect = ({ selectedLLM, setSelectedLLM }) => {
  const LLM_OPTIONS = [
    { value: "openai", label: "GPT 4o" },
    { value: "anthropic", label: "Claude Haiku" },
    { value: "mistral", label: "Mistral 8x7B" },
    { value: "llama", label: "Llama 3.1 70B" },
  ];

  return (
    <Select.Root value={selectedLLM}>
      <Select.Trigger
        className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
        aria-label="Select LLM"
      >
        <Select.Value>
          {LLM_OPTIONS.find((option) => option.value === selectedLLM)?.label ||
            "Select LLM"}
        </Select.Value>
        <Select.Icon>
          <ChevronDown size={14} className="text-gray-500" />
        </Select.Icon>
      </Select.Trigger>

      <Select.Portal>
        <Select.Content
          position="popper"
          className="z-50 bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden"
        >
          <Select.Viewport className="p-1">
            {LLM_OPTIONS.map((option) => (
              <Select.Item
                key={option.value}
                value={option.value}
                onClick={(e) => {
                  console.log("yesss");
                  e.stopPropagation();
                  e.preventDefault();
                  setSelectedLLM(option.value);
                }}
                className="px-3 py-2 text-xs text-gray-700 hover:bg-gray-50 cursor-pointer outline-none focus:bg-gray-100 data-[highlighted]:bg-gray-100 transition-colors"
              >
                <Select.ItemText>{option.label}</Select.ItemText>
              </Select.Item>
            ))}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
};

const getFileIcon = (fileName) => {
  const extension = fileName.split(".").pop().toLowerCase();
  switch (extension) {
    case "jpg":
    case "png":
    case "gif":
    case "jpeg":
    case "webp":
      return <Image className="text-green-500" />;
    case "pdf":
    case "doc":
    case "docx":
    case "txt":
    case "md":
      return <FileText className="text-yellow-500" />;
    case "mp3":
    case "wav":
    case "ogg":
      return <Music className="text-purple-500" />;
    case "mp4":
    case "mov":
    case "avi":
    case "webm":
      return <Video className="text-red-500" />;
    case "zip":
    case "rar":
    case "7z":
      return <Archive className="text-orange-500" />;
    default:
      return <File className="text-gray-500" />;
  }
};

const ChatInput = ({
  setError: setParentError,
  chatId,
  messages,
  onSendMessage,
}) => {
  const { currentSpace } = useUser();
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState("slow");
  const [researchMode, setResearchMode] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedLLM, setSelectedLLM] = useState("openai");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isFileDialogOpen, setIsFileDialogOpen] = useState(false);
  const [files, setFiles] = useState([]);
  const [currentPath, setCurrentPath] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [fileError, setFileError] = useState(null);
  const componentRef = useRef();
  const textareaRef = useRef();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        componentRef.current &&
        !componentRef.current.contains(event.target)
      ) {
        setIsExpanded(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  useEffect(() => {
    if (isExpanded && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isExpanded]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (message.trim()) {
      try {
        setIsLoading(true);
        await onSendMessage(
          message.trim(),
          mode,
          researchMode,
          selectedFiles,
          selectedLLM
        );
        setMessage("");
        setSelectedFiles([]);
        setIsExpanded(false);
      } catch (error) {
        setParentError("Failed to send message");
        console.error("Error sending message:", error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const loadFiles = async (path = "") => {
    if (!currentSpace?.id) {
      setFileError("No space selected");
      return;
    }

    try {
      setIsLoadingFiles(true);
      setFileError(null);
      const response = await fetch(
        `${API_BASE_URL}/spaces/${currentSpace.id}/files/${path}`
      );
      if (!response.ok) {
        throw new Error("Failed to load files");
      }
      const data = await response.json();
      setFiles(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Error loading files:", error);
      setFileError("Failed to load files");
      setFiles([]);
    } finally {
      setIsLoadingFiles(false);
    }
  };

  useEffect(() => {
    if (isFileDialogOpen) {
      loadFiles(currentPath);
    } else {
      setFiles([]);
      setFileError(null);
      setCurrentPath("");
      setSearchQuery("");
    }
  }, [isFileDialogOpen, currentPath, currentSpace?.id]);

  const handleFileSelect = (file) => {
    if (!file || !file.name || file.type !== "file") return;

    const filePath = currentPath ? `${currentPath}/${file.name}` : file.name;
    setSelectedFiles((prev) => {
      const isAlreadySelected = prev.includes(filePath);
      if (isAlreadySelected) {
        return prev.filter((path) => path !== filePath);
      } else {
        return [...prev, filePath];
      }
    });
  };

  const handleFolderClick = (folderName) => {
    const newPath = currentPath ? `${currentPath}/${folderName}` : folderName;
    setCurrentPath(newPath);
  };

  const handleNavigateUp = () => {
    if (!currentPath) return;
    const newPath = currentPath.split("/").slice(0, -1).join("/");
    setCurrentPath(newPath);
  };

  const handleRemoveFile = (filePath) => {
    setSelectedFiles((prev) => prev.filter((path) => path !== filePath));
  };

  const FileSelectionDialog = () => (
    <Dialog.Root open={isFileDialogOpen} onOpenChange={setIsFileDialogOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        <Dialog.Content className="fixed top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%] bg-white rounded-xl shadow-xl p-6 w-[800px] max-h-[80vh] flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-4">
              <Dialog.Title className="text-lg font-semibold">
                Select Files
              </Dialog.Title>
              {currentPath && (
                <button
                  onClick={handleNavigateUp}
                  className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors text-gray-600 flex items-center gap-1"
                >
                  <ChevronLeft size={20} />
                  Back
                </button>
              )}
              <div className="text-sm text-gray-500">
                {currentPath || "Root"}
              </div>
            </div>
            <Dialog.Close className="p-2 hover:bg-gray-100 rounded-full transition-colors">
              <X size={20} />
            </Dialog.Close>
          </div>

          <div className="mb-4">
            <div className="relative">
              <input
                type="text"
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                <Search size={18} />
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto min-h-[400px] border rounded-lg">
            {isLoadingFiles ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
              </div>
            ) : fileError ? (
              <div className="flex flex-col items-center justify-center h-full text-red-500 gap-2">
                <AlertCircle size={24} />
                <p>{fileError}</p>
              </div>
            ) : (
              <div className="divide-y">
                {Array.isArray(files) && files.length > 0 ? (
                  files
                    .filter((item) =>
                      item.name
                        .toLowerCase()
                        .includes(searchQuery.toLowerCase())
                    )
                    .map((item, index) => (
                      <div
                        key={index}
                        onClick={() =>
                          item.type === "folder"
                            ? handleFolderClick(item.name)
                            : handleFileSelect(item)
                        }
                        className={`flex items-center justify-between p-3 hover:bg-gray-50 cursor-pointer ${
                          item.type === "file" &&
                          selectedFiles.includes(
                            currentPath
                              ? `${currentPath}/${item.name}`
                              : item.name
                          )
                            ? "bg-blue-50"
                            : ""
                        }`}
                      >
                        <div className="flex items-center gap-3 flex-1">
                          {item.type === "folder" ? (
                            <Folder className="text-blue-500" size={20} />
                          ) : (
                            getFileIcon(item.name)
                          )}
                          <span className="text-sm text-gray-700">
                            {item.name}
                          </span>
                        </div>
                        {item.type === "file" &&
                          selectedFiles.includes(
                            currentPath
                              ? `${currentPath}/${item.name}`
                              : item.name
                          ) && (
                            <div className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                              Selected
                            </div>
                          )}
                      </div>
                    ))
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                    <File size={40} className="mb-2 opacity-50" />
                    <p>No files in this folder</p>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex justify-between items-center mt-4 pt-4 border-t">
            <div className="text-sm text-gray-600">
              {selectedFiles.length} file(s) selected
            </div>
            <div className="flex gap-2">
              <Dialog.Close
                className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                onClick={() => {
                  setSelectedFiles([]);
                  setCurrentPath("");
                }}
              >
                Cancel
              </Dialog.Close>
              <Dialog.Close className="px-4 py-2 text-sm text-white bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors">
                Done
              </Dialog.Close>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );

  return (
    <>
      <div
        ref={componentRef}
        className={`w-full relative mb-4 transition-all duration-500 ease-in-out ${
          isExpanded ? "h-48" : selectedFiles.length > 0 ? "h-28" : "h-16"
        }`}
        onClick={() => setIsExpanded(true)}
      >
        <form
          onSubmit={handleSendMessage}
          className="p-3 max-w-5xl mx-auto bg-white border-2 border-gray-300 rounded-2xl shadow-sm hover:shadow-md transition-all duration-500 h-full"
        >
          <div className="w-full flex flex-col space-y-2 h-full">
            {selectedFiles.length > 0 && (
              <div className="flex flex-wrap gap-2 px-2">
                {selectedFiles.map((filePath, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-1 bg-blue-50 text-blue-700 text-sm px-2 py-1 rounded-lg"
                  >
                    <File size={14} />
                    <span>{filePath.split("/").pop()}</span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveFile(filePath);
                      }}
                      className="ml-1 hover:bg-blue-100 rounded-full p-1"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
                setIsTyping(e.target.value.length > 0);
              }}
              onFocus={() => setIsExpanded(true)}
              placeholder="Ask me anything..."
              className="w-full p-2 bg-gray-50 rounded-xl border-none outline-none text-gray-800 placeholder:text-gray-400 resize-none transition-all duration-500 focus:bg-gray-100"
              style={{ height: isExpanded ? "100px" : "40px" }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(e);
                }
              }}
            />

            <div
              className={`flex items-center justify-between gap-2 transition-all duration-500 ${
                isExpanded
                  ? "opacity-100 max-h-20"
                  : "opacity-0 max-h-0 overflow-hidden"
              }`}
            >
              <div className="flex items-center gap-2">
                <div className="relative">
                  <div className="flex items-center">
                    <span className="mr-2 text-sm text-gray-600">
                      Fast mode:
                    </span>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={mode === "fast"}
                        onChange={() => {
                          setMode(mode === "fast" ? "slow" : "fast");
                          console.log(mode);
                        }}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
                <LLMSelect
                  selectedLLM={selectedLLM}
                  onLLMChange={setSelectedLLM}
                />
                <button
                  type="button"
                  onClick={() => setIsFileDialogOpen(true)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors flex items-center gap-2 text-gray-600 text-sm"
                >
                  <Paperclip size={18} />
                  <span
                    className={
                      selectedFiles.length > 0
                        ? "text-blue-600 font-medium"
                        : ""
                    }
                  >
                    {selectedFiles.length > 0
                      ? `${selectedFiles.length} file(s)`
                      : "Attach files"}
                  </span>
                </button>
              </div>

              <div className="flex items-center gap-2">
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={researchMode}
                    onChange={(e) => setResearchMode(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600" />
                  <span className="ml-2 text-sm font-medium text-gray-700">
                    Research Mode
                  </span>
                </label>
                <button
                  type="submit"
                  disabled={!isTyping || isLoading}
                  className={`p-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-300 ${
                    isTyping && !isLoading
                      ? "bg-blue-600 hover:bg-blue-700 text-white"
                      : isLoading
                      ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                      : "bg-gray-100 text-gray-400 cursor-not-allowed"
                  }`}
                >
                  {isLoading ? (
                    <svg
                      className="animate-spin h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                  ) : (
                    <ArrowUp size={20} />
                  )}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>

      <FileSelectionDialog />
    </>
  );
};

export default ChatInput;
