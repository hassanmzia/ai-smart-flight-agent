"""
WebSocket consumers for real-time notifications.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.
    Handles connection, authentication, and message broadcasting.
    """

    async def connect(self):
        """
        Handle WebSocket connection.
        """
        # Get user from scope (set by authentication middleware)
        self.user = self.scope.get('user')

        # Reject anonymous users
        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            logger.warning("WebSocket connection rejected: User not authenticated")
            await self.close(code=4001)
            return

        # Create unique group name for this user
        self.group_name = f'user_{self.user.id}'

        # Add this connection to the user's group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Accept the connection
        await self.accept()

        logger.info(f"WebSocket connected: User {self.user.id}, Channel {self.channel_name}")

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to notification service',
            'user_id': str(self.user.id)
        }))

        # Send unread notification count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        if hasattr(self, 'group_name'):
            # Remove this connection from the user's group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

            logger.info(f"WebSocket disconnected: User {self.user.id if self.user else 'Unknown'}, Code {close_code}")

    async def receive(self, text_data):
        """
        Handle incoming messages from WebSocket.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            logger.debug(f"WebSocket message received from user {self.user.id}: {message_type}")

            # Route message based on type
            if message_type == 'mark_read':
                await self.handle_mark_read(data)

            elif message_type == 'mark_all_read':
                await self.handle_mark_all_read()

            elif message_type == 'get_notifications':
                await self.handle_get_notifications(data)

            elif message_type == 'ping':
                # Respond to keep-alive ping
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))

            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))

    async def notification_message(self, event):
        """
        Handler for notification messages sent to the group.
        This is called when a notification is broadcast to the user's group.
        """
        notification = event.get('notification', {})

        logger.debug(f"Broadcasting notification to user {self.user.id}: {notification.get('id')}")

        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': notification
        }))

    async def notification_update(self, event):
        """
        Handler for notification update messages (e.g., read status changed).
        """
        await self.send(text_data=json.dumps({
            'type': 'notification_update',
            'notification_id': event.get('notification_id'),
            'updates': event.get('updates', {})
        }))

    async def handle_mark_read(self, data):
        """
        Handle marking a notification as read.
        """
        notification_id = data.get('notification_id')

        if not notification_id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'notification_id is required'
            }))
            return

        try:
            success = await self.mark_notification_read(notification_id)

            if success:
                await self.send(text_data=json.dumps({
                    'type': 'marked_read',
                    'notification_id': notification_id
                }))

                # Update unread count
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': unread_count
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Failed to mark notification as read'
                }))

        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def handle_mark_all_read(self):
        """
        Handle marking all notifications as read.
        """
        try:
            count = await self.mark_all_notifications_read()

            await self.send(text_data=json.dumps({
                'type': 'marked_all_read',
                'count': count
            }))

            # Update unread count to 0
            await self.send(text_data=json.dumps({
                'type': 'unread_count',
                'count': 0
            }))

        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def handle_get_notifications(self, data):
        """
        Handle fetching notifications.
        """
        limit = data.get('limit', 20)
        offset = data.get('offset', 0)
        unread_only = data.get('unread_only', False)

        try:
            notifications = await self.get_notifications(limit, offset, unread_only)

            await self.send(text_data=json.dumps({
                'type': 'notifications',
                'notifications': notifications,
                'limit': limit,
                'offset': offset
            }))

        except Exception as e:
            logger.error(f"Error fetching notifications: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    @database_sync_to_async
    def get_unread_count(self):
        """
        Get count of unread notifications for the user.
        """
        from .models import Notification
        return Notification.objects.filter(user=self.user, is_read=False).count()

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """
        Mark a notification as read.
        """
        from .models import Notification
        from django.utils import timezone

        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            return True
        except Notification.DoesNotExist:
            logger.warning(f"Notification {notification_id} not found for user {self.user.id}")
            return False

    @database_sync_to_async
    def mark_all_notifications_read(self):
        """
        Mark all notifications as read for the user.
        """
        from .models import Notification
        from django.utils import timezone

        return Notification.objects.filter(
            user=self.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

    @database_sync_to_async
    def get_notifications(self, limit, offset, unread_only):
        """
        Fetch notifications for the user.
        """
        from .models import Notification

        queryset = Notification.objects.filter(user=self.user)

        if unread_only:
            queryset = queryset.filter(is_read=False)

        notifications = queryset.order_by('-created_at')[offset:offset + limit]

        return [
            {
                'id': str(n.id),
                'type': n.notification_type,
                'title': n.title,
                'message': n.message,
                'data': n.data,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
                'read_at': n.read_at.isoformat() if n.read_at else None,
            }
            for n in notifications
        ]


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time streaming chat with AI agent.
    Supports token-by-token streaming, conversation memory, and structured responses.
    """

    async def connect(self):
        self.user = self.scope.get('user')

        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            logger.warning("Chat WebSocket connection rejected: User not authenticated")
            await self.close(code=4001)
            return

        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')

        if self.conversation_id:
            self.room_group_name = f'chat_{self.conversation_id}'
        else:
            conversation = await self.create_conversation()
            self.conversation_id = str(conversation.id)
            self.room_group_name = f'chat_{self.conversation_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        logger.info(f"Chat WebSocket connected: User {self.user.id}, Conversation {self.conversation_id}")

        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'conversation_id': self.conversation_id
        }))

        # Auto-load recent history
        history = await self.get_conversation_history(limit=50)
        if history:
            await self.send(text_data=json.dumps({
                'type': 'conversation_history',
                'messages': history,
                'conversation_id': self.conversation_id
            }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"Chat WebSocket disconnected: Conversation {self.conversation_id}, Code {close_code}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'chat_message':
                message = data.get('message', '').strip()
                if not message:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Message content is required'
                    }))
                    return
                await self.process_streaming_message(message)

            elif message_type == 'load_history':
                limit = data.get('limit', 50)
                offset = data.get('offset', 0)
                history = await self.get_conversation_history(limit=limit, offset=offset)
                await self.send(text_data=json.dumps({
                    'type': 'conversation_history',
                    'messages': history,
                    'conversation_id': self.conversation_id
                }))

            elif message_type == 'new_conversation':
                conversation = await self.create_conversation()
                self.conversation_id = str(conversation.id)
                old_group = self.room_group_name
                self.room_group_name = f'chat_{self.conversation_id}'
                await self.channel_layer.group_discard(old_group, self.channel_name)
                await self.channel_layer.group_add(self.room_group_name, self.channel_name)
                await self.send(text_data=json.dumps({
                    'type': 'new_conversation',
                    'conversation_id': self.conversation_id
                }))

            elif message_type == 'typing':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'user_typing', 'user_id': str(self.user.id)}
                )

            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))

            else:
                logger.warning(f"Unknown chat message type: {message_type}")

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error', 'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error handling chat message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error', 'message': 'Internal server error'
            }))

    async def process_streaming_message(self, message):
        """Process user message and stream AI response token-by-token."""
        import uuid as _uuid
        from datetime import datetime

        # Save user message
        user_msg = await self.save_message(message, 'user')

        # Send acknowledgment
        await self.send(text_data=json.dumps({
            'type': 'message_sent',
            'message': {
                'id': str(user_msg.id),
                'content': message,
                'sender': 'user',
                'timestamp': user_msg.created_at.isoformat()
            }
        }))

        # Send typing indicator
        await self.send(text_data=json.dumps({'type': 'agent_typing'}))

        # Generate AI response with streaming
        agent_message_id = str(_uuid.uuid4())
        full_response = ""
        start_time = datetime.utcnow()

        try:
            # Get conversation context for memory
            context = await self.build_conversation_context()

            # Stream response from LLM
            async for token in self.stream_ai_response(message, context):
                full_response += token
                await self.send(text_data=json.dumps({
                    'type': 'agent_stream',
                    'token': token,
                    'message_id': agent_message_id
                }))

            # Calculate response time
            elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Save agent message to DB
            agent_msg = await self.save_message(
                full_response, 'agent',
                response_time_ms=elapsed_ms
            )

            # Send completion signal with streaming ID so frontend can
            # replace the streaming placeholder with the final message.
            await self.send(text_data=json.dumps({
                'type': 'agent_message_complete',
                'streaming_message_id': agent_message_id,
                'message': {
                    'id': str(agent_msg.id),
                    'content': full_response,
                    'sender': 'agent',
                    'timestamp': agent_msg.created_at.isoformat(),
                    'response_time_ms': elapsed_ms
                }
            }))

        except Exception as e:
            logger.error(f"Error streaming AI response: {str(e)}")
            error_msg = "I'm sorry, I encountered an error processing your request. Please try again."
            agent_msg = await self.save_message(error_msg, 'agent')
            await self.send(text_data=json.dumps({
                'type': 'agent_message_complete',
                'message': {
                    'id': str(agent_msg.id),
                    'content': error_msg,
                    'sender': 'agent',
                    'timestamp': agent_msg.created_at.isoformat(),
                    'error': True
                }
            }))

    async def stream_ai_response(self, message, context):
        """Stream AI response using real OpenAI streaming when available."""
        import asyncio
        import os

        openai_key = os.getenv('OPENAI_API_KEY', '')
        if not openai_key or openai_key in ('your_openai_api_key_here', ''):
            # Fallback: generate full response then simulate streaming
            response_text = await database_sync_to_async(self._generate_ai_response)(message, context)
            words = response_text.split(' ')
            for i, word in enumerate(words):
                yield (' ' + word) if i > 0 else word
                await asyncio.sleep(0.02)
            return

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=openai_key)

            # Build RAG context
            rag_context = ""
            try:
                from apps.agents.chat_rag import get_user_data_rag
                rag = await database_sync_to_async(get_user_data_rag)()
                rag_context = await database_sync_to_async(rag.retrieve)(self.user, message, n_results=5)
            except Exception:
                pass

            system_prompt = f"""You are an expert AI travel planning assistant. You help users plan trips, find flights, hotels, restaurants, and activities. You are knowledgeable, friendly, and proactive.

When a user asks about trip planning:
- Ask clarifying questions about destination, dates, budget, and preferences
- Suggest specific flights, hotels, and activities when you have enough info
- Consider weather, safety, local events, and cultural factors
- Provide cost estimates and budget breakdowns
- Offer alternative options at different price points

{f"User's travel data for context:{chr(10)}{rag_context}" if rag_context else ""}

Keep responses concise but helpful. Use markdown formatting for lists and emphasis. If the user's request is vague, ask 1-2 clarifying questions."""

            messages = [{"role": "system", "content": system_prompt}]
            for msg in context.get('history', []):
                role = 'assistant' if msg['sender'] == 'agent' else 'user'
                messages.append({"role": role, "content": msg['content']})
            messages.append({"role": "user", "content": message})

            model_name = getattr(
                settings, 'AGENT_CONFIG', {}
            ).get('MODEL', 'gpt-4o-mini')

            stream = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content

        except Exception as e:
            logger.warning(f"Real streaming failed, falling back: {e}")
            response_text = await database_sync_to_async(self._generate_ai_response)(message, context)
            words = response_text.split(' ')
            for i, word in enumerate(words):
                yield (' ' + word) if i > 0 else word
                await asyncio.sleep(0.02)

    def _generate_ai_response(self, message, context):
        """Generate AI response synchronously using LangChain (called from sync context)."""
        import os
        from django.conf import settings

        try:
            openai_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
            if not openai_key or openai_key in ('your_openai_api_key_here', ''):
                return self._fallback_response(message)

            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage as HMsg, SystemMessage as SMsg, AIMessage as AMsg

            model = ChatOpenAI(
                model=getattr(settings, 'AGENT_CONFIG', {}).get('MODEL', 'gpt-4o-mini'),
                temperature=0.7,
                api_key=openai_key,
                request_timeout=60,
            )

            # Build RAG context
            rag_context = ""
            try:
                from apps.agents.chat_rag import get_user_data_rag
                rag = get_user_data_rag()
                rag_context = rag.retrieve(self.user, message, n_results=5)
            except Exception as e:
                logger.debug(f"RAG retrieval failed: {e}")

            system_prompt = f"""You are an expert AI travel planning assistant. You help users plan trips, find flights, hotels, restaurants, and activities. You are knowledgeable, friendly, and proactive.

When a user asks about trip planning:
- Ask clarifying questions about destination, dates, budget, and preferences
- Suggest specific flights, hotels, and activities when you have enough info
- Consider weather, safety, local events, and cultural factors
- Provide cost estimates and budget breakdowns
- Offer alternative options at different price points

{f"User's travel data for context:{chr(10)}{rag_context}" if rag_context else ""}

Keep responses concise but helpful. Use markdown formatting for lists and emphasis. If the user's request is vague, ask 1-2 clarifying questions."""

            messages = [SMsg(content=system_prompt)]

            # Add conversation history
            for msg in context.get('history', []):
                if msg['sender'] == 'user':
                    messages.append(HMsg(content=msg['content']))
                elif msg['sender'] == 'agent':
                    messages.append(AMsg(content=msg['content']))

            messages.append(HMsg(content=message))

            response = model.invoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            return self._fallback_response(message)

    def _fallback_response(self, message):
        """Provide a helpful response when LLM is unavailable."""
        msg_lower = message.lower()
        if any(w in msg_lower for w in ['flight', 'fly', 'airport']):
            return "I'd love to help you find flights! To search, please visit the **Flight Search** page from the navigation menu. You can search by origin, destination, dates, and number of passengers. Would you like me to help with anything else?"
        elif any(w in msg_lower for w in ['hotel', 'stay', 'accommodation']):
            return "For hotel searches, head to the **Hotel Search** page where you can filter by location, dates, guests, and budget. I can help you compare options once you have results!"
        elif any(w in msg_lower for w in ['trip', 'plan', 'itinerary', 'vacation']):
            return "I can help you plan your trip! Try the **AI Trip Planner** page for a complete itinerary with flights, hotels, restaurants, and attractions. Just enter your destination, dates, and budget to get started."
        else:
            return "I'm your AI travel assistant! I can help with:\n\n- **Trip Planning** - Complete itineraries with flights, hotels & activities\n- **Flight Search** - Find the best flight deals\n- **Hotel Search** - Compare accommodations\n- **Restaurant Recommendations** - Local dining spots\n- **Travel Tips** - Weather, safety, packing advice\n\nWhat would you like help with?"

    async def build_conversation_context(self):
        """Build context from conversation history for LLM memory."""
        history = await self.get_conversation_history(limit=50)
        return {'history': history}

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def user_typing(self, event):
        if event.get('user_id') != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id']
            }))

    @database_sync_to_async
    def create_conversation(self):
        from apps.agents.models import AgentConversation
        return AgentConversation.objects.create(
            user=self.user,
            status='active'
        )

    @database_sync_to_async
    def save_message(self, content, sender_type, response_time_ms=None):
        from apps.agents.models import AgentConversation, AgentMessage
        conversation = AgentConversation.objects.get(id=self.conversation_id)
        return AgentMessage.objects.create(
            conversation=conversation,
            content=content,
            sender_type=sender_type,
            user=self.user if sender_type == 'user' else None,
            response_time_ms=response_time_ms,
        )

    @database_sync_to_async
    def get_conversation_history(self, limit=50, offset=0):
        from apps.agents.models import AgentMessage
        messages = AgentMessage.objects.filter(
            conversation_id=self.conversation_id
        ).order_by('created_at')[offset:offset + limit]
        return [
            {
                'id': str(m.id),
                'content': m.content,
                'sender': m.sender_type,
                'message_type': m.message_type,
                'metadata': m.metadata,
                'timestamp': m.created_at.isoformat(),
            }
            for m in messages
        ]
