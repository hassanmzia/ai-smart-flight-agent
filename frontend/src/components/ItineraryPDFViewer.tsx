/**
 * ItineraryPDFViewer Component
 * Professional PDF viewer for travel itineraries
 * Features: Inline viewing, download, email, theme selection
 */

import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Mail,
  Eye,
  Palette,
  Loader2,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';

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
    { name: 'pumpkin', label: 'Pumpkin Orange', color: '#f78b1f' },
    { name: 'ocean', label: 'Ocean Blue', color: '#0ea5e9' },
    { name: 'forest', label: 'Forest Green', color: '#10b981' }
  ] as const;

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
        // Download file
        const a = document.createElement('a');
        a.href = url;
        a.download = `itinerary_${destination.replace(/\s/g, '_')}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } else {
        // Show inline viewer
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

      // Reset status after 5 seconds
      setTimeout(() => {
        setEmailStatus('idle');
        setEmailMessage('');
      }, 5000);
    } catch (error: any) {
      setEmailStatus('error');
      setEmailMessage(error.response?.data?.error || 'Failed to send email');

      // Reset status after 5 seconds
      setTimeout(() => {
        setEmailStatus('idle');
        setEmailMessage('');
      }, 5000);
    }
  };

  return (
    <div className="pdf-viewer-container">
      {/* PDF Options Panel */}
      <div className="pdf-options-panel">
        <div className="panel-header">
          <FileText className="icon" />
          <h3>Export Itinerary</h3>
        </div>

        {/* Theme Selection */}
        <div className="option-group">
          <label className="option-label">
            <Palette className="icon-small" />
            PDF Theme
          </label>
          <div className="theme-selector">
            {themes.map((theme) => (
              <button
                key={theme.name}
                className={`theme-button ${selectedTheme === theme.name ? 'active' : ''}`}
                onClick={() => setSelectedTheme(theme.name as PDFTheme)}
                style={{
                  borderColor: selectedTheme === theme.name ? theme.color : '#e5e7eb',
                  backgroundColor: selectedTheme === theme.name ? `${theme.color}10` : 'white'
                }}
              >
                <div
                  className="theme-color-dot"
                  style={{ backgroundColor: theme.color }}
                />
                {theme.label}
              </button>
            ))}
          </div>
        </div>

        {/* QR Code Option */}
        <div className="option-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={includeQR}
              onChange={(e) => setIncludeQR(e.target.checked)}
            />
            <span>Include QR code for online version</span>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="action-buttons">
          <button
            className="btn btn-primary"
            onClick={() => generatePDF('download')}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="icon-spin" />
                Generating...
              </>
            ) : (
              <>
                <Download className="icon" />
                Download PDF
              </>
            )}
          </button>

          <button
            className="btn btn-secondary"
            onClick={() => generatePDF('inline')}
            disabled={loading}
          >
            <Eye className="icon" />
            Preview
          </button>
        </div>

        {/* Email Section */}
        <div className="email-section">
          <label className="option-label">
            <Mail className="icon-small" />
            Send via Email
          </label>

          <div className="email-input-group">
            <input
              type="email"
              className="email-input"
              placeholder="recipient@example.com"
              value={emailAddress}
              onChange={(e) => setEmailAddress(e.target.value)}
              disabled={emailStatus === 'sending'}
            />
            <button
              className="btn btn-email"
              onClick={sendEmail}
              disabled={emailStatus === 'sending' || !emailAddress}
            >
              {emailStatus === 'sending' ? (
                <>
                  <Loader2 className="icon-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Mail className="icon" />
                  Send
                </>
              )}
            </button>
          </div>

          {/* Email Status Message */}
          {emailMessage && (
            <div className={`status-message ${emailStatus}`}>
              {emailStatus === 'success' && <CheckCircle2 className="icon-small" />}
              {emailStatus === 'error' && <AlertCircle className="icon-small" />}
              <span>{emailMessage}</span>
            </div>
          )}

          <p className="email-note">
            📧 PDF will be attached with calendar file (.ics)
          </p>
        </div>
      </div>

      {/* PDF Inline Viewer Modal */}
      {showViewer && pdfUrl && (
        <div className="pdf-viewer-modal" onClick={() => setShowViewer(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>PDF Preview</h3>
              <button
                className="close-button"
                onClick={() => setShowViewer(false)}
              >
                ×
              </button>
            </div>
            <div className="pdf-viewer-frame">
              <iframe
                src={pdfUrl}
                className="pdf-iframe"
                title="PDF Preview"
              />
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .pdf-viewer-container {
          width: 100%;
          max-width: 600px;
          margin: 0 auto;
        }

        .pdf-options-panel {
          background: white;
          border-radius: 12px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          padding: 24px;
          border: 1px solid #e5e7eb;
        }

        .panel-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 24px;
          padding-bottom: 16px;
          border-bottom: 2px solid #f3f4f6;
        }

        .panel-header h3 {
          margin: 0;
          font-size: 20px;
          font-weight: 700;
          color: #111827;
        }

        .option-group {
          margin-bottom: 20px;
        }

        .option-label {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          font-weight: 600;
          color: #374151;
          margin-bottom: 12px;
        }

        .theme-selector {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .theme-button {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          background: white;
          cursor: pointer;
          transition: all 0.2s;
          font-size: 14px;
          font-weight: 500;
        }

        .theme-button:hover {
          transform: translateY(-1px);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .theme-color-dot {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          border: 2px solid white;
          box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1);
        }

        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          font-size: 14px;
          color: #374151;
        }

        .checkbox-label input[type="checkbox"] {
          width: 18px;
          height: 18px;
          cursor: pointer;
        }

        .action-buttons {
          display: flex;
          gap: 12px;
          margin-bottom: 24px;
        }

        .btn {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 12px 16px;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-primary {
          background: linear-gradient(135deg, #d46d00, #f78b1f);
          color: white;
          box-shadow: 0 4px 12px rgba(247, 139, 31, 0.3);
        }

        .btn-primary:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 6px 16px rgba(247, 139, 31, 0.4);
        }

        .btn-secondary {
          background: #f3f4f6;
          color: #374151;
        }

        .btn-secondary:hover:not(:disabled) {
          background: #e5e7eb;
        }

        .email-section {
          padding-top: 20px;
          border-top: 1px solid #e5e7eb;
        }

        .email-input-group {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
        }

        .email-input {
          flex: 1;
          padding: 10px 14px;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          font-size: 14px;
          transition: border-color 0.2s;
        }

        .email-input:focus {
          outline: none;
          border-color: #f78b1f;
        }

        .btn-email {
          padding: 10px 20px;
          background: linear-gradient(135deg, #0ea5e9, #0284c7);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: all 0.2s;
        }

        .btn-email:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
        }

        .btn-email:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .status-message {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 14px;
          border-radius: 6px;
          font-size: 13px;
          margin-bottom: 8px;
        }

        .status-message.success {
          background: #d1fae5;
          color: #065f46;
        }

        .status-message.error {
          background: #fee2e2;
          color: #991b1b;
        }

        .email-note {
          font-size: 12px;
          color: #6b7280;
          margin: 0;
        }

        .icon {
          width: 20px;
          height: 20px;
        }

        .icon-small {
          width: 16px;
          height: 16px;
        }

        .icon-spin {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        /* PDF Viewer Modal */
        .pdf-viewer-modal {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.75);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 20px;
        }

        .modal-content {
          background: white;
          border-radius: 12px;
          width: 100%;
          max-width: 900px;
          height: 90vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .modal-header h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }

        .close-button {
          background: none;
          border: none;
          font-size: 28px;
          cursor: pointer;
          color: #6b7280;
          padding: 0;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 4px;
        }

        .close-button:hover {
          background: #f3f4f6;
        }

        .pdf-viewer-frame {
          flex: 1;
          overflow: hidden;
        }

        .pdf-iframe {
          width: 100%;
          height: 100%;
          border: none;
        }
      `}</style>
    </div>
  );
};

export default ItineraryPDFViewer;
