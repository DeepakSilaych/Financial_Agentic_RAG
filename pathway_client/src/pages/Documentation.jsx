import React from 'react';
import { Book, Code, Settings, Zap, Search } from 'lucide-react';

const Documentation = () => {
  return (
    <div className="container mx-auto px-4 py-6 max-w-5xl">
      {/* Search Bar */}
      <div className="mb-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search documentation..."
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="space-y-8">
        {/* Getting Started */}
        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Zap className="mr-2 text-blue-500" size={20} />
            Getting Started
          </h2>
          <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
            <div className="prose prose-sm max-w-none">
              <h3 className="text-lg font-medium mb-2">Quick Start Guide</h3>
              <ol className="list-decimal list-inside space-y-2 text-gray-600">
                <li>Create a new chat by clicking the "New Chat" button</li>
                <li>Type your message or query in the input field</li>
                <li>Use the toolbar to format your message or add attachments</li>
                <li>Press Enter or click the send button to start the conversation</li>
              </ol>
            </div>
          </div>
        </section>

        {/* Features */}
        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Code className="mr-2 text-blue-500" size={20} />
            Key Features
          </h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
              <h3 className="text-lg font-medium mb-2">Smart Conversations</h3>
              <ul className="list-disc list-inside text-gray-600 text-sm space-y-1">
                <li>Natural language processing</li>
                <li>Context-aware responses</li>
                <li>Multi-turn conversations</li>
                <li>Real-time suggestions</li>
              </ul>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
              <h3 className="text-lg font-medium mb-2">File Handling</h3>
              <ul className="list-disc list-inside text-gray-600 text-sm space-y-1">
                <li>Multiple file formats support</li>
                <li>Drag and drop uploads</li>
                <li>File preview</li>
                <li>Secure storage</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Configuration */}
        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Settings className="mr-2 text-blue-500" size={20} />
            Configuration
          </h2>
          <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
            <div className="prose prose-sm max-w-none">
              <h3 className="text-lg font-medium mb-2">Customization Options</h3>
              <div className="text-sm text-gray-600 space-y-2">
                <p>Access the settings panel to customize your experience:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Theme preferences (Light/Dark mode)</li>
                  <li>Notification settings</li>
                  <li>Language preferences</li>
                  <li>Privacy settings</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Keyboard Shortcuts */}
        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Book className="mr-2 text-blue-500" size={20} />
            Keyboard Shortcuts
          </h2>
          <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <h3 className="text-lg font-medium mb-2">Navigation</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">New Chat</span>
                    <kbd className="px-2 py-1 bg-gray-100 rounded">⌘ + N</kbd>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Search</span>
                    <kbd className="px-2 py-1 bg-gray-100 rounded">⌘ + K</kbd>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="text-lg font-medium mb-2">Editor</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Send Message</span>
                    <kbd className="px-2 py-1 bg-gray-100 rounded">↵</kbd>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">New Line</span>
                    <kbd className="px-2 py-1 bg-gray-100 rounded">⇧ + ↵</kbd>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Documentation;
