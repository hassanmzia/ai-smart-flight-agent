import { useState, useRef, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  DocumentArrowUpIcon,
  TrashIcon,
  ArrowPathIcon,
  XMarkIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import { API_ENDPOINTS, QUERY_KEYS } from '@/utils/constants';
import { cn } from '@/utils/helpers';
import { LoadingSpinner } from '@/components/common/Loading';

interface RAGDocument {
  id: number;
  title: string;
  description: string;
  file_url: string;
  file_type: string;
  file_size: number;
  status: 'pending' | 'processing' | 'indexed' | 'failed';
  error_message: string;
  chunk_count: number;
  scope: 'global' | 'user';
  tags: string[];
  uploaded_by_email: string;
  created_at: string;
}

const STATUS_CONFIG = {
  pending: { icon: ClockIcon, color: 'text-yellow-500', bg: 'bg-yellow-50 dark:bg-yellow-900/20', label: 'Pending' },
  processing: { icon: ArrowPathIcon, color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20', label: 'Processing' },
  indexed: { icon: CheckCircleIcon, color: 'text-green-500', bg: 'bg-green-50 dark:bg-green-900/20', label: 'Indexed' },
  failed: { icon: ExclamationCircleIcon, color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-900/20', label: 'Failed' },
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface DocumentManagerProps {
  isOpen: boolean;
  onClose: () => void;
}

const DocumentManager = ({ isOpen, onClose }: DocumentManagerProps) => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [scope, setScope] = useState<'global' | 'user'>('global');
  const [uploadError, setUploadError] = useState('');

  // Fetch documents
  const { data: documents, isLoading } = useQuery({
    queryKey: QUERY_KEYS.RAG_DOCUMENTS,
    queryFn: async () => {
      const res = await api.get(`${API_ENDPOINTS.AGENT.DOCUMENTS}/`);
      return (res.data?.results || res.data || []) as RAGDocument[];
    },
    enabled: isOpen,
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const res = await api.post(`${API_ENDPOINTS.AGENT.DOCUMENTS}/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.RAG_DOCUMENTS });
      setTitle('');
      setDescription('');
      setUploadError('');
      if (fileInputRef.current) fileInputRef.current.value = '';
    },
    onError: (err: any) => {
      setUploadError(err?.response?.data?.file?.[0] || err?.message || 'Upload failed');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`${API_ENDPOINTS.AGENT.DOCUMENTS}/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.RAG_DOCUMENTS });
    },
  });

  // Reindex mutation
  const reindexMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await api.post(`${API_ENDPOINTS.AGENT.DOCUMENTS}/${id}/reindex/`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.RAG_DOCUMENTS });
    },
  });

  const handleUpload = useCallback(() => {
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      setUploadError('Please select a file');
      return;
    }
    if (!title.trim()) {
      setUploadError('Please enter a title');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title.trim());
    formData.append('description', description.trim());
    formData.append('scope', scope);

    setUploadError('');
    uploadMutation.mutate(formData);
  }, [title, description, scope, uploadMutation]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <DocumentTextIcon className="h-5 w-5 text-primary-600" />
            <h2 className="font-semibold text-gray-900 dark:text-white">
              Knowledge Base Documents
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Upload form */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 space-y-3">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Upload company policies, travel guides, or any document. The AI assistant will use them to answer questions.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Document title *"
              className="px-3 py-2 text-sm border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white border-gray-200 dark:border-gray-600 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as 'global' | 'user')}
              className="px-3 py-2 text-sm border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white border-gray-200 dark:border-gray-600 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="global">All users (company-wide)</option>
              <option value="user">Only me</option>
            </select>
          </div>

          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (optional)"
            className="w-full px-3 py-2 text-sm border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white border-gray-200 dark:border-gray-600 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />

          <div className="flex items-center space-x-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.md,.docx,.csv"
              className="flex-1 text-sm text-gray-500 dark:text-gray-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 dark:file:bg-primary-900/30 dark:file:text-primary-300"
            />
            <button
              onClick={handleUpload}
              disabled={uploadMutation.isPending}
              className="flex items-center space-x-1.5 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm font-medium transition-colors"
            >
              {uploadMutation.isPending ? (
                <LoadingSpinner className="h-4 w-4" />
              ) : (
                <DocumentArrowUpIcon className="h-4 w-4" />
              )}
              <span>{uploadMutation.isPending ? 'Uploading...' : 'Upload'}</span>
            </button>
          </div>

          {uploadError && (
            <p className="text-xs text-red-500">{uploadError}</p>
          )}
          {uploadMutation.isSuccess && (
            <p className="text-xs text-green-600">Document uploaded and indexed successfully!</p>
          )}
        </div>

        {/* Document list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner className="h-6 w-6 text-primary-500" />
            </div>
          ) : !documents || documents.length === 0 ? (
            <div className="text-center py-8 text-gray-400 dark:text-gray-500">
              <DocumentTextIcon className="h-10 w-10 mx-auto mb-2" />
              <p className="text-sm">No documents uploaded yet.</p>
              <p className="text-xs mt-1">
                Upload PDFs, text files, or Word documents to enhance the AI assistant.
              </p>
            </div>
          ) : (
            documents.map((doc) => {
              const statusConfig = STATUS_CONFIG[doc.status];
              const StatusIcon = statusConfig.icon;

              return (
                <div
                  key={doc.id}
                  className={cn(
                    'flex items-start justify-between p-3 rounded-lg border',
                    'border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50'
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-sm text-gray-900 dark:text-white truncate">
                        {doc.title}
                      </span>
                      <span className={cn(
                        'inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-medium',
                        statusConfig.bg, statusConfig.color
                      )}>
                        <StatusIcon className="h-3 w-3" />
                        <span>{statusConfig.label}</span>
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 mt-1 text-xs text-gray-400 dark:text-gray-500">
                      <span className="uppercase">{doc.file_type}</span>
                      <span>{formatFileSize(doc.file_size)}</span>
                      {doc.chunk_count > 0 && (
                        <span>{doc.chunk_count} chunks</span>
                      )}
                      <span className={doc.scope === 'global' ? 'text-blue-500' : 'text-gray-400'}>
                        {doc.scope === 'global' ? 'Company-wide' : 'Personal'}
                      </span>
                    </div>
                    {doc.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                        {doc.description}
                      </p>
                    )}
                    {doc.error_message && (
                      <p className="text-xs text-red-500 mt-1">{doc.error_message}</p>
                    )}
                  </div>

                  <div className="flex items-center space-x-1 ml-2">
                    {doc.status === 'failed' && (
                      <button
                        onClick={() => reindexMutation.mutate(doc.id)}
                        disabled={reindexMutation.isPending}
                        className="p-1.5 text-gray-400 hover:text-blue-600 transition-colors"
                        title="Retry indexing"
                      >
                        <ArrowPathIcon className={cn(
                          'h-4 w-4',
                          reindexMutation.isPending && 'animate-spin'
                        )} />
                      </button>
                    )}
                    <button
                      onClick={() => {
                        if (confirm('Delete this document? This will also remove it from the AI knowledge base.')) {
                          deleteMutation.mutate(doc.id);
                        }
                      }}
                      disabled={deleteMutation.isPending}
                      className="p-1.5 text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete document"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentManager;
