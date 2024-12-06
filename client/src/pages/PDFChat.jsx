import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import Split from 'react-split';
import PDFRenderer from '../components/storage/PDFRenderer';
import ChatContainer from '../components/app/ChatContainer';
import { chatApi } from '../utils/api';
import { useUser } from '../context/UserContext';
import toast from 'react-hot-toast';

export default function PDFChat() {
  const location = useLocation();
  const { currentSpace } = useUser();
  const [pdfUrl, setPdfUrl] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [notes, setNotes] = useState([]);
  const [chatId, setChatId] = useState(null);
  const [showNotes, setShowNotes] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [splitSizes, setSplitSizes] = useState([70, 30]);
  const [newNote, setNewNote] = useState('');

  useEffect(() => {
    const url = localStorage.getItem('pdf_req_url');
    if (url) {
      setPdfUrl(url);
      const filename = decodeURIComponent(url.split('path=').pop());
      loadNotes(filename);
    }
  }, []);

  const loadNotes = (filename) => {
    const storedNotes = JSON.parse(localStorage.getItem('pdf_notes') || '{}');
    setNotes(storedNotes[filename] || []);
  };

  const handleCreateChat = async () => {
    try {
      setIsLoading(true);
      if (!currentSpace?.id) {
        throw new Error('Please select a space first');
      }

      const chat = await chatApi.createChat(currentSpace.id);
      setChatId(chat.id);
      setShowChat(true);
      
      if (showNotes) {
        setShowNotes(false);
      }
    } catch (error) {
      console.error('Error creating chat:', error);
      toast.error(error.message || 'Failed to create chat. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleNotes = () => {
    setShowNotes(!showNotes);
    if (showChat) {
      setShowChat(false);
    }
  };

  const toggleChat = () => {
    if (!showChat && !chatId) {
      handleCreateChat();
    } else {
      setShowChat(!showChat);
      if (showNotes) {
        setShowNotes(false);
      }
    }
  };

  const handleAddNote = () => {
    if (newNote.trim()) {
      const updatedNotes = [...notes, { id: Date.now(), text: newNote, created_at: new Date().toISOString() }];
      setNotes(updatedNotes);
      setNewNote('');

      const filename = decodeURIComponent(pdfUrl.split('path=').pop());
      const storedNotes = JSON.parse(localStorage.getItem('pdf_notes') || '{}');
      storedNotes[filename] = updatedNotes;
      localStorage.setItem('pdf_notes', JSON.stringify(storedNotes));
    }
  };

  return (
    <div className="h-full bg-gray-100 overflow-hidden">
      <div className="h-full p-4">
        <div className="flex flex-col h-full">
          <div className="flex justify-end gap-2 mb-4">
            <button
              onClick={toggleNotes}
              className={`px-4 py-2 rounded-lg font-medium transition-colors duration-200 ${
                showNotes
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {showNotes ? 'Hide Notes' : 'Show Notes'}
            </button>
            <button
              onClick={toggleChat}
              disabled={isLoading}
              className={`px-4 py-2 rounded-lg font-medium transition-colors duration-200 ${
                showChat
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              } disabled:bg-gray-300 disabled:cursor-not-allowed`}
            >
              {isLoading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating Chat...
                </span>
              ) : showChat ? 'Hide Chat' : 'Start Chat'}
            </button>
          </div>

          {(showNotes || showChat) ? (
            <Split 
              sizes={splitSizes}
              minSize={300}
              expandToMin={false}
              gutterSize={10}
              gutterAlign="center"
              snapOffset={30}
              dragInterval={1}
              direction="horizontal"
              cursor="col-resize"
              className="flex gap-0 flex-1 min-h-0 split-parent"
              onDragEnd={sizes => setSplitSizes(sizes)}
            >
              <div className="overflow-auto split-child">
                {pdfUrl && (
                  <PDFRenderer
                    pdf={pdfUrl}
                    setPage={setCurrentPage}
                  />
                )}
              </div>

              <div className="overflow-auto split-child">
                {showNotes && (
                  <div className="h-full bg-white rounded-lg shadow flex flex-col min-h-0">
                    <h2 className="text-xl font-semibold p-4">Notes</h2>
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                      {notes.map((note) => (
                        <div key={note.id} className="bg-gray-50 p-4 rounded-lg">
                          <p className="whitespace-pre-wrap">{note.text}</p>
                          <div className="text-sm text-gray-500 mt-2">
                            Created: {new Date(note.created_at).toLocaleString()}
                          </div>
                        </div>
                      ))}
                      {notes.length === 0 && (
                        <div className="text-center text-gray-500">
                          No notes found for this PDF
                        </div>
                      )}
                    </div>
                    <div className="p-4 border-t">
                      <textarea
                        value={newNote}
                        onChange={(e) => setNewNote(e.target.value)}
                        placeholder="Add a new note..."
                        className="w-full p-2 border rounded-lg"
                        rows="3"
                      />
                      <button
                        onClick={handleAddNote}
                        className="mt-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                      >
                        Add Note
                      </button>
                    </div>
                  </div>
                )}

                {showChat && (
                  <div className="h-full bg-white rounded-lg shadow min-h-0">
                    {chatId && <ChatContainer chatId={chatId} />}
                  </div>
                )}
              </div>
            </Split>
          ) : (
            <div className="flex-1 min-h-0">
              {pdfUrl && (
                <PDFRenderer
                  pdf={pdfUrl}
                  setPage={setCurrentPage}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}