import { useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as notificationService from '@/services/notificationService';
import useNotificationStore from '@/store/notificationStore';
import { QUERY_KEYS } from '@/utils/constants';
import toast from 'react-hot-toast';

/**
 * Hook to manage notifications
 */
export const useNotifications = () => {
  const queryClient = useQueryClient();
  const { notifications, unreadCount, markAsRead, markAllAsRead, removeNotification } =
    useNotificationStore();

  // Fetch notifications
  const { data: notificationsData, isPending: isLoading } = useQuery({
    queryKey: QUERY_KEYS.NOTIFICATIONS,
    queryFn: () => notificationService.getNotifications(),
  });

  // Sync with store when data loads
  useEffect(() => {
    if (notificationsData?.items) {
      notificationsData.items.forEach((notification: any) => {
        useNotificationStore.getState().addNotification(notification);
      });
    }
  }, [notificationsData]);

  // Fetch unread count
  useQuery({
    queryKey: [...QUERY_KEYS.NOTIFICATIONS, 'unread-count'],
    queryFn: notificationService.getUnreadCount,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Mark as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: notificationService.markAsRead,
  });

  // Mark all as read mutation
  const markAllAsReadMutation = useMutation({
    mutationFn: notificationService.markAllAsRead,
  });

  // Delete notification mutation
  const deleteNotificationMutation = useMutation({
    mutationFn: notificationService.deleteNotification,
  });

  const handleMarkAsRead = useCallback(
    async (notificationId: string) => {
      try {
        await markAsReadMutation.mutateAsync(notificationId);
        markAsRead(notificationId);
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.NOTIFICATIONS });
      } catch (error) {
        toast.error('Failed to mark notification as read');
      }
    },
    [markAsReadMutation, markAsRead, queryClient]
  );

  const handleMarkAllAsRead = useCallback(async () => {
    try {
      await markAllAsReadMutation.mutateAsync();
      markAllAsRead();
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.NOTIFICATIONS });
      toast.success('All notifications marked as read');
    } catch (error) {
      toast.error('Failed to mark all notifications as read');
    }
  }, [markAllAsReadMutation, markAllAsRead, queryClient]);

  const handleDeleteNotification = useCallback(
    async (notificationId: string) => {
      try {
        await deleteNotificationMutation.mutateAsync(notificationId);
        removeNotification(notificationId);
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.NOTIFICATIONS });
        toast.success('Notification deleted');
      } catch (error) {
        toast.error('Failed to delete notification');
      }
    },
    [deleteNotificationMutation, removeNotification, queryClient]
  );

  return {
    notifications,
    unreadCount,
    isLoading,
    markAsRead: handleMarkAsRead,
    markAllAsRead: handleMarkAllAsRead,
    deleteNotification: handleDeleteNotification,
  };
};

/**
 * Hook to show toast notifications
 */
export const useToast = () => {
  const showSuccess = useCallback((message: string) => {
    toast.success(message);
  }, []);

  const showError = useCallback((message: string) => {
    toast.error(message);
  }, []);

  const showInfo = useCallback((message: string) => {
    toast(message);
  }, []);

  const showLoading = useCallback((message: string) => {
    return toast.loading(message);
  }, []);

  const dismiss = useCallback((toastId?: string) => {
    toast.dismiss(toastId);
  }, []);

  return {
    showSuccess,
    showError,
    showInfo,
    showLoading,
    dismiss,
  };
};
