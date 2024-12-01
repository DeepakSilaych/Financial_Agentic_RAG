import React, { useState } from 'react';
import { Users, UserPlus, Mail } from 'lucide-react';
import { useTeam } from '../../context/TeamContext';

const TeamMembers = () => {
  const { currentTeam, teamMembers } = useTeam();
  const [isOpen, setIsOpen] = useState(false);
  const [isInviting, setIsInviting] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');

  const handleInvite = () => {
    if (inviteEmail.trim()) {
      // Here you would typically make an API call to invite the user
      console.log('Inviting:', inviteEmail);
      setInviteEmail('');
      setIsInviting(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-gray-500 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-pink-500 p-2 rounded-md relative"
      >
        <Users size={20} />
        {teamMembers.filter(m => m.status === 'online').length > 0 && (
          <span className="absolute top-1 right-1 w-2 h-2 bg-green-500 rounded-full"></span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
          <div className="px-4 py-2 text-xs font-medium text-gray-500 flex justify-between items-center">
            <span>Team Members</span>
            <span className="text-green-500">
              {teamMembers.filter(m => m.status === 'online').length} online
            </span>
          </div>

          <div className="max-h-64 overflow-y-auto">
            {teamMembers.map(member => (
              <div
                key={member.id}
                className="px-4 py-2 hover:bg-gray-50 flex items-center justify-between"
              >
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-600">
                      {member.avatar}
                    </div>
                    {member.status === 'online' && (
                      <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-white"></span>
                    )}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {member.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {member.role}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-gray-200 my-1"></div>

          {isInviting ? (
            <div className="px-4 py-2">
              <div className="flex items-center space-x-2">
                <Mail size={16} className="text-gray-400" />
                <input
                  type="email"
                  placeholder="Enter email address..."
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="flex-1 text-sm border-none focus:ring-0 p-0"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleInvite();
                    } else if (e.key === 'Escape') {
                      setIsInviting(false);
                    }
                  }}
                  autoFocus
                />
              </div>
              <div className="flex justify-end space-x-2 mt-2">
                <button
                  onClick={() => setIsInviting(false)}
                  className="px-2 py-1 text-xs text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={handleInvite}
                  className="px-2 py-1 text-xs text-pink-600 hover:text-pink-800"
                >
                  Send Invite
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setIsInviting(true)}
              className="w-full text-left px-4 py-2 text-sm text-pink-600 hover:bg-gray-100 flex items-center space-x-2"
            >
              <UserPlus size={16} />
              <span>Invite Team Member</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default TeamMembers;
