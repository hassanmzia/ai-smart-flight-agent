"""
MCP (Model Context Protocol) Server for Agent-to-Agent Communication
Implements A2A (Agent-to-Agent) communication patterns
"""
import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import redis.asyncio as aioredis
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6384/1')
MCP_PORT = int(os.getenv('MCP_PORT', '8107'))

# Initialize FastAPI app
app = FastAPI(
    title="AI Travel Agent MCP Server",
    description="Model Context Protocol Server for Agent-to-Agent Communication",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis client (initialized on startup)
redis_client: Optional[aioredis.Redis] = None


# Models
class AgentType(str, Enum):
    """Agent types in the system"""
    FLIGHT = "flight"
    HOTEL = "hotel"
    GOAL_BASED = "goal_based"
    UTILITY_BASED = "utility_based"
    MANAGER = "manager"
    CUSTOM = "custom"


class MessageType(str, Enum):
    """Message types for agent communication"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    STATUS_UPDATE = "status_update"


class AgentMessage(BaseModel):
    """Message format for agent-to-agent communication"""
    message_id: str = Field(..., description="Unique message ID")
    from_agent: str = Field(..., description="Sender agent ID")
    to_agent: Optional[str] = Field(None, description="Receiver agent ID (None for broadcast)")
    agent_type: AgentType = Field(..., description="Type of sender agent")
    message_type: MessageType = Field(..., description="Type of message")
    payload: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request-response tracking")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentRegistration(BaseModel):
    """Agent registration model"""
    agent_id: str
    agent_type: AgentType
    capabilities: List[str]
    endpoint: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentContext(BaseModel):
    """Shared context between agents"""
    context_id: str
    session_id: str
    data: Dict[str, Any]
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    ttl: int = Field(default=3600, description="Time to live in seconds")


# Connection manager for WebSocket
class ConnectionManager:
    """Manages WebSocket connections for real-time agent communication"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_subscriptions: Dict[str, List[str]] = {}

    async def connect(self, agent_id: str, websocket: WebSocket):
        """Register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        logger.info(f"Agent {agent_id} connected via WebSocket")

    def disconnect(self, agent_id: str):
        """Remove a WebSocket connection"""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
        logger.info(f"Agent {agent_id} disconnected")

    async def send_message(self, agent_id: str, message: Dict[str, Any]):
        """Send message to specific agent"""
        if agent_id in self.active_connections:
            try:
                await self.active_connections[agent_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {agent_id}: {e}")
                self.disconnect(agent_id)

    async def broadcast(self, message: Dict[str, Any], exclude: Optional[str] = None):
        """Broadcast message to all connected agents"""
        for agent_id, connection in list(self.active_connections.items()):
            if agent_id != exclude:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {agent_id}: {e}")
                    self.disconnect(agent_id)


manager = ConnectionManager()


# Startup and shutdown events
@app.on_event("startup")
async def startup():
    """Initialize Redis connection on startup"""
    global redis_client
    try:
        redis_client = await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("Connected to Redis successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None


@app.on_event("shutdown")
async def shutdown():
    """Close Redis connection on shutdown"""
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "AI Travel Agent MCP Server",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    redis_status = "connected"
    try:
        if redis_client:
            await redis_client.ping()
        else:
            redis_status = "disconnected"
    except Exception as e:
        redis_status = f"error: {str(e)}"

    return {
        "status": "healthy" if redis_status == "connected" else "degraded",
        "redis": redis_status,
        "active_agents": len(manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/agents/register")
async def register_agent(registration: AgentRegistration):
    """Register a new agent in the system"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")

    try:
        agent_key = f"agent:{registration.agent_id}"
        agent_data = registration.model_dump_json()

        # Store agent registration
        await redis_client.setex(agent_key, 3600, agent_data)

        # Add to agent type index
        await redis_client.sadd(f"agents:{registration.agent_type}", registration.agent_id)

        logger.info(f"Agent registered: {registration.agent_id} ({registration.agent_type})")

        return {
            "success": True,
            "agent_id": registration.agent_id,
            "message": "Agent registered successfully"
        }
    except Exception as e:
        logger.error(f"Error registering agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/agents/{agent_id}")
async def unregister_agent(agent_id: str):
    """Unregister an agent"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")

    try:
        agent_key = f"agent:{agent_id}"
        agent_data = await redis_client.get(agent_key)

        if agent_data:
            agent = AgentRegistration.model_validate_json(agent_data)
            await redis_client.delete(agent_key)
            await redis_client.srem(f"agents:{agent.agent_type}", agent_id)

        logger.info(f"Agent unregistered: {agent_id}")

        return {"success": True, "message": "Agent unregistered"}
    except Exception as e:
        logger.error(f"Error unregistering agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents")
async def list_agents(agent_type: Optional[AgentType] = None):
    """List all registered agents"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")

    try:
        if agent_type:
            agent_ids = await redis_client.smembers(f"agents:{agent_type}")
        else:
            # Get all agent types
            agent_ids = set()
            for atype in AgentType:
                type_agents = await redis_client.smembers(f"agents:{atype}")
                agent_ids.update(type_agents)

        agents = []
        for agent_id in agent_ids:
            agent_data = await redis_client.get(f"agent:{agent_id}")
            if agent_data:
                agents.append(json.loads(agent_data))

        return {"agents": agents, "count": len(agents)}
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/messages/send")
async def send_message(message: AgentMessage):
    """Send a message between agents"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")

    try:
        # Store message in Redis
        message_key = f"message:{message.message_id}"
        await redis_client.setex(message_key, 3600, message.model_dump_json())

        # If to_agent is specified, send directly
        if message.to_agent:
            await manager.send_message(message.to_agent, message.model_dump())

            # Also store in agent's message queue
            queue_key = f"agent_queue:{message.to_agent}"
            await redis_client.lpush(queue_key, message.model_dump_json())
            await redis_client.expire(queue_key, 3600)
        else:
            # Broadcast to all agents
            await manager.broadcast(message.model_dump(), exclude=message.from_agent)

        logger.info(f"Message sent: {message.message_id} from {message.from_agent}")

        return {"success": True, "message_id": message.message_id}
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/messages/{agent_id}")
async def get_agent_messages(agent_id: str, limit: int = 10):
    """Get messages for a specific agent"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")

    try:
        queue_key = f"agent_queue:{agent_id}"
        messages = await redis_client.lrange(queue_key, 0, limit - 1)

        return {
            "agent_id": agent_id,
            "messages": [json.loads(msg) for msg in messages],
            "count": len(messages)
        }
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/context/create")
async def create_context(context: AgentContext):
    """Create or update shared context"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")

    try:
        context_key = f"context:{context.context_id}"
        await redis_client.setex(context_key, context.ttl, context.model_dump_json())

        logger.info(f"Context created: {context.context_id}")

        return {"success": True, "context_id": context.context_id}
    except Exception as e:
        logger.error(f"Error creating context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/context/{context_id}")
async def get_context(context_id: str):
    """Get shared context"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")

    try:
        context_key = f"context:{context_id}"
        context_data = await redis_client.get(context_key)

        if not context_data:
            raise HTTPException(status_code=404, detail="Context not found")

        return json.loads(context_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for real-time agent communication"""
    await manager.connect(agent_id, websocket)

    try:
        while True:
            # Receive message from agent
            data = await websocket.receive_json()

            # Process message
            message = AgentMessage(**data)

            # Store and route message
            if redis_client:
                message_key = f"message:{message.message_id}"
                await redis_client.setex(message_key, 3600, message.model_dump_json())

            # Send to target or broadcast
            if message.to_agent:
                await manager.send_message(message.to_agent, message.model_dump())
            else:
                await manager.broadcast(message.model_dump(), exclude=agent_id)

    except WebSocketDisconnect:
        manager.disconnect(agent_id)
    except Exception as e:
        logger.error(f"WebSocket error for {agent_id}: {e}")
        manager.disconnect(agent_id)


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=MCP_PORT,
        log_level="info",
        reload=False
    )
