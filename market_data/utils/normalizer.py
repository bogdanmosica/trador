"""
Data Normalizer

Normalizes market data from different providers into standardized formats.
Handles data conversion, missing field handling, and format standardization.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from ..models import Candle, Ticker, OrderBook, OrderBookLevel, Trade


logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    Normalizes market data from different providers into standard formats.
    
    Converts provider-specific data structures into unified models
    while handling missing fields and data quality issues.
    """
    
    @staticmethod
    def normalize_binance_kline(
        kline_data: List[Any],
        symbol: str,
        interval: str
    ) -> Candle:
        """
        Normalize Binance kline/candlestick data.
        
        Args:
            kline_data (List[Any]): Raw Binance kline data array
            symbol (str): Trading symbol
            interval (str): Candle interval
            
        Returns:
            Candle: Normalized candle data
        """
        try:
            # Binance kline format:
            # [
            #   0: Open time, 1: Open, 2: High, 3: Low, 4: Close, 5: Volume,
            #   6: Close time, 7: Quote asset volume, 8: Number of trades,
            #   9: Taker buy base asset volume, 10: Taker buy quote asset volume, 11: Ignore
            # ]
            
            candle = Candle(
                timestamp=int(kline_data[0]),
                symbol=symbol.upper(),
                interval=interval,
                open=float(kline_data[1]),
                high=float(kline_data[2]),
                low=float(kline_data[3]),
                close=float(kline_data[4]),
                volume=float(kline_data[5]),
                quote_volume=float(kline_data[7]) if len(kline_data) > 7 else None,
                trade_count=int(kline_data[8]) if len(kline_data) > 8 else None,
                taker_buy_volume=float(kline_data[9]) if len(kline_data) > 9 else None,
                taker_buy_quote_volume=float(kline_data[10]) if len(kline_data) > 10 else None,
                raw_data={'binance_kline': kline_data}
            )
            
            return candle
            
        except (IndexError, ValueError, TypeError) as e:
            logger.error(f"Failed to normalize Binance kline data: {e}")
            raise ValueError(f"Invalid Binance kline data format: {e}")
    
    @staticmethod
    def normalize_binance_ticker(
        ticker_data: Dict[str, Any],
        symbol: Optional[str] = None
    ) -> Ticker:
        """
        Normalize Binance 24hr ticker data.
        
        Args:
            ticker_data (Dict[str, Any]): Raw Binance ticker data
            symbol (Optional[str]): Symbol override
            
        Returns:
            Ticker: Normalized ticker data
        """
        try:
            symbol = symbol or ticker_data.get('symbol', '').upper()
            
            ticker = Ticker(
                timestamp=int(ticker_data.get('closeTime', 0)),
                symbol=symbol,
                price=float(ticker_data.get('lastPrice', 0)),
                bid=float(ticker_data.get('bidPrice', 0)) if 'bidPrice' in ticker_data else None,
                ask=float(ticker_data.get('askPrice', 0)) if 'askPrice' in ticker_data else None,
                bid_size=float(ticker_data.get('bidQty', 0)) if 'bidQty' in ticker_data else None,
                ask_size=float(ticker_data.get('askQty', 0)) if 'askQty' in ticker_data else None,
                volume_24h=float(ticker_data.get('volume', 0)),
                price_change_24h=float(ticker_data.get('priceChange', 0)),
                price_change_percent_24h=float(ticker_data.get('priceChangePercent', 0)),
                high_24h=float(ticker_data.get('highPrice', 0)),
                low_24h=float(ticker_data.get('lowPrice', 0)),
                open_24h=float(ticker_data.get('openPrice', 0)),
                quote_volume_24h=float(ticker_data.get('quoteVolume', 0)),
                raw_data={'binance_ticker': ticker_data}
            )
            
            return ticker
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to normalize Binance ticker data: {e}")
            raise ValueError(f"Invalid Binance ticker data format: {e}")
    
    @staticmethod
    def normalize_binance_depth(
        depth_data: Dict[str, Any],
        symbol: str
    ) -> OrderBook:
        """
        Normalize Binance order book depth data.
        
        Args:
            depth_data (Dict[str, Any]): Raw Binance depth data
            symbol (str): Trading symbol
            
        Returns:
            OrderBook: Normalized order book
        """
        try:
            # Convert bid and ask arrays to OrderBookLevel objects
            bids = [
                OrderBookLevel(float(level[0]), float(level[1]))
                for level in depth_data.get('bids', [])
            ]
            
            asks = [
                OrderBookLevel(float(level[0]), float(level[1]))
                for level in depth_data.get('asks', [])
            ]
            
            order_book = OrderBook(
                timestamp=int(datetime.now(timezone.utc).timestamp() * 1000),
                symbol=symbol.upper(),
                bids=bids,
                asks=asks,
                last_update_id=depth_data.get('lastUpdateId'),
                raw_data={'binance_depth': depth_data}
            )
            
            return order_book
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to normalize Binance depth data: {e}")
            raise ValueError(f"Invalid Binance depth data format: {e}")
    
    @staticmethod
    def normalize_binance_trade(
        trade_data: Dict[str, Any],
        symbol: str
    ) -> Trade:
        """
        Normalize Binance trade data.
        
        Args:
            trade_data (Dict[str, Any]): Raw Binance trade data
            symbol (str): Trading symbol
            
        Returns:
            Trade: Normalized trade data
        """
        try:
            trade = Trade(
                timestamp=int(trade_data.get('time', 0)),
                symbol=symbol.upper(),
                trade_id=str(trade_data.get('id', '')),
                price=float(trade_data.get('price', 0)),
                quantity=float(trade_data.get('qty', 0)),
                side='buy' if not trade_data.get('isBuyerMaker', False) else 'sell',
                is_buyer_maker=trade_data.get('isBuyerMaker', False),
                raw_data={'binance_trade': trade_data}
            )
            
            return trade
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to normalize Binance trade data: {e}")
            raise ValueError(f"Invalid Binance trade data format: {e}")
    
    @staticmethod
    def normalize_websocket_kline(
        ws_data: Dict[str, Any]
    ) -> Candle:
        """
        Normalize WebSocket kline/candlestick data.
        
        Args:
            ws_data (Dict[str, Any]): WebSocket kline message
            
        Returns:
            Candle: Normalized candle data
        """
        try:
            # Extract kline data from WebSocket message
            kline = ws_data.get('k', {})
            
            candle = Candle(
                timestamp=int(kline.get('t', 0)),  # Open time
                symbol=kline.get('s', '').upper(),
                interval=kline.get('i', ''),
                open=float(kline.get('o', 0)),
                high=float(kline.get('h', 0)),
                low=float(kline.get('l', 0)),
                close=float(kline.get('c', 0)),
                volume=float(kline.get('v', 0)),
                quote_volume=float(kline.get('q', 0)),
                trade_count=int(kline.get('n', 0)),
                taker_buy_volume=float(kline.get('V', 0)),
                taker_buy_quote_volume=float(kline.get('Q', 0)),
                raw_data={'websocket_kline': ws_data}
            )
            
            return candle
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to normalize WebSocket kline data: {e}")
            raise ValueError(f"Invalid WebSocket kline data format: {e}")
    
    @staticmethod
    def normalize_websocket_ticker(
        ws_data: Dict[str, Any]
    ) -> Ticker:
        """
        Normalize WebSocket ticker data.
        
        Args:
            ws_data (Dict[str, Any]): WebSocket ticker message
            
        Returns:
            Ticker: Normalized ticker data
        """
        try:
            ticker = Ticker(
                timestamp=int(ws_data.get('E', 0)),  # Event time
                symbol=ws_data.get('s', '').upper(),
                price=float(ws_data.get('c', 0)),  # Current close price
                bid=float(ws_data.get('b', 0)) if 'b' in ws_data else None,
                ask=float(ws_data.get('a', 0)) if 'a' in ws_data else None,
                bid_size=float(ws_data.get('B', 0)) if 'B' in ws_data else None,
                ask_size=float(ws_data.get('A', 0)) if 'A' in ws_data else None,
                volume_24h=float(ws_data.get('v', 0)),
                price_change_24h=float(ws_data.get('P', 0)),
                price_change_percent_24h=float(ws_data.get('p', 0)),
                high_24h=float(ws_data.get('h', 0)),
                low_24h=float(ws_data.get('l', 0)),
                open_24h=float(ws_data.get('o', 0)),
                quote_volume_24h=float(ws_data.get('q', 0)),
                raw_data={'websocket_ticker': ws_data}
            )
            
            return ticker
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to normalize WebSocket ticker data: {e}")
            raise ValueError(f"Invalid WebSocket ticker data format: {e}")
    
    @staticmethod
    def normalize_websocket_depth(
        ws_data: Dict[str, Any]
    ) -> OrderBook:
        """
        Normalize WebSocket depth/order book data.
        
        Args:
            ws_data (Dict[str, Any]): WebSocket depth message
            
        Returns:
            OrderBook: Normalized order book data
        """
        try:
            # Convert bid and ask arrays
            bids = [
                OrderBookLevel(float(level[0]), float(level[1]))
                for level in ws_data.get('b', [])
            ]
            
            asks = [
                OrderBookLevel(float(level[0]), float(level[1]))
                for level in ws_data.get('a', [])
            ]
            
            order_book = OrderBook(
                timestamp=int(ws_data.get('E', 0)),  # Event time
                symbol=ws_data.get('s', '').upper(),
                bids=bids,
                asks=asks,
                last_update_id=ws_data.get('u'),
                raw_data={'websocket_depth': ws_data}
            )
            
            return order_book
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to normalize WebSocket depth data: {e}")
            raise ValueError(f"Invalid WebSocket depth data format: {e}")
    
    @staticmethod
    def normalize_websocket_trade(
        ws_data: Dict[str, Any]
    ) -> Trade:
        """
        Normalize WebSocket trade data.
        
        Args:
            ws_data (Dict[str, Any]): WebSocket trade message
            
        Returns:
            Trade: Normalized trade data
        """
        try:
            trade = Trade(
                timestamp=int(ws_data.get('T', 0)),  # Trade time
                symbol=ws_data.get('s', '').upper(),
                trade_id=str(ws_data.get('t', '')),
                price=float(ws_data.get('p', 0)),
                quantity=float(ws_data.get('q', 0)),
                side='buy' if not ws_data.get('m', False) else 'sell',  # m: buyer is maker
                is_buyer_maker=ws_data.get('m', False),
                raw_data={'websocket_trade': ws_data}
            )
            
            return trade
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to normalize WebSocket trade data: {e}")
            raise ValueError(f"Invalid WebSocket trade data format: {e}")
    
    @staticmethod
    def fill_missing_candle_data(candle: Candle) -> Candle:
        """
        Fill missing optional fields in candle data with reasonable defaults.
        
        Args:
            candle (Candle): Candle with potentially missing data
            
        Returns:
            Candle: Candle with filled data
        """
        # Estimate quote volume if missing
        if candle.quote_volume is None:
            avg_price = (candle.open + candle.high + candle.low + candle.close) / 4
            candle.quote_volume = candle.volume * avg_price
        
        # Estimate trade count if missing (rough approximation)
        if candle.trade_count is None:
            # Assume average trade size based on volume
            avg_trade_size = candle.volume / 100 if candle.volume > 0 else 1
            candle.trade_count = max(1, int(candle.volume / avg_trade_size))
        
        # Estimate taker buy volumes if missing (assume 50% taker buy)
        if candle.taker_buy_volume is None:
            candle.taker_buy_volume = candle.volume * 0.5
        
        if candle.taker_buy_quote_volume is None and candle.quote_volume:
            candle.taker_buy_quote_volume = candle.quote_volume * 0.5
        
        return candle
    
    @staticmethod
    def normalize_symbol_format(symbol: str, provider: str = "binance") -> str:
        """
        Normalize symbol format for specific providers.
        
        Args:
            symbol (str): Symbol to normalize
            provider (str): Target provider format
            
        Returns:
            str: Normalized symbol
        """
        # Remove any separators and convert to uppercase
        clean_symbol = symbol.replace('-', '').replace('_', '').replace('/', '').upper()
        
        if provider.lower() == "binance":
            # Binance uses no separators (e.g., BTCUSDT)
            return clean_symbol
        elif provider.lower() == "coinbase":
            # Coinbase uses hyphen (e.g., BTC-USD)
            if len(clean_symbol) >= 6:
                return f"{clean_symbol[:-3]}-{clean_symbol[-3:]}"
        elif provider.lower() == "kraken":
            # Kraken may use different naming conventions
            return clean_symbol
        
        return clean_symbol
    
    @staticmethod
    def normalize_interval_format(interval: str, provider: str = "binance") -> str:
        """
        Normalize interval format for specific providers.
        
        Args:
            interval (str): Interval to normalize
            provider (str): Target provider format
            
        Returns:
            str: Normalized interval
        """
        interval = interval.lower().strip()
        
        # Common mappings
        interval_mappings = {
            "1min": "1m",
            "5min": "5m", 
            "15min": "15m",
            "30min": "30m",
            "1hour": "1h",
            "4hour": "4h",
            "1day": "1d",
            "1week": "1w",
            "1month": "1M"
        }
        
        normalized = interval_mappings.get(interval, interval)
        
        if provider.lower() == "binance":
            # Binance format is already our standard
            return normalized
        elif provider.lower() == "coinbase":
            # Coinbase uses seconds
            conversions = {
                "1m": "60", "5m": "300", "15m": "900", "30m": "1800",
                "1h": "3600", "4h": "14400", "1d": "86400"
            }
            return conversions.get(normalized, normalized)
        
        return normalized