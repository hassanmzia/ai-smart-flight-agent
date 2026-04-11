import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';

interface Collaborator {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'editor' | 'viewer';
  avatar?: string;
  joinedAt: string;
}

interface VoteItem {
  id: string;
  type: 'flight' | 'hotel' | 'rental' | 'restaurant' | 'attraction';
  name: string;
  details: string;
  price?: string;
  votes: { up: number; down: number };
  userVote?: 'up' | 'down' | null;
  addedBy: string;
}

const CollaboratePage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'my-trips' | 'create' | 'join'>('my-trips');
  const [inviteEmail, setInviteEmail] = useState('');
  const [tripName, setTripName] = useState('');
  const [destination, setDestination] = useState('');

  // Mock data for demonstration
  const [collaborators] = useState<Collaborator[]>([
    { id: '1', name: 'You', email: user?.email || '', role: 'admin', joinedAt: new Date().toISOString() },
  ]);

  const [voteItems] = useState<VoteItem[]>([
    {
      id: '1', type: 'hotel', name: 'Grand Hyatt Tokyo', details: '5-star, Roppongi Hills',
      price: '$280/night', votes: { up: 3, down: 1 }, userVote: 'up', addedBy: 'You'
    },
    {
      id: '2', type: 'rental', name: 'Shibuya Family Villa', details: '4 bed, 3 bath, entire home, sleeps 10',
      price: '$420/night (whole property)', votes: { up: 5, down: 0 }, userVote: 'up', addedBy: 'Sarah'
    },
    {
      id: '3', type: 'hotel', name: 'Park Hotel Tokyo', details: '4-star, Shiodome',
      price: '$180/night', votes: { up: 2, down: 0 }, userVote: null, addedBy: 'Sarah'
    },
    {
      id: '4', type: 'restaurant', name: 'Sushi Saito', details: '3 Michelin stars, Roppongi',
      price: '$300/person', votes: { up: 4, down: 0 }, userVote: 'up', addedBy: 'Mike'
    },
  ]);

  const tabs = [
    { id: 'my-trips' as const, label: 'My Shared Trips', icon: '🗂️' },
    { id: 'create' as const, label: 'Create Trip', icon: '➕' },
    { id: 'join' as const, label: 'Join Trip', icon: '🔗' },
  ];

  const roleColors = {
    admin: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    editor: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    viewer: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-300',
  };

  const typeIcons: Record<string, string> = { flight: '✈️', hotel: '🏨', rental: '🏡', restaurant: '🍽️', attraction: '🎭' };

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <div className="relative overflow-hidden bg-gradient-to-br from-teal-500 via-cyan-600 to-blue-600 dark:from-teal-800 dark:via-cyan-800 dark:to-blue-800">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-20 -right-20 w-72 h-72 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-48 h-48 bg-teal-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-3xl md:text-4xl font-extrabold text-white mb-2">
            👥 Collaborative Trip Planning
          </h1>
          <p className="text-cyan-100 text-lg">
            Plan trips together with friends and family. Vote on options, split costs, and build the perfect itinerary as a team.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
        {/* Tabs */}
        <div className="flex gap-1.5 sm:gap-2 mb-6 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-hide">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1 sm:gap-2 px-3 sm:px-5 py-2.5 rounded-xl font-medium text-xs sm:text-sm transition-all duration-200 whitespace-nowrap flex-shrink-0 ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-teal-600 to-cyan-600 text-white shadow-lg shadow-teal-500/25'
                  : 'bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-700 shadow-sm border border-gray-200/60 dark:border-gray-700/50'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* My Shared Trips */}
        {activeTab === 'my-trips' && (
          <div className="space-y-6">
            {/* Sample shared trip card */}
            <Card>
              <CardContent>
                <div className="p-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white">Tokyo Adventure 2026</h3>
                      <p className="text-gray-600 dark:text-gray-400">Apr 15 - Apr 22 · 4 collaborators</p>
                    </div>
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 self-start">
                      Active
                    </span>
                  </div>

                  {/* Collaborators */}
                  <div className="mb-6">
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Team Members</h4>
                    <div className="flex flex-wrap gap-2">
                      {collaborators.map((c) => (
                        <div key={c.id} className="flex items-center gap-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg px-3 py-2">
                          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-400 to-cyan-500 flex items-center justify-center text-white text-xs font-bold">
                            {c.name.charAt(0)}
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">{c.name}</p>
                            <span className={`text-xs px-1.5 py-0.5 rounded ${roleColors[c.role]}`}>{c.role}</span>
                          </div>
                        </div>
                      ))}
                      <button className="flex items-center gap-1 px-3 py-2 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-gray-500 dark:text-gray-400 hover:border-teal-500 hover:text-teal-500 transition-colors text-sm">
                        + Invite
                      </button>
                    </div>
                  </div>

                  {/* Invite Input */}
                  <div className="mb-6 flex gap-2">
                    <input
                      type="email"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      placeholder="Enter email to invite..."
                      className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm"
                    />
                    <Button onClick={() => setInviteEmail('')}>
                      Send Invite
                    </Button>
                  </div>

                  {/* Accommodation Comparison */}
                  <div className="mb-6">
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Accommodation Cost Comparison</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-lg">🏨</span>
                          <span className="font-semibold text-gray-900 dark:text-white text-sm">Hotel Option</span>
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">3 rooms x $180/night x 7 nights</p>
                        <p className="text-lg font-bold text-blue-700 dark:text-blue-300">$3,780 total</p>
                        <p className="text-xs text-gray-500 mt-1">~$945 per family (4 families)</p>
                      </div>
                      <div className="bg-green-50 dark:bg-green-900/20 border-2 border-green-400 dark:border-green-600 rounded-xl p-4 relative">
                        <span className="absolute -top-2.5 right-3 text-xs bg-green-500 text-white px-2 py-0.5 rounded-full font-medium">Best Value</span>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-lg">🏡</span>
                          <span className="font-semibold text-gray-900 dark:text-white text-sm">Vacation Rental</span>
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">$420/night x 7 nights + $150 cleaning</p>
                        <p className="text-lg font-bold text-green-700 dark:text-green-300">$3,090 total</p>
                        <p className="text-xs text-gray-500 mt-1">~$773 per family (4 families) &mdash; save $690!</p>
                      </div>
                    </div>
                  </div>

                  {/* Voting Section */}
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Vote on Options</h4>
                    <div className="space-y-3">
                      {voteItems.map((item) => (
                        <div key={item.id} className="flex items-center gap-4 bg-gray-50 dark:bg-gray-700/30 rounded-xl p-4 border border-gray-200/60 dark:border-gray-700/50">
                          <div className="text-2xl">{typeIcons[item.type]}</div>
                          <div className="flex-1 min-w-0">
                            <h5 className="font-semibold text-gray-900 dark:text-white truncate">{item.name}</h5>
                            <p className="text-sm text-gray-600 dark:text-gray-400">{item.details}</p>
                            {item.price && (
                              <span className="text-sm font-medium text-teal-600 dark:text-teal-400">{item.price}</span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            <button
                              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                                item.userVote === 'up'
                                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                                  : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 hover:bg-green-50 hover:text-green-600'
                              }`}
                            >
                              👍 {item.votes.up}
                            </button>
                            <button
                              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                                item.userVote === 'down'
                                  ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                                  : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 hover:bg-red-50 hover:text-red-600'
                              }`}
                            >
                              👎 {item.votes.down}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Empty state for no trips */}
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400">
                No other shared trips yet.{' '}
                <button onClick={() => setActiveTab('create')} className="text-teal-600 dark:text-teal-400 hover:underline font-medium">
                  Create one!
                </button>
              </p>
            </div>
          </div>
        )}

        {/* Create Trip */}
        {activeTab === 'create' && (
          <Card>
            <CardHeader>
              <CardTitle>Create a Shared Trip</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6 max-w-lg">
                <Input
                  label="Trip Name"
                  value={tripName}
                  onChange={(e) => setTripName(e.target.value)}
                  placeholder="e.g., Tokyo Adventure 2026"
                  required
                />
                <Input
                  label="Destination"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  placeholder="e.g., Tokyo, Japan"
                  required
                />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input label="Start Date" type="date" value="" onChange={() => {}} required />
                  <Input label="End Date" type="date" value="" onChange={() => {}} required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Invite Collaborators (optional)
                  </label>
                  <textarea
                    placeholder="Enter email addresses, one per line..."
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                  />
                </div>
                <button className="w-full py-3 rounded-xl bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-700 hover:to-cyan-700 text-white font-semibold shadow-lg shadow-teal-500/25 hover:shadow-xl transition-all duration-200">
                  Create Shared Trip
                </button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Join Trip */}
        {activeTab === 'join' && (
          <Card>
            <CardHeader>
              <CardTitle>Join an Existing Trip</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="max-w-lg space-y-6">
                <p className="text-gray-600 dark:text-gray-400">
                  Enter the invite code shared by your trip organizer to join their collaborative trip planning.
                </p>
                <Input
                  label="Invite Code"
                  value=""
                  onChange={() => {}}
                  placeholder="e.g., TRIP-ABC123"
                  required
                />
                <button className="w-full py-3 rounded-xl bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-700 hover:to-cyan-700 text-white font-semibold shadow-lg shadow-teal-500/25 hover:shadow-xl transition-all duration-200">
                  Join Trip
                </button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default CollaboratePage;
