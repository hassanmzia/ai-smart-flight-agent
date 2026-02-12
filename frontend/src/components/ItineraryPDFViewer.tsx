/**
 * ItineraryPDFViewer Component
 * Professional PDF viewer for travel itineraries
 * Features: Inline viewing, download, email, theme selection
 */

import React, { useState } from 'react';
import {
  DocumentTextIcon,
  ArrowDownTrayIcon,
  EnvelopeIcon,
  EyeIcon,
  SwatchIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { ArrowPathIcon } from '@heroicons/react/24/solid';
import api from '../services/api';

interface ItineraryPDFViewerProps {
  itineraryId: number;
  destination?: string;
  onEmailSent?: () => void;
}

type PDFTheme = 'pumpkin' | 'ocean' | 'forest';
type EmailStatus = 'idle' | 'sending' | 'success' | 'error';

export const ItineraryPDFViewer: React.FC<ItineraryPDFViewerProps> = ({
  itineraryId,
  destination = 'Your Trip',
  onEmailSent
}) => {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState<PDFTheme>('pumpkin');
  const [includeQR, setIncludeQR] = useState(false);
  const [showViewer, setShowViewer] = useState(false);
  const [emailAddress, setEmailAddress] = useState('');
  const [emailStatus, setEmailStatus] = useState<EmailStatus>('idle');
  const [emailMessage, setEmailMessage] = useState('');

  const themes = [
    { name: 'pumpkin' as PDFTheme, label: 'Pumpkin Orange', color: '#f78b1f' },
    { name: 'ocean' as PDFTheme, label: 'Ocean Blue', color: '#0ea5e9' },
    { name: 'forest' as PDFTheme, label: 'Forest Green', color: '#10b981' }
  ];

  const generatePDF = async (format: 'download' | 'inline' = 'download') => {
    setLoading(true);
    try {
      const response = await api.post(
        `/api/itineraries/${itineraryId}/export-pdf/`,
        {
          theme: selectedTheme,
          include_qr: includeQR,
          format
        },
        { responseType: 'blob' }
      );

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);

      if (format === 'download') {
        const a = document.createElement('a');
        a.href = url;
        a.download = `itinerary_${destination.replace(/\s/g, '_')}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } else {
        setPdfUrl(url);
        setShowViewer(true);
      }
    } catch (error) {
      console.error('Error generating PDF:', error);
      alert('Failed to generate PDF. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const sendEmail = async () => {
    if (!emailAddress || !emailAddress.includes('@')) {
      setEmailStatus('error');
      setEmailMessage('Please enter a valid email address');
      return;
    }

    setEmailStatus('sending');
    setEmailMessage('Sending...');

    try {
      const response = await api.post(`/api/itineraries/${itineraryId}/send-email/`, {
        to_email: emailAddress,
        subject: `Your Trip Itinerary: ${destination}`,
        backend: 'auto',
        include_calendar: true
      });

      setEmailStatus('success');
      setEmailMessage(response.data.message || 'Email sent successfully!');
      setEmailAddress('');

      if (onEmailSent) {
        onEmailSent();
      }

      setTimeout(() => {
        setEmailStatus('idle');
        setEmailMessage('');
      }, 5000);
    } catch (error: any) {
      setEmailStatus('error');
      setEmailMessage(error.response?.data?.error || 'Failed to send email');

      setTimeout(() => {
        setEmailStatus('idle');
        setEmailMessage('');
      }, 5000);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* PDF Options Panel */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b-2 border-gray-100">
          <DocumentTextIcon className="w-6 h-6 text-gray-700" />
          <h3 className="text-xl font-bold text-gray-900">Export Itinerary</h3>
        </div>

        {/* Theme Selection */}
        <div className="mb-5">
          <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
            <SwatchIcon className="w-4 h-4" />
            PDF Theme
          </label>
          <div className="flex flex-col gap-2">
            {themes.map((theme) => (
              <button
                key={theme.name}
                className={`flex items-center gap-3 p-3 border-2 rounded-lg transition-all ${
                  selectedTheme === theme.name
                    ? 'border-opacity-100 bg-opacity-10'
                    : 'border-gray-200 bg-white hover:shadow-md hover:-translate-y-0.5'
                }`}
                onClick={() => setSelectedTheme(theme.name)}
                style={{
                  borderColor: selectedTheme === theme.name ? theme.color : undefined,
                  backgroundColor: selectedTheme === theme.name ? `${theme.color}10` : undefined
                }}
              >
                <div
                  className="w-4 h-4 rounded-full border-2 border-white shadow-sm"
                  style={{ backgroundColor: theme.color }}
                />
                <span className="text-sm font-medium">{theme.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* QR Code Option */}
        <div className="mb-5">
          <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-700">
            <input
              type="checkbox"
              checked={includeQR}
              onChange={(e) => setIncludeQR(e.target.checked)}
              className="w-4 h-4 cursor-pointer text-orange-500 focus:ring-orange-500 rounded"
            />
            <span>Include QR code for online version</span>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mb-6">
          <button
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-orange-600 to-orange-500 text-white rounded-lg font-semibold shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:translate-y-0"
            onClick={() => generatePDF('download')}
            disabled={loading}
          >
            {loading ? (
              <>
                <ArrowPathIcon className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <ArrowDownTrayIcon className="w-5 h-5" />
                Download PDF
              </>
            )}
          </button>

          <button
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            onClick={() => generatePDF('inline')}
            disabled={loading}
          >
            <EyeIcon className="w-5 h-5" />
            Preview
          </button>
        </div>

        {/* Email Section */}
        <div className="pt-5 border-t border-gray-200">
          <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
            <EnvelopeIcon className="w-4 h-4" />
            Send via Email
          </label>

          <div className="flex gap-2 mb-3">
            <input
              type="email"
              className="flex-1 px-3 py-2 border-2 border-gray-200 rounded-lg text-sm focus:outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all"
              placeholder="recipient@example.com"
              value={emailAddress}
              onChange={(e) => setEmailAddress(e.target.value)}
              disabled={emailStatus === 'sending'}
            />
            <button
              className="px-5 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg text-sm font-semibold flex items-center gap-2 hover:shadow-lg hover:-translate-y-0.5 transition-all disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:translate-y-0"
              onClick={sendEmail}
              disabled={emailStatus === 'sending' || !emailAddress}
            >
              {emailStatus === 'sending' ? (
                <>
                  <ArrowPathIcon className="w-4 h-4 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <EnvelopeIcon className="w-4 h-4" />
                  Send
                </>
              )}
            </button>
          </div>

          {/* Email Status Message */}
          {emailMessage && (
            <div
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm mb-2 ${
                emailStatus === 'success'
                  ? 'bg-green-50 text-green-800'
                  : emailStatus === 'error'
                  ? 'bg-red-50 text-red-800'
                  : 'bg-gray-50 text-gray-800'
              }`}
            >
              {emailStatus === 'success' && <CheckCircleIcon className="w-4 h-4" />}
              {emailStatus === 'error' && <ExclamationCircleIcon className="w-4 h-4" />}
              <span>{emailMessage}</span>
            </div>
          )}

          <p className="text-xs text-gray-500">
            📧 PDF will be attached with calendar file (.ics)
          </p>
        </div>
      </div>

      {/* PDF Inline Viewer Modal */}
      {showViewer && pdfUrl && (
        <div
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-5"
          onClick={() => setShowViewer(false)}
        >
          <div
            className="bg-white rounded-xl w-full max-w-4xl h-[90vh] flex flex-col overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">PDF Preview</h3>
              <button
                className="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-100 transition-colors"
                onClick={() => setShowViewer(false)}
              >
                <XMarkIcon className="w-6 h-6 text-gray-600" />
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <iframe
                src={pdfUrl}
                className="w-full h-full border-0"
                title="PDF Preview"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ItineraryPDFViewer;
