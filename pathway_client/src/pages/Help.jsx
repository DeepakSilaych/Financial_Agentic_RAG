import React, { useState } from 'react';
import { HelpCircle, Mail, MessageCircle, Phone, ChevronDown, ChevronUp, Search } from 'lucide-react';

const FAQItem = ({ question, answer }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border-b border-gray-200 last:border-0">
      <button
        className="w-full py-4 flex items-center justify-between text-left"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="font-medium text-gray-900">{question}</span>
        {isOpen ? (
          <ChevronUp className="text-gray-500" size={20} />
        ) : (
          <ChevronDown className="text-gray-500" size={20} />
        )}
      </button>
      {isOpen && (
        <div className="pb-4 text-gray-600 text-sm">
          {answer}
        </div>
      )}
    </div>
  );
};

const Help = () => {
  const faqs = [
    {
      question: "How do I start a new chat?",
      answer: "Click the 'New Chat' button in the top-left corner of the screen or use the keyboard shortcut ⌘ + N (Mac) or Ctrl + N (Windows)."
    },
    {
      question: "Can I upload files to the chat?",
      answer: "Yes, you can upload files by clicking the attachment icon or dragging and dropping files into the chat window. We support various file formats including documents, images, and PDFs."
    },
    {
      question: "How do I customize my notification settings?",
      answer: "Go to Settings > Notifications to customize your notification preferences. You can enable/disable different types of notifications and choose how you want to receive them."
    },
    {
      question: "Is my data secure?",
      answer: "Yes, we use industry-standard encryption to protect your data. All communications are encrypted end-to-end, and we never share your information with third parties."
    },
    {
      question: "How can I search through my chat history?",
      answer: "Use the search bar at the top of the screen or press ⌘ + K (Mac) or Ctrl + K (Windows) to quickly search through your conversations."
    }
  ];

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      {/* Search Bar */}
      <div className="mb-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search help articles..."
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        {/* Left Column - Quick Help */}
        <div className="md:col-span-2 space-y-6">
          <section>
            <h2 className="text-xl font-semibold mb-4">Frequently Asked Questions</h2>
            <div className="bg-white rounded-lg shadow-sm border border-gray-100">
              {faqs.map((faq, index) => (
                <FAQItem key={index} question={faq.question} answer={faq.answer} />
              ))}
            </div>
          </section>
        </div>

        {/* Right Column - Contact Options */}
        <div className="space-y-4">
          <section>
            <h2 className="text-xl font-semibold mb-4">Need More Help?</h2>
            <div className="space-y-4">
              <a
                href="#"
                className="block p-4 bg-white rounded-lg shadow-sm border border-gray-100 hover:border-blue-500 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <MessageCircle className="text-blue-500" size={20} />
                  <div>
                    <h3 className="font-medium">Live Chat</h3>
                    <p className="text-sm text-gray-600">Available 24/7</p>
                  </div>
                </div>
              </a>
              
              <a
                href="mailto:support@example.com"
                className="block p-4 bg-white rounded-lg shadow-sm border border-gray-100 hover:border-blue-500 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <Mail className="text-blue-500" size={20} />
                  <div>
                    <h3 className="font-medium">Email Support</h3>
                    <p className="text-sm text-gray-600">Get help via email</p>
                  </div>
                </div>
              </a>

              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h3 className="font-medium mb-2">Support Hours</h3>
                <p className="text-sm text-gray-600">
                  Monday - Friday<br />
                  9:00 AM - 6:00 PM EST
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default Help;
