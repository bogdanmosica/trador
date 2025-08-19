"""
Data Stream Infrastructure

Core streaming infrastructure for real-time market data with event-driven
architecture, connection management, and data normalization.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Callable, Any, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging

from ..models import Candle, Ticker, OrderBook, Trade


logger = logging.getLogger(__name__)


class StreamEvent(Enum):
    """Stream event types."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    DATA_RECEIVED = "data_received"
    HEARTBEAT = "heartbeat"
    RECONNECTING = "reconnecting"


@dataclass
class StreamConfig:
    """Configuration for data streaming."""
    
    # Connection settings
    url: str
    reconnect_attempts: int = 5
    reconnect_delay: float = 1.0
    reconnect_backoff: float = 2.0
    max_reconnect_delay: float = 60.0
    
    # Heartbeat and keepalive
    heartbeat_interval: float = 30.0
    ping_interval: float = 20.0
    pong_timeout: float = 10.0
    
    # Data handling
    buffer_size: int = 1000
    max_message_size: int = 1024 * 1024  # 1MB
    
    # Quality of Service
    enable_compression: bool = True
    subscription_timeout: float = 10.0
    
    # Authentication (if needed)
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'url': self.url,
            'reconnect_attempts': self.reconnect_attempts,
            'reconnect_delay': self.reconnect_delay,
            'reconnect_backoff': self.reconnect_backoff,
            'max_reconnect_delay': self.max_reconnect_delay,
            'heartbeat_interval': self.heartbeat_interval,
            'ping_interval': self.ping_interval,
            'pong_timeout': self.pong_timeout,
            'buffer_size': self.buffer_size,
            'max_message_size': self.max_message_size,
            'enable_compression': self.enable_compression,
            'subscription_timeout': self.subscription_timeout
        }


@dataclass
class StreamMessage:
    """Wrapper for stream messages with metadata."""
    data: Any
    timestamp: datetime
    stream_id: str
    message_type: str
    raw_message: Dict[str, Any] = field(default_factory=dict)


class DataStream:
    """
    Real-time data stream with WebSocket support.
    
    Provides reliable real-time market data streaming with automatic
    reconnection, heartbeat monitoring, and event-driven architecture.
    """
    
    def __init__(
        self,
        config: StreamConfig,
        stream_id: Optional[str] = None
    ):
        """
        Initialize data stream.
        
        Args:
            config (StreamConfig): Stream configuration
            stream_id (Optional[str]): Unique stream identifier
        """
        self.config = config
        self.stream_id = stream_id or f"stream_{int(time.time())}"
        
        # Connection state
        self._websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._running = False
        self._reconnect_count = 0
        
        # Message handling
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=config.buffer_size)
        self._subscriptions: Dict[str, Dict[str, Any]] = {}
        
        # Event handlers
        self._event_handlers: Dict[StreamEvent, List[Callable]] = {
            event: [] for event in StreamEvent
        }
        
        # Tasks
        self._connection_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._message_handler_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'connection_count': 0,
            'reconnection_count': 0,
            'last_heartbeat': None,
            'uptime_start': None
        }
        
        logger.info(f"Data stream {self.stream_id} initialized")
    
    async def connect(self) -> bool:
        """
        Establish WebSocket connection.
        
        Returns:
            bool: True if connection successful
        """
        if self._connected:
            logger.warning(f"Stream {self.stream_id} already connected")
            return True
        
        try:
            # Create HTTP session if needed
            if not self._session:
                timeout = aiohttp.ClientTimeout(total=30)
                self._session = aiohttp.ClientSession(timeout=timeout)
            
            # Establish WebSocket connection
            logger.info(f"Connecting stream {self.stream_id} to {self.config.url}")
            
            self._websocket = await self._session.ws_connect(
                self.config.url,
                max_msg_size=self.config.max_message_size,
                compress=self.config.enable_compression,
                heartbeat=self.config.heartbeat_interval
            )
            
            self._connected = True
            self._running = True
            self._stats['connection_count'] += 1
            self._stats['uptime_start'] = datetime.now(timezone.utc)
            
            # Start background tasks
            self._connection_task = asyncio.create_task(self._connection_handler())
            self._heartbeat_task = asyncio.create_task(self._heartbeat_handler())
            self._message_handler_task = asyncio.create_task(self._message_handler())
            
            # Trigger connected event
            await self._trigger_event(StreamEvent.CONNECTED, {'stream_id': self.stream_id})
            
            logger.info(f"Stream {self.stream_id} connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect stream {self.stream_id}: {e}")
            await self._trigger_event(StreamEvent.ERROR, {'error': str(e)})
            return False
    
    async def disconnect(self):
        """Disconnect and cleanup resources."""
        if not self._connected:
            return
        
        logger.info(f"Disconnecting stream {self.stream_id}")
        
        self._running = False
        self._connected = False
        
        # Cancel background tasks
        for task in [self._connection_task, self._heartbeat_task, self._message_handler_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close WebSocket
        if self._websocket and not self._websocket.closed:
            await self._websocket.close()
        
        # Close session
        if self._session and not self._session.closed:
            await self._session.close()
        
        self._websocket = None
        self._session = None
        
        # Trigger disconnected event
        await self._trigger_event(StreamEvent.DISCONNECTED, {'stream_id': self.stream_id})
        
        logger.info(f"Stream {self.stream_id} disconnected")
    
    async def subscribe(
        self,
        subscription_type: str,
        symbols: List[str],
        **kwargs
    ) -> bool:
        """
        Subscribe to data streams.
        
        Args:
            subscription_type (str): Type of subscription ('kline', 'ticker', 'depth', 'trade')
            symbols (List[str]): List of symbols to subscribe to
            **kwargs: Additional subscription parameters
            
        Returns:
            bool: True if subscription successful
        """
        if not self._connected:
            logger.error("Cannot subscribe: stream not connected")
            return False
        
        try:
            # Build subscription message (Binance format)
            if subscription_type == 'kline':
                interval = kwargs.get('interval', '1m')
                streams = [f"{symbol.lower()}@kline_{interval}" for symbol in symbols]
            elif subscription_type == 'ticker':
                streams = [f"{symbol.lower()}@ticker" for symbol in symbols]
            elif subscription_type == 'depth':
                update_speed = kwargs.get('update_speed', '1000ms')
                streams = [f"{symbol.lower()}@depth@{update_speed}" for symbol in symbols]
            elif subscription_type == 'trade':
                streams = [f"{symbol.lower()}@trade" for symbol in symbols]
            else:
                raise ValueError(f"Unsupported subscription type: {subscription_type}")
            
            subscription_msg = {
                'method': 'SUBSCRIBE',
                'params': streams,
                'id': int(time.time() * 1000)
            }
            
            # Send subscription message
            await self._send_message(subscription_msg)
            
            # Store subscription info
            subscription_key = f"{subscription_type}_{'-'.join(symbols)}"
            self._subscriptions[subscription_key] = {
                'type': subscription_type,
                'symbols': symbols,
                'streams': streams,
                'timestamp': datetime.now(timezone.utc),
                **kwargs
            }
            
            logger.info(f"Subscribed to {subscription_type} for {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {subscription_type}: {e}")
            return False
    
    async def unsubscribe(
        self,
        subscription_type: str,
        symbols: List[str],
        **kwargs
    ) -> bool:
        """
        Unsubscribe from data streams.
        
        Args:
            subscription_type (str): Type of subscription
            symbols (List[str]): List of symbols to unsubscribe from
            **kwargs: Additional parameters
            
        Returns:
            bool: True if unsubscription successful
        """
        if not self._connected:
            logger.error("Cannot unsubscribe: stream not connected")
            return False
        
        try:
            # Find subscription
            subscription_key = f"{subscription_type}_{'-'.join(symbols)}"
            if subscription_key not in self._subscriptions:
                logger.warning(f"Subscription not found: {subscription_key}")
                return False
            
            subscription = self._subscriptions[subscription_key]
            streams = subscription['streams']
            
            unsubscribe_msg = {
                'method': 'UNSUBSCRIBE',
                'params': streams,
                'id': int(time.time() * 1000)
            }
            
            # Send unsubscribe message
            await self._send_message(unsubscribe_msg)
            
            # Remove subscription
            del self._subscriptions[subscription_key]
            
            logger.info(f"Unsubscribed from {subscription_type} for {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {subscription_type}: {e}")
            return False
    
    async def get_messages(self) -> AsyncIterator[StreamMessage]:
        """
        Get stream messages as async iterator.
        
        Yields:
            StreamMessage: Stream messages with parsed data
        """
        while self._running:
            try:
                # Get message from queue with timeout
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0
                )
                yield message
                
            except asyncio.TimeoutError:
                # No message received, continue
                continue
            except Exception as e:
                logger.error(f"Error getting message: {e}")
                break
    
    def add_event_handler(
        self,
        event: StreamEvent,
        handler: Callable[[Dict[str, Any]], None]
    ):
        """
        Add event handler for stream events.
        
        Args:
            event (StreamEvent): Event type to handle
            handler (Callable): Event handler function
        """
        self._event_handlers[event].append(handler)
    
    def remove_event_handler(
        self,
        event: StreamEvent,
        handler: Callable[[Dict[str, Any]], None]
    ):
        """
        Remove event handler.
        
        Args:
            event (StreamEvent): Event type
            handler (Callable): Handler to remove
        """
        if handler in self._event_handlers[event]:
            self._event_handlers[event].remove(handler)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get stream statistics.
        
        Returns:
            Dict[str, Any]: Stream statistics
        """
        uptime = None
        if self._stats['uptime_start']:
            uptime = (datetime.now(timezone.utc) - self._stats['uptime_start']).total_seconds()
        
        return {
            'stream_id': self.stream_id,
            'connected': self._connected,
            'running': self._running,
            'subscriptions': len(self._subscriptions),
            'queue_size': self._message_queue.qsize(),
            'uptime_seconds': uptime,
            **self._stats
        }
    
    async def _connection_handler(self):
        """Handle WebSocket connection and messages."""
        try:
            while self._running and self._websocket:
                async for msg in self._websocket:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self._process_message(msg.data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"WebSocket error: {self._websocket.exception()}")
                        break
                    elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING):
                        logger.info("WebSocket connection closed")
                        break
        except Exception as e:
            logger.error(f"Connection handler error: {e}")
        
        if self._running:
            # Connection lost, attempt reconnection
            await self._handle_disconnection()
    
    async def _heartbeat_handler(self):
        """Handle periodic heartbeat/ping."""
        try:
            while self._running and self._connected:
                await asyncio.sleep(self.config.ping_interval)
                
                if self._websocket and not self._websocket.closed:
                    try:
                        await self._websocket.ping()
                        self._stats['last_heartbeat'] = datetime.now(timezone.utc)
                        await self._trigger_event(StreamEvent.HEARTBEAT, {
                            'timestamp': self._stats['last_heartbeat']
                        })
                    except Exception as e:
                        logger.warning(f"Heartbeat failed: {e}")
                        break
        except Exception as e:
            logger.error(f"Heartbeat handler error: {e}")
    
    async def _message_handler(self):
        """Process queued messages."""
        try:
            while self._running:
                # This task processes messages from the queue
                # In this implementation, messages are processed directly
                # in _process_message, but this could be used for batching
                # or additional processing
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Message handler error: {e}")
    
    async def _process_message(self, message_data: str):
        """Process incoming WebSocket message."""
        try:
            # Parse JSON message
            raw_message = json.loads(message_data)
            self._stats['messages_received'] += 1
            
            # Create stream message
            stream_message = StreamMessage(
                data=raw_message,
                timestamp=datetime.now(timezone.utc),
                stream_id=self.stream_id,
                message_type=self._determine_message_type(raw_message),
                raw_message=raw_message
            )
            
            # Add to queue (non-blocking)
            try:
                self._message_queue.put_nowait(stream_message)
            except asyncio.QueueFull:
                logger.warning("Message queue full, dropping message")
            
            # Trigger data received event
            await self._trigger_event(StreamEvent.DATA_RECEIVED, {
                'message_type': stream_message.message_type,
                'timestamp': stream_message.timestamp
            })
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _determine_message_type(self, message: Dict[str, Any]) -> str:
        """Determine message type from raw message."""
        # Binance WebSocket message format detection
        if 'stream' in message:
            stream_name = message['stream']
            if '@kline_' in stream_name:
                return 'kline'
            elif '@ticker' in stream_name:
                return 'ticker'
            elif '@depth' in stream_name:
                return 'depth'
            elif '@trade' in stream_name:
                return 'trade'
        
        if 'result' in message or 'id' in message:
            return 'response'
        
        return 'unknown'
    
    async def _send_message(self, message: Dict[str, Any]):
        """Send message to WebSocket."""
        if not self._websocket or self._websocket.closed:
            raise ConnectionError("WebSocket not connected")
        
        message_str = json.dumps(message)
        await self._websocket.send_str(message_str)
        self._stats['messages_sent'] += 1
    
    async def _handle_disconnection(self):
        """Handle disconnection and attempt reconnection."""
        self._connected = False
        await self._trigger_event(StreamEvent.DISCONNECTED, {
            'stream_id': self.stream_id,
            'reconnect_count': self._reconnect_count
        })
        
        if self._reconnect_count < self.config.reconnect_attempts:
            await self._attempt_reconnection()
        else:
            logger.error(f"Max reconnection attempts reached for stream {self.stream_id}")
            self._running = False
    
    async def _attempt_reconnection(self):
        """Attempt to reconnect with exponential backoff."""
        self._reconnect_count += 1
        self._stats['reconnection_count'] += 1
        
        delay = min(
            self.config.reconnect_delay * (self.config.reconnect_backoff ** (self._reconnect_count - 1)),
            self.config.max_reconnect_delay
        )
        
        logger.info(f"Attempting reconnection {self._reconnect_count}/{self.config.reconnect_attempts} "
                   f"for stream {self.stream_id} in {delay:.1f}s")
        
        await self._trigger_event(StreamEvent.RECONNECTING, {
            'attempt': self._reconnect_count,
            'delay': delay
        })
        
        await asyncio.sleep(delay)
        
        # Attempt reconnection
        if await self.connect():
            # Restore subscriptions
            await self._restore_subscriptions()
            self._reconnect_count = 0  # Reset on successful connection
    
    async def _restore_subscriptions(self):
        """Restore subscriptions after reconnection."""
        logger.info(f"Restoring {len(self._subscriptions)} subscriptions")
        
        for subscription_key, subscription in self._subscriptions.copy().items():
            try:
                await self.subscribe(
                    subscription['type'],
                    subscription['symbols'],
                    **{k: v for k, v in subscription.items() 
                       if k not in ['type', 'symbols', 'streams', 'timestamp']}
                )
            except Exception as e:
                logger.error(f"Failed to restore subscription {subscription_key}: {e}")
    
    async def _trigger_event(self, event: StreamEvent, data: Dict[str, Any]):
        """Trigger event handlers."""
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event}: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()