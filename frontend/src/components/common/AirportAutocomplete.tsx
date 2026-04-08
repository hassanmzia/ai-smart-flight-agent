import { useState, useEffect, useRef, useCallback } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { cn } from '@/utils/helpers';
import api from '@/services/api';

interface Airport {
  code: string;
  name: string;
  city: string;
  country: string;
  display: string;
}

interface AirportAutocompleteProps {
  label: string;
  value: string;
  onChange: (value: string, airport?: Airport) => void;
  placeholder?: string;
  required?: boolean;
  className?: string;
}

const AirportAutocomplete = ({
  label,
  value,
  onChange,
  placeholder = 'Search city or airport...',
  required = false,
  className,
}: AirportAutocompleteProps) => {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<Airport[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  // Sync external value changes
  useEffect(() => {
    setQuery(value);
  }, [value]);

  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 1) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }

    setLoading(true);
    try {
      const response = await api.get(`/api/flights/airports?q=${encodeURIComponent(q)}&limit=8`);
      const data = response.data;
      setSuggestions(Array.isArray(data) ? data : []);
      setIsOpen(data.length > 0);
      setHighlightIndex(-1);
    } catch {
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    onChange(val); // Keep parent in sync with raw text

    // Debounce API calls
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(val), 200);
  };

  const handleSelect = (airport: Airport) => {
    const displayValue = `${airport.city} (${airport.code})`;
    setQuery(displayValue);
    onChange(displayValue, airport);
    setIsOpen(false);
    setSuggestions([]);
    inputRef.current?.blur();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || suggestions.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightIndex(prev => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter' && highlightIndex >= 0) {
      e.preventDefault();
      handleSelect(suggestions[highlightIndex]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Cleanup debounce
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  const inputId = label.toLowerCase().replace(/\s+/g, '-');

  return (
    <div ref={wrapperRef} className={cn('w-full relative', className)}>
      <label
        htmlFor={inputId}
        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
      >
        {label}
      </label>

      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
        </div>

        <input
          ref={inputRef}
          id={inputId}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (suggestions.length > 0) setIsOpen(true);
          }}
          placeholder={placeholder}
          required={required}
          autoComplete="off"
          className={cn(
            'block w-full rounded-lg border transition-colors',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'dark:bg-gray-800 dark:text-white dark:border-gray-600',
            'border-gray-300 dark:border-gray-600',
            'pl-10 pr-3 py-2',
          )}
        />

        {loading && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <div className="h-4 w-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && suggestions.length > 0 && (
        <div className="absolute z-50 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-64 overflow-y-auto">
          {suggestions.map((airport, idx) => (
            <button
              key={airport.code + idx}
              type="button"
              onClick={() => handleSelect(airport)}
              className={cn(
                'w-full text-left px-3 py-2.5 flex items-center gap-3 transition-colors',
                'hover:bg-primary-50 dark:hover:bg-gray-700',
                idx === highlightIndex && 'bg-primary-50 dark:bg-gray-700',
                idx < suggestions.length - 1 && 'border-b border-gray-100 dark:border-gray-750',
              )}
            >
              <span className="flex-shrink-0 w-12 text-center font-bold text-primary-600 dark:text-primary-400 text-sm bg-primary-50 dark:bg-primary-900/30 rounded px-1.5 py-0.5">
                {airport.code}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {airport.city}, {airport.country}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {airport.name}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default AirportAutocomplete;
