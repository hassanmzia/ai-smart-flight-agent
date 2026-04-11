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

/* ------------------------------------------------------------------ */
/*  Shared helpers                                                     */
/* ------------------------------------------------------------------ */

const dropdownTransition = {
  enter: 'transition ease-out duration-100',
  enterFrom: 'transform opacity-0 scale-95',
  enterTo: 'transform opacity-100 scale-100',
  leave: 'transition ease-in duration-75',
  leaveFrom: 'transform opacity-100 scale-100',
  leaveTo: 'transform opacity-0 scale-95',
};

const navBtnCls =
  'text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-2 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1 transition-all whitespace-nowrap';

const itemCls = (active: boolean) =>
  `${active ? 'bg-gray-50 dark:bg-gray-700' : ''} flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md`;

/* ------------------------------------------------------------------ */
/*  Dropdown component                                                 */
/* ------------------------------------------------------------------ */

interface DropdownItem {
  to: string;
  icon: string;
  label: string;
}

const NavDropdown = ({
  label,
  items,
  alignRight,
}: {
  label: string;
  items: DropdownItem[];
  alignRight?: boolean;
}) => (
  <Menu as="div" className="relative">
    <Menu.Button className={navBtnCls}>
      {label}
      <ChevronDownIcon className="h-3 w-3" />
    </Menu.Button>
    <Transition as={Fragment} {...dropdownTransition}>
      <Menu.Items
        className={`absolute ${alignRight ? 'right-0 origin-top-right' : 'left-0 origin-top-left'} mt-2 w-52 rounded-lg bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none border border-gray-200 dark:border-gray-700 z-50`}
      >
        <div className="p-1">
          {items.map((item) => (
            <Menu.Item key={item.to}>
              {({ active }) => (
                <Link to={item.to} className={itemCls(active)}>
                  <span className="text-sm">{item.icon}</span> {item.label}
                </Link>
              )}
            </Menu.Item>
          ))}
        </div>
      </Menu.Items>
    </Transition>
  </Menu>
);

/* ------------------------------------------------------------------ */
/*  Menu definitions                                                   */
/* ------------------------------------------------------------------ */

const planItems: DropdownItem[] = [
  { to: ROUTES.AI_PLANNER, icon: '🤖', label: 'AI Planner' },
  { to: ROUTES.CHAT, icon: '💬', label: 'AI Chat' },
  { to: ROUTES.AGENT_HUB, icon: '🧠', label: 'Agent Hub' },
  { to: ROUTES.PREDICTIONS, icon: '📊', label: 'Predictions' },
  { to: ROUTES.PRICING, icon: '💎', label: 'Pricing & Plans' },
];

const searchItems: DropdownItem[] = [
  { to: ROUTES.FLIGHT_SEARCH, icon: '✈️', label: 'Flights' },
  { to: ROUTES.HOTEL_SEARCH, icon: '🏨', label: 'Hotels' },
  { to: ROUTES.RENTAL_SEARCH, icon: '🏡', label: 'Vacation Rentals' },
  { to: '/cars', icon: '🚙', label: 'Car Rentals' },
];

const exploreItems: DropdownItem[] = [
  { to: '/attractions', icon: '🗺️', label: 'Attractions' },
  { to: '/restaurants', icon: '🍽️', label: 'Restaurants' },
  { to: '/shopping', icon: '🛍️', label: 'Shopping' },
  { to: '/events', icon: '🎉', label: 'Events' },
  { to: ROUTES.PARTNERSHIPS, icon: '🏷️', label: 'Deals & Coupons' },
];

const travelInfoItems: DropdownItem[] = [
  { to: '/weather', icon: '🌤️', label: 'Weather' },
  { to: '/commute', icon: '🚗', label: 'Traffic & Commute' },
  { to: ROUTES.SAFETY_DASHBOARD, icon: '🛡️', label: 'Safety Intelligence' },
  { to: ROUTES.AI_RATINGS, icon: '⭐', label: 'AI Ratings' },
  { to: ROUTES.TRAVEL_PROFILE, icon: '🧬', label: 'Travel DNA' },
  { to: ROUTES.LANGUAGE_TOOL, icon: '🌐', label: 'Language Tool' },
  { to: ROUTES.DESTINATION_GUIDE, icon: '📍', label: 'Destination Guide' },
  { to: ROUTES.TRIP_MEMORY, icon: '🧠', label: 'Trip Memory' },
  { to: ROUTES.DESTINATION_KB, icon: '📚', label: 'Destination KB' },
  { to: ROUTES.FAITH_TRAVEL, icon: '🕌', label: 'Faith Travel' },
  { to: ROUTES.HEALTH_TRAVEL, icon: '🏥', label: 'Health Travel' },
];

const communityItems: DropdownItem[] = [
  { to: ROUTES.COMMUNITY, icon: '🌐', label: 'Community' },
  { to: ROUTES.TRAVEL_STORIES, icon: '📖', label: 'Travel Stories' },
  { to: ROUTES.TRIP_GALLERY, icon: '🗺️', label: 'Trip Gallery' },
  { to: ROUTES.CONTENT_HUB, icon: '📸', label: 'Content Hub' },
  { to: ROUTES.COLLABORATE, icon: '👥', label: 'Collaborate' },
  { to: ROUTES.TRIP_MAP, icon: '🌍', label: 'My Travel Map' },
];

/* ------------------------------------------------------------------ */
/*  Mobile menu section                                                */
/* ------------------------------------------------------------------ */

const MobileSection = ({
  title,
  items,
  onClose,
}: {
  title: string;
  items: DropdownItem[];
  onClose: () => void;
}) => (
  <div className="py-2">
    <div className="px-4 pb-1.5 text-[11px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest">
      {title}
    </div>
    <div className="space-y-0.5 px-2">
      {items.map((item) => (
        <Link
          key={item.to}
          to={item.to}
          onClick={onClose}
          className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-[13px] text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50 active:bg-gray-200 dark:active:bg-gray-600/50 transition-colors"
        >
          <span className="text-base leading-none">{item.icon}</span>
          <span>{item.label}</span>
        </Link>
      ))}
    </div>
  </div>
);

/* ------------------------------------------------------------------ */
/*  Header Component                                                   */
/* ------------------------------------------------------------------ */

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

  const closeMobile = () => setMobileMenuOpen(false);

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16 lg:h-[4.5rem]">
          {/* Logo */}
          <Link to={ROUTES.HOME} className="flex items-center gap-2 group flex-shrink-0 mr-3">
            <span className="text-2xl">✈️</span>
            <span className="hidden sm:inline text-sm font-bold bg-gradient-to-r from-primary-600 to-primary-800 dark:from-primary-400 dark:to-primary-600 bg-clip-text text-transparent group-hover:from-primary-700 group-hover:to-primary-900 dark:group-hover:from-primary-300 dark:group-hover:to-primary-500 transition-all whitespace-nowrap">
              AI Travel Agent
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-0.5 flex-1 justify-center">
            <NavDropdown label="Plan" items={planItems} />
            <NavDropdown label="Search" items={searchItems} />
            <NavDropdown label="Explore" items={exploreItems} />
            <NavDropdown label="Travel Info" items={travelInfoItems} />
            <NavDropdown label="Community" items={communityItems} alignRight />

            <Link to={ROUTES.ITINERARY} className={navBtnCls}>
              My Trips
            </Link>
            {isAuthenticated && (
              <Link to={ROUTES.DASHBOARD} className={navBtnCls}>
                Dashboard
              </Link>
            )}
          </nav>

          {/* Right side actions */}
          <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
            {/* Theme toggle */}
            <button
              onClick={handleThemeToggle}
              className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-lg"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? (
                <SunIcon className="h-5 w-5" />
              ) : (
                <MoonIcon className="h-5 w-5" />
              )}
            </button>

            {isAuthenticated ? (
              <>
                {/* Notifications */}
                <button
                  onClick={() => navigate('/notifications')}
                  className="relative p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-lg"
                  aria-label="Notifications"
                >
                  <BellIcon className="h-5 w-5" />
                  {unreadCount > 0 && (
                    <span className="absolute top-0.5 right-0.5 block h-4 w-4 rounded-full bg-red-500 text-white text-[10px] leading-4 text-center font-medium">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </button>

                {/* User menu */}
                <Menu as="div" className="relative">
                  <Menu.Button className="flex items-center p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
                    {user?.name ? (
                      <span className="inline-flex items-center justify-center h-7 w-7 rounded-full bg-primary-600 text-white text-xs font-semibold select-none">
                        {user.name.charAt(0).toUpperCase()}
                      </span>
                    ) : (
                      <UserCircleIcon className="h-7 w-7 text-gray-600 dark:text-gray-300" />
                    )}
                  </Menu.Button>

                  <Transition as={Fragment} {...dropdownTransition}>
                    <Menu.Items className="absolute right-0 mt-2 w-48 origin-top-right rounded-lg bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50 border border-gray-200 dark:border-gray-700">
                      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
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
              <div className="flex items-center gap-1.5">
                <Button variant="ghost" onClick={() => navigate(ROUTES.LOGIN)} className="!text-xs !px-3 !py-1.5">
                  Sign In
                </Button>
                <Button onClick={() => navigate(ROUTES.REGISTER)} className="!text-xs !px-3 !py-1.5">
                  Sign Up
                </Button>
              </div>
            )}

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-lg"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 max-h-[calc(100dvh-4rem)] overflow-y-auto overscroll-contain">
          {/* Section groups with dividers */}
          <MobileSection title="Plan" items={planItems} onClose={closeMobile} />

          <div className="mx-4 border-t border-gray-100 dark:border-gray-700/50" />
          <MobileSection title="Search" items={searchItems} onClose={closeMobile} />

          <div className="mx-4 border-t border-gray-100 dark:border-gray-700/50" />
          <MobileSection title="Explore" items={exploreItems} onClose={closeMobile} />

          <div className="mx-4 border-t border-gray-100 dark:border-gray-700/50" />
          <MobileSection title="Travel Info" items={travelInfoItems} onClose={closeMobile} />

          <div className="mx-4 border-t border-gray-100 dark:border-gray-700/50" />
          <MobileSection title="Community" items={communityItems} onClose={closeMobile} />

          {/* Quick links */}
          <div className="mx-4 border-t border-gray-200 dark:border-gray-700" />
          <div className="py-2 px-2 space-y-0.5">
            <Link
              to={ROUTES.ITINERARY}
              onClick={closeMobile}
              className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-[13px] font-semibold text-gray-800 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700/50 active:bg-gray-200 dark:active:bg-gray-600/50 transition-colors"
            >
              <span className="text-base leading-none">📋</span>
              <span>My Trips</span>
            </Link>
            {isAuthenticated && (
              <Link
                to={ROUTES.DASHBOARD}
                onClick={closeMobile}
                className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-[13px] font-semibold text-gray-800 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700/50 active:bg-gray-200 dark:active:bg-gray-600/50 transition-colors"
              >
                <span className="text-base leading-none">📊</span>
                <span>Dashboard</span>
              </Link>
            )}
          </div>

          {/* Bottom safe area spacing */}
          <div className="h-4" />
        </div>
      )}
    </header>
  );
};

export default Header;
