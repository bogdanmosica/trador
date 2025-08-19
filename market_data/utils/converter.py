"""
Data Converter

Converts between different data formats and structures.
Provides utility functions for transforming market data between
various representations used by strategies and analysis tools.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json

from ..models import Candle, Ticker, OrderBook, Trade


class DataConverter:
    """
    Converts market data between different formats and structures.
    
    Provides utility functions for transforming data between native models,
    pandas DataFrames, dictionaries, and other common formats.
    """
    
    @staticmethod
    def candles_to_dataframe(
        candles: List[Candle],
        include_raw_data: bool = False
    ) -> pd.DataFrame:
        """
        Convert list of candles to pandas DataFrame.
        
        Args:
            candles (List[Candle]): List of candles to convert
            include_raw_data (bool): Whether to include raw_data column
            
        Returns:
            pd.DataFrame: DataFrame with candle data
        """
        if not candles:
            return pd.DataFrame()
        
        data = []
        for candle in candles:
            row = {
                'timestamp': candle.timestamp,
                'datetime': candle.datetime,
                'symbol': candle.symbol,
                'interval': candle.interval,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume,
                'quote_volume': candle.quote_volume,
                'trade_count': candle.trade_count,
                'taker_buy_volume': candle.taker_buy_volume,
                'taker_buy_quote_volume': candle.taker_buy_quote_volume,
                'price_change': candle.price_change,
                'price_change_percent': candle.price_change_percent,
                'typical_price': candle.typical_price,
                'weighted_price': candle.weighted_price
            }
            
            if include_raw_data:
                row['raw_data'] = candle.raw_data
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Set datetime as index for time series analysis
        if not df.empty:
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
        
        return df
    
    @staticmethod
    def dataframe_to_candles(
        df: pd.DataFrame,
        symbol: Optional[str] = None,
        interval: Optional[str] = None
    ) -> List[Candle]:
        """
        Convert pandas DataFrame to list of candles.
        
        Args:
            df (pd.DataFrame): DataFrame with candle data
            symbol (Optional[str]): Symbol if not in DataFrame
            interval (Optional[str]): Interval if not in DataFrame
            
        Returns:
            List[Candle]: List of candles
        """
        if df.empty:
            return []
        
        candles = []
        
        for index, row in df.iterrows():
            # Handle datetime index
            if isinstance(index, pd.Timestamp):
                timestamp = int(index.timestamp() * 1000)
            else:
                timestamp = int(row.get('timestamp', 0))
            
            candle = Candle(
                timestamp=timestamp,
                symbol=row.get('symbol', symbol or ''),
                interval=row.get('interval', interval or ''),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=float(row['volume']),
                quote_volume=row.get('quote_volume'),
                trade_count=row.get('trade_count'),
                taker_buy_volume=row.get('taker_buy_volume'),
                taker_buy_quote_volume=row.get('taker_buy_quote_volume'),
                raw_data=row.get('raw_data', {})
            )
            candles.append(candle)
        
        return candles
    
    @staticmethod
    def tickers_to_dataframe(tickers: List[Ticker]) -> pd.DataFrame:
        """
        Convert list of tickers to pandas DataFrame.
        
        Args:
            tickers (List[Ticker]): List of tickers to convert
            
        Returns:
            pd.DataFrame: DataFrame with ticker data
        """
        if not tickers:
            return pd.DataFrame()
        
        data = []
        for ticker in tickers:
            row = ticker.to_dict()
            row['datetime'] = ticker.datetime
            data.append(row)
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
        
        return df
    
    @staticmethod
    def trades_to_dataframe(trades: List[Trade]) -> pd.DataFrame:
        """
        Convert list of trades to pandas DataFrame.
        
        Args:
            trades (List[Trade]): List of trades to convert
            
        Returns:
            pd.DataFrame: DataFrame with trade data
        """
        if not trades:
            return pd.DataFrame()
        
        data = []
        for trade in trades:
            row = trade.to_dict()
            row['datetime'] = trade.datetime
            data.append(row)
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
        
        return df
    
    @staticmethod
    def candles_to_ohlcv(candles: List[Candle]) -> Dict[str, List[float]]:
        """
        Convert candles to OHLCV format for analysis libraries.
        
        Args:
            candles (List[Candle]): List of candles
            
        Returns:
            Dict[str, List[float]]: OHLCV data structure
        """
        if not candles:
            return {
                'open': [],
                'high': [],
                'low': [], 
                'close': [],
                'volume': []
            }
        
        return {
            'open': [c.open for c in candles],
            'high': [c.high for c in candles],
            'low': [c.low for c in candles],
            'close': [c.close for c in candles],
            'volume': [c.volume for c in candles]
        }
    
    @staticmethod
    def candles_to_strategy_format(candles: List[Candle]) -> List[Dict[str, Any]]:
        """
        Convert candles to format compatible with strategy module.
        
        Args:
            candles (List[Candle]): List of candles
            
        Returns:
            List[Dict[str, Any]]: Strategy-compatible format
        """
        # Import here to avoid circular dependency
        try:
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent.parent))
            from strategy.base_strategy import MarketData
            
            market_data = []
            for candle in candles:
                data = MarketData(
                    timestamp=candle.datetime,
                    open=candle.open,
                    high=candle.high,
                    low=candle.low,
                    close=candle.close,
                    volume=candle.volume,
                    symbol=candle.symbol,
                    timeframe=candle.interval
                )
                market_data.append(data)
            
            return market_data
            
        except ImportError:
            # Fallback to dictionary format
            return [candle.to_dict() for candle in candles]
    
    @staticmethod
    def order_book_to_arrays(order_book: OrderBook) -> Dict[str, Any]:
        """
        Convert order book to arrays for analysis.
        
        Args:
            order_book (OrderBook): Order book to convert
            
        Returns:
            Dict[str, Any]: Order book in array format
        """
        return {
            'timestamp': order_book.timestamp,
            'symbol': order_book.symbol,
            'bids': {
                'prices': [level.price for level in order_book.bids],
                'quantities': [level.quantity for level in order_book.bids],
                'notional': [level.notional_value for level in order_book.bids]
            },
            'asks': {
                'prices': [level.price for level in order_book.asks],
                'quantities': [level.quantity for level in order_book.asks],
                'notional': [level.notional_value for level in order_book.asks]
            },
            'spread': order_book.spread,
            'mid_price': order_book.mid_price
        }
    
    @staticmethod
    def candles_to_csv(
        candles: List[Candle],
        filename: str,
        include_calculated_fields: bool = True
    ):
        """
        Save candles to CSV file.
        
        Args:
            candles (List[Candle]): List of candles to save
            filename (str): Output filename
            include_calculated_fields (bool): Include calculated fields
        """
        df = DataConverter.candles_to_dataframe(candles)
        
        if not include_calculated_fields:
            # Remove calculated fields
            calculated_fields = [
                'price_change', 'price_change_percent',
                'typical_price', 'weighted_price'
            ]
            df = df.drop(columns=[col for col in calculated_fields if col in df.columns])
        
        df.to_csv(filename)
    
    @staticmethod
    def candles_from_csv(
        filename: str,
        symbol: str,
        interval: str
    ) -> List[Candle]:
        """
        Load candles from CSV file.
        
        Args:
            filename (str): CSV filename
            symbol (str): Symbol for candles
            interval (str): Interval for candles
            
        Returns:
            List[Candle]: List of loaded candles
        """
        df = pd.read_csv(filename, index_col=0, parse_dates=True)
        return DataConverter.dataframe_to_candles(df, symbol, interval)
    
    @staticmethod
    def candles_to_json(
        candles: List[Candle],
        filename: Optional[str] = None,
        pretty: bool = True
    ) -> str:
        """
        Convert candles to JSON format.
        
        Args:
            candles (List[Candle]): List of candles
            filename (Optional[str]): Output filename (if None, returns JSON string)
            pretty (bool): Pretty-print JSON
            
        Returns:
            str: JSON string if filename is None
        """
        data = [candle.to_dict() for candle in candles]
        
        json_str = json.dumps(
            data,
            indent=2 if pretty else None,
            default=str  # Handle datetime serialization
        )
        
        if filename:
            with open(filename, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    @staticmethod
    def candles_from_json(
        json_data: str,
        symbol: Optional[str] = None,
        interval: Optional[str] = None
    ) -> List[Candle]:
        """
        Load candles from JSON data.
        
        Args:
            json_data (str): JSON string or filename
            symbol (Optional[str]): Symbol override
            interval (Optional[str]): Interval override
            
        Returns:
            List[Candle]: List of loaded candles
        """
        # Check if it's a filename
        try:
            with open(json_data, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Assume it's JSON string
            data = json.loads(json_data)
        
        candles = []
        for item in data:
            candle = Candle.from_dict(item)
            if symbol:
                candle.symbol = symbol
            if interval:
                candle.interval = interval
            candles.append(candle)
        
        return candles
    
    @staticmethod
    def resample_candles(
        candles: List[Candle],
        target_interval: str,
        method: str = 'last'
    ) -> List[Candle]:
        """
        Resample candles to different timeframe.
        
        Args:
            candles (List[Candle]): Source candles
            target_interval (str): Target interval (e.g., '1h', '4h', '1d')
            method (str): Resampling method ('last', 'first', 'mean')
            
        Returns:
            List[Candle]: Resampled candles
        """
        if not candles:
            return []
        
        # Convert to DataFrame for resampling
        df = DataConverter.candles_to_dataframe(candles)
        
        # Convert interval to pandas frequency
        freq_map = {
            '1m': '1Min', '5m': '5Min', '15m': '15Min', '30m': '30Min',
            '1h': '1H', '2h': '2H', '4h': '4H', '6h': '6H', '12h': '12H',
            '1d': '1D', '1w': '1W', '1M': '1M'
        }
        
        pandas_freq = freq_map.get(target_interval)
        if not pandas_freq:
            raise ValueError(f"Unsupported target interval: {target_interval}")
        
        # Resample OHLCV data
        resampled = df.resample(pandas_freq).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'quote_volume': 'sum',
            'trade_count': 'sum',
            'taker_buy_volume': 'sum',
            'taker_buy_quote_volume': 'sum'
        }).dropna()
        
        # Add metadata columns
        resampled['symbol'] = candles[0].symbol
        resampled['interval'] = target_interval
        resampled['timestamp'] = (resampled.index.astype('int64') // 10**6).astype('int64')
        
        # Convert back to candles
        return DataConverter.dataframe_to_candles(resampled)
    
    @staticmethod
    def merge_candles(
        *candle_lists: List[Candle],
        sort_by_timestamp: bool = True
    ) -> List[Candle]:
        """
        Merge multiple candle lists.
        
        Args:
            *candle_lists: Variable number of candle lists
            sort_by_timestamp (bool): Sort result by timestamp
            
        Returns:
            List[Candle]: Merged candles
        """
        merged = []
        for candle_list in candle_lists:
            merged.extend(candle_list)
        
        if sort_by_timestamp:
            merged.sort(key=lambda c: c.timestamp)
        
        return merged