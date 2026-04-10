import { Fragment, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Menu, Transition } from '@headlessui/react';
import {
  BellIcon,
  UserCircleIcon,
  SunIcon,
  MoonIcon,
  Bars3Icon,
  XMarkIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '@/hooks/useAuth';
import { useNotifications } from '@/hooks/useNotifications';
import { ROUTES } from '@/utils/constants';
import { getTheme, toggleTheme } from '@/utils/helpers';
import Button from '@/components/common/Button';

const Header = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();
  const { unreadCount } = useNotifications();
  const [theme, setTheme] = useState(getTheme());
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleThemeToggle = () => {
    toggleTheme();
    setTheme(getTheme());
  };

  const handleLogout = () => {
    logout();
    navigate(ROUTES.LOGIN);
  };

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to={ROUTES.HOME} className="flex items-center gap-2 group">
            <span className="text-base">✈️</span>
            <span className="text-sm font-bold bg-gradient-to-r from-primary-600 to-primary-800 dark:from-primary-400 dark:to-primary-600 bg-clip-text text-transparent group-hover:from-primary-700 group-hover:to-primary-900 dark:group-hover:from-primary-300 dark:group-hover:to-primary-500 transition-all">
              AI Travel Agent
            </span>
          </Link>

          {/* Navigation */}
          <nav className="hidden lg:flex items-center space-x-2">
            {/* AI Planner - First */}
            <Link
              to={ROUTES.AI_PLANNER}
              className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-all"
            >
              <span>🤖</span> AI Planner
            </Link>

            {/* AI Chat */}
            <Link
              to={ROUTES.CHAT}
              className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-all"
            >
              <span>💬</span> AI Chat
            </Link>

            {/* Agent Hub */}
            <Link
              to={ROUTES.AGENT_HUB}
              className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-all"
            >
              <span>🧠</span> Agent Hub
            </Link>

            {/* Search Dropdown */}
            <Menu as="div" className="relative">
              <Menu.Button className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-1 transition-all">
                Search
                <ChevronDownIcon className="h-4 w-4" />
              </Menu.Button>

              <Transition
                as={Fragment}
                enter="transition ease-out duration-100"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
              >
                <Menu.Items className="absolute left-0 mt-2 w-56 origin-top-left rounded-lg bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none border border-gray-200 dark:border-gray-700">
                  <div className="p-1">
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to={ROUTES.FLIGHT_SEARCH}
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>✈️</span> Flights
                        </Link>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to={ROUTES.HOTEL_SEARCH}
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>🏨</span> Hotels
                        </Link>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to="/cars"
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>🚙</span> Car Rentals
                        </Link>
                      )}
                    </Menu.Item>
                  </div>
                </Menu.Items>
              </Transition>
            </Menu>

            {/* Explore Dropdown */}
            <Menu as="div" className="relative">
              <Menu.Button className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-1 transition-all">
                Explore
                <ChevronDownIcon className="h-4 w-4" />
              </Menu.Button>

              <Transition
                as={Fragment}
                enter="transition ease-out duration-100"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
              >
                <Menu.Items className="absolute left-0 mt-2 w-56 origin-top-left rounded-lg bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none border border-gray-200 dark:border-gray-700">
                  <div className="p-1">
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to="/attractions"
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>🗺️</span> Attractions
                        </Link>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to="/restaurants"
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>🍽️</span> Restaurants
                        </Link>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to="/shopping"
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>🛍️</span> Shopping
                        </Link>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to="/events"
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>🎉</span> Events
                        </Link>
                      )}
                    </Menu.Item>
                  </div>
                </Menu.Items>
              </Transition>
            </Menu>

            {/* Travel Info Dropdown */}
            <Menu as="div" className="relative">
              <Menu.Button className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-1 transition-all">
                Travel Info
                <ChevronDownIcon className="h-4 w-4" />
              </Menu.Button>

              <Transition
                as={Fragment}
                enter="transition ease-out duration-100"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
              >
                <Menu.Items className="absolute left-0 mt-2 w-56 origin-top-left rounded-lg bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none border border-gray-200 dark:border-gray-700">
                  <div className="p-1">
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to="/weather"
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>🌤️</span> Weather
                        </Link>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to="/commute"
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>🚗</span> Traffic & Commute
                        </Link>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to={ROUTES.SAFETY_DASHBOARD}
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>🛡️</span> Safety Intelligence
                        </Link>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to={ROUTES.AI_RATINGS}
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>⭐</span> AI Ratings
                        </Link>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to={ROUTES.TRAVEL_PROFILE}
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>🧬</span> Travel DNA
                        </Link>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to={ROUTES.LANGUAGE_TOOL}
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>🌐</span> Language Tool
                        </Link>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to={ROUTES.DESTINATION_GUIDE}
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>📍</span> Destination Guide
                        </Link>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to={ROUTES.TRIP_MEMORY}
                          className={`${
                            active ? 'bg-gray-50 dark:bg-gray-700' : ''
                          } flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`}
                        >
                          <span>🧠</span> Trip Memory
                        </Link>
                      )}
                    </Menu.Item>
                  </div>
                </Menu.Items>
              </Transition>
            </Menu>

            <Link
              to={ROUTES.PRICING}
              className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-3 py-2 rounded-lg text-sm font-medium transition-all"
            >
              Pricing
            </Link>
            <Link
              to={ROUTES.COLLABORATE}
              className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-all"
            >
              <span>👥</span> Collaborate
            </Link>
            <Link
              to={ROUTES.PREDICTIONS}
              className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-all"
            >
              <span>📊</span> Predictions
            </Link>
            <Link
              to={ROUTES.TRIP_MAP}
              className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-all"
            >
              <span>🌍</span> My Travel
            </Link>
            <Link
              to={ROUTES.COMMUNITY}
              className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-all"
            >
              <span>🌐</span> Community
            </Link>
            <Link
              to={ROUTES.ITINERARY}
              className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-3 py-2 rounded-lg text-sm font-medium transition-all"
            >
              My Trips
            </Link>
            {isAuthenticated && (
              <Link
                to={ROUTES.DASHBOARD}
                className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-3 py-2 rounded-lg text-sm font-medium transition-all"
              >
                Dashboard
              </Link>
            )}
          </nav>

          {/* Right side actions */}
          <div className="flex items-center space-x-4">
            {/* Theme toggle */}
            <button
              onClick={handleThemeToggle}
              className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            >
              {theme === 'dark' ? (
                <SunIcon className="h-6 w-6" />
              ) : (
                <MoonIcon className="h-6 w-6" />
              )}
            </button>

            {isAuthenticated ? (
              <>
                {/* Notifications */}
                <button
                  onClick={() => navigate('/notifications')}
                  className="relative p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                >
                  <BellIcon className="h-6 w-6" />
                  {unreadCount > 0 && (
                    <span className="absolute top-0 right-0 block h-5 w-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </button>

                {/* User menu */}
                <Menu as="div" className="relative">
                  <Menu.Button className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
                    <UserCircleIcon className="h-8 w-8 text-gray-500 dark:text-gray-400" />
                  </Menu.Button>

                  <Transition
                    as={Fragment}
                    enter="transition ease-out duration-100"
                    enterFrom="transform opacity-0 scale-95"
                    enterTo="transform opacity-100 scale-100"
                    leave="transition ease-in duration-75"
                    leaveFrom="transform opacity-100 scale-100"
                    leaveTo="transform opacity-0 scale-95"
                  >
                    <Menu.Items className="absolute right-0 mt-2 w-48 origin-top-right rounded-md bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {user?.name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          {user?.email}
                        </p>
                      </div>

                      <div className="py-1">
                        <Menu.Item>
                          {({ active }) => (
                            <Link
                              to={ROUTES.PROFILE}
                              className={`${
                                active ? 'bg-gray-100 dark:bg-gray-700' : ''
                              } block px-4 py-2 text-sm text-gray-700 dark:text-gray-300`}
                            >
                              Profile
                            </Link>
                          )}
                        </Menu.Item>
                        <Menu.Item>
                          {({ active }) => (
                            <Link
                              to={ROUTES.DASHBOARD}
                              className={`${
                                active ? 'bg-gray-100 dark:bg-gray-700' : ''
                              } block px-4 py-2 text-sm text-gray-700 dark:text-gray-300`}
                            >
                              My Bookings
                            </Link>
                          )}
                        </Menu.Item>
                        {user?.role === 'admin' && (
                          <Menu.Item>
                            {({ active }) => (
                              <Link
                                to={ROUTES.ADMIN_DASHBOARD}
                                className={`${
                                  active ? 'bg-gray-100 dark:bg-gray-700' : ''
                                } block px-4 py-2 text-sm text-gray-700 dark:text-gray-300`}
                              >
                                Admin Dashboard
                              </Link>
                            )}
                          </Menu.Item>
                        )}
                      </div>

                      <div className="py-1 border-t border-gray-200 dark:border-gray-700">
                        <Menu.Item>
                          {({ active }) => (
                            <button
                              onClick={handleLogout}
                              className={`${
                                active ? 'bg-gray-100 dark:bg-gray-700' : ''
                              } block w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400`}
                            >
                              Sign out
                            </button>
                          )}
                        </Menu.Item>
                      </div>
                    </Menu.Items>
                  </Transition>
                </Menu>
              </>
            ) : (
              <div className="flex space-x-2">
                <Button variant="ghost" onClick={() => navigate(ROUTES.LOGIN)}>
                  Sign In
                </Button>
                <Button onClick={() => navigate(ROUTES.REGISTER)}>Sign Up</Button>
              </div>
            )}

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            >
              {mobileMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-gray-200 dark:border-gray-700 py-4 space-y-1.5 max-h-[calc(100dvh-5rem)] overflow-y-auto overscroll-contain safe-bottom">
            <Link
              to={ROUTES.AI_PLANNER}
              onClick={() => setMobileMenuOpen(false)}
              className="block px-4 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50"
            >
              🤖 AI Planner
            </Link>
            <Link
              to={ROUTES.CHAT}
              onClick={() => setMobileMenuOpen(false)}
              className="block px-4 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50"
            >
              💬 AI Chat
            </Link>

            <div className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Search</div>
            <Link to={ROUTES.FLIGHT_SEARCH} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">✈️ Flights</Link>
            <Link to={ROUTES.HOTEL_SEARCH} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🏨 Hotels</Link>
            <Link to="/cars" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🚙 Car Rentals</Link>

            <div className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Explore</div>
            <Link to="/attractions" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🗺️ Attractions</Link>
            <Link to="/restaurants" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🍽️ Restaurants</Link>
            <Link to="/shopping" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🛍️ Shopping</Link>
            <Link to="/events" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🎉 Events</Link>

            <div className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Travel Info</div>
            <Link to="/weather" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🌤️ Weather</Link>
            <Link to="/commute" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🚗 Traffic & Commute</Link>
            <Link to={ROUTES.SAFETY_DASHBOARD} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🛡️ Safety Intelligence</Link>
            <Link to={ROUTES.AI_RATINGS} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">⭐ AI Ratings</Link>
            <Link to={ROUTES.TRAVEL_PROFILE} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🧬 Travel DNA</Link>
            <Link to={ROUTES.LANGUAGE_TOOL} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🌐 Language Tool</Link>
            <Link to={ROUTES.DESTINATION_GUIDE} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">📍 Destination Guide</Link>
            <Link to={ROUTES.TRIP_MEMORY} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🧠 Trip Memory</Link>

            <div className="border-t border-gray-200 dark:border-gray-700 mt-2 pt-2">
              <Link to={ROUTES.AGENT_HUB} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🧠 Agent Hub</Link>
              <Link to={ROUTES.COLLABORATE} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">👥 Collaborate</Link>
              <Link to={ROUTES.PRICING} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">Pricing</Link>
              <Link to={ROUTES.PREDICTIONS} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">📊 Predictions</Link>
              <Link to={ROUTES.TRIP_MAP} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🌍 My Travel</Link>
              <Link to={ROUTES.COMMUNITY} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">🌐 Community</Link>
              <Link to={ROUTES.ITINERARY} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">My Trips</Link>
              {isAuthenticated && (
                <Link to={ROUTES.DASHBOARD} onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">Dashboard</Link>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
