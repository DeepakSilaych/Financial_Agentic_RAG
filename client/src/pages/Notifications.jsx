import React, { useState } from 'react';
import { Bell, MessageSquare, UserPlus, AlertCircle, Check, X, Clock } from 'lucide-react';

const NotificationItem = ({ notification, onMarkAsRead, onRemove }) => {
  const { type, title, content, time, read } = notification;

  const getIcon = () => {
    switch (type) {
      case 'message':
        return <MessageSquare className="w-5 h-5 text-blue-500" />;
      case 'user':
        return <UserPlus className="w-5 h-5 text-green-500" />;
      case 'alert':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Bell className="w-5 h-5 text-gray-500" />;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${read ? 'border-gray-100' : 'border-l-4 border-l-blue-500 border-y border-r'}`}>
      <div className="p-4">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 mt-1">{getIcon()}</div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium text-gray-900">{title}</p>
              <div className="flex items-center gap-2">
                <time className="text-xs text-gray-500 whitespace-nowrap">{time}</time>
              </div>
            </div>
            <p className="mt-1 text-sm text-gray-600 line-clamp-2">{content}</p>
          </div>
        </div>
        <div className="mt-3 flex items-center justify-end gap-2">
          <button
            onClick={() => onMarkAsRead(notification.id)}
            className="text-xs text-gray-600 hover:text-blue-600 flex items-center gap-1"
          >
            <Check size={14} />
            {read ? 'Mark as unread' : 'Mark as read'}
          </button>
          <button
            onClick={() => onRemove(notification.id)}
            className="text-xs text-gray-600 hover:text-red-600 flex items-center gap-1"
          >
            <X size={14} />
            Remove
          </button>
        </div>
      </div>
    </div>
  );
};

const Notifications = () => {
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: 'message',
      title: 'New message from Support Team',
      content: 'Your recent inquiry has been addressed. Please check your messages for our response.',
      time: '5 minutes ago',
      read: false,
    },
    {
      id: 2,
      type: 'user',
      title: 'Team Invitation',
      content: 'John Doe has invited you to collaborate on Project X. Click here to view and respond to the invitation.',
      time: '1 hour ago',
      read: false,
    },
    {
      id: 3,
      type: 'alert',
      title: 'System Update Scheduled',
      content: 'A system maintenance is scheduled for tonight at 2 AM EST. The service may be unavailable for up to 30 minutes.',
      time: '2 hours ago',
      read: true,
    },
    {
      id: 4,
      type: 'message',
      title: 'File Shared',
      content: 'Sarah Smith shared a document "Q4 Report.pdf" with you.',
      time: '3 hours ago',
      read: true,
    },
  ]);

  const [filter, setFilter] = useState('all'); // all, unread, read

  const handleMarkAsRead = (id) => {
    setNotifications(notifications.map(notif =>
      notif.id === id ? { ...notif, read: !notif.read } : notif
    ));
  };

  const handleRemove = (id) => {
    setNotifications(notifications.filter(notif => notif.id !== id));
  };

  const handleMarkAllAsRead = () => {
    setNotifications(notifications.map(notif => ({ ...notif, read: true })));
  };

  const handleClearAll = () => {
    setNotifications([]);
  };

  const filteredNotifications = notifications.filter(notif => {
    if (filter === 'unread') return !notif.read;
    if (filter === 'read') return notif.read;
    return true;
  });

  return (
    <div className="container mx-auto px-4 py-6 max-w-3xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold">Notifications</h1>
          {notifications.some(n => !n.read) && (
            <span className="bg-blue-100 text-blue-600 text-xs font-medium px-2 py-0.5 rounded-full">
              {notifications.filter(n => !n.read).length} new
            </span>
          )}
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={handleMarkAllAsRead}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Mark all as read
          </button>
          <button
            onClick={handleClearAll}
            className="text-sm text-gray-600 hover:text-gray-700"
          >
            Clear all
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 text-sm rounded-full ${
            filter === 'all'
              ? 'bg-gray-900 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('unread')}
          className={`px-3 py-1 text-sm rounded-full ${
            filter === 'unread'
              ? 'bg-gray-900 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Unread
        </button>
        <button
          onClick={() => setFilter('read')}
          className={`px-3 py-1 text-sm rounded-full ${
            filter === 'read'
              ? 'bg-gray-900 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Read
        </button>
      </div>

      {/* Notifications List */}
      <div className="space-y-3">
        {filteredNotifications.map((notification) => (
          <NotificationItem
            key={notification.id}
            notification={notification}
            onMarkAsRead={handleMarkAsRead}
            onRemove={handleRemove}
          />
        ))}
      </div>

      {/* Empty State */}
      {filteredNotifications.length === 0 && (
        <div className="text-center py-12">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gray-100 mb-4">
            <Bell className="w-6 h-6 text-gray-400" />
          </div>
          <h3 className="text-sm font-medium text-gray-900">No notifications</h3>
          <p className="mt-1 text-sm text-gray-500">
            {filter === 'all'
              ? "You're all caught up!"
              : filter === 'unread'
              ? 'No unread notifications'
              : 'No read notifications'}
          </p>
        </div>
      )}
    </div>
  );
};

export default Notifications;
