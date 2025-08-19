"""
Data Storage

Persistent storage system for market data with support for multiple formats
including Parquet, CSV, and JSON. Provides efficient data archival and retrieval.
"""

import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import logging

from ..models import Candle, Ticker, OrderBook, Trade


logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    """Configuration for data storage."""
    base_path: str = "./data"
    format: str = "parquet"  # parquet, csv, json
    compression: Optional[str] = "snappy"  # For parquet: snappy, gzip, lz4
    partition_by: str = "date"  # date, symbol, interval
    max_file_size_mb: int = 100
    enable_indexing: bool = True
    backup_enabled: bool = False
    backup_path: Optional[str] = None


class DataStorage:
    """
    Persistent storage manager for market data.
    
    Supports multiple storage formats and partitioning strategies
    for efficient data organization and retrieval.
    """
    
    def __init__(self, config: StorageConfig):
        """
        Initialize data storage.
        
        Args:
            config (StorageConfig): Storage configuration
        """
        self.config = config
        self.base_path = Path(config.base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different data types
        self.candles_path = self.base_path / "candles"
        self.tickers_path = self.base_path / "tickers"
        self.orderbooks_path = self.base_path / "orderbooks"
        self.trades_path = self.base_path / "trades"
        
        for path in [self.candles_path, self.tickers_path, self.orderbooks_path, self.trades_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Data storage initialized at {self.base_path}")
    
    def store_candles(
        self,
        candles: List[Candle],
        symbol: Optional[str] = None,
        interval: Optional[str] = None
    ) -> str:
        """
        Store candlestick data.
        
        Args:
            candles (List[Candle]): List of candles to store
            symbol (Optional[str]): Symbol for filename (extracted from candles if None)
            interval (Optional[str]): Interval for filename (extracted from candles if None)
            
        Returns:
            str: Path to stored file
        """
        if not candles:
            raise ValueError("No candles provided")
        
        # Extract metadata if not provided
        if symbol is None:
            symbol = candles[0].symbol
        if interval is None:
            interval = candles[0].interval
        
        # Convert to DataFrame
        df = self._candles_to_dataframe(candles)
        
        # Generate filename
        start_time = datetime.fromtimestamp(candles[0].timestamp / 1000)
        end_time = datetime.fromtimestamp(candles[-1].timestamp / 1000)
        
        filename = self._generate_filename(
            "candles",
            symbol,
            interval,
            start_time,
            end_time
        )
        
        file_path = self.candles_path / filename
        
        # Store data
        self._save_dataframe(df, file_path)
        
        logger.info(f"Stored {len(candles)} candles to {file_path}")
        return str(file_path)
    
    def load_candles(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Candle]:
        """
        Load candlestick data.
        
        Args:
            symbol (str): Trading symbol
            interval (str): Candle interval
            start_time (Optional[datetime]): Start time filter
            end_time (Optional[datetime]): End time filter
            
        Returns:
            List[Candle]: Loaded candles
        """
        # Find matching files
        pattern = f"candles_{symbol}_{interval}_*.{self.config.format}"
        matching_files = list(self.candles_path.glob(pattern))
        
        if not matching_files:
            return []
        
        # Load and concatenate data
        all_candles = []
        for file_path in matching_files:
            try:
                df = self._load_dataframe(file_path)
                candles = self._dataframe_to_candles(df)
                all_candles.extend(candles)
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
        
        # Filter by time range if specified
        if start_time or end_time:
            filtered_candles = []
            for candle in all_candles:
                candle_time = datetime.fromtimestamp(candle.timestamp / 1000)
                
                if start_time and candle_time < start_time:
                    continue
                if end_time and candle_time > end_time:
                    continue
                
                filtered_candles.append(candle)
            
            all_candles = filtered_candles
        
        # Sort by timestamp
        all_candles.sort(key=lambda c: c.timestamp)
        
        logger.info(f"Loaded {len(all_candles)} candles for {symbol} {interval}")
        return all_candles
    
    def store_tickers(self, tickers: List[Ticker]) -> str:
        """
        Store ticker data.
        
        Args:
            tickers (List[Ticker]): List of tickers to store
            
        Returns:
            str: Path to stored file
        """
        if not tickers:
            raise ValueError("No tickers provided")
        
        # Convert to DataFrame
        df = self._tickers_to_dataframe(tickers)
        
        # Generate filename
        start_time = datetime.fromtimestamp(tickers[0].timestamp / 1000)
        end_time = datetime.fromtimestamp(tickers[-1].timestamp / 1000)
        
        filename = self._generate_filename(
            "tickers",
            "multi" if len(set(t.symbol for t in tickers)) > 1 else tickers[0].symbol,
            "24hr",
            start_time,
            end_time
        )
        
        file_path = self.tickers_path / filename
        
        # Store data
        self._save_dataframe(df, file_path)
        
        logger.info(f"Stored {len(tickers)} tickers to {file_path}")
        return str(file_path)
    
    def store_trades(self, trades: List[Trade], symbol: Optional[str] = None) -> str:
        """
        Store trade data.
        
        Args:
            trades (List[Trade]): List of trades to store
            symbol (Optional[str]): Symbol for filename
            
        Returns:
            str: Path to stored file
        """
        if not trades:
            raise ValueError("No trades provided")
        
        if symbol is None:
            symbol = trades[0].symbol
        
        # Convert to DataFrame
        df = self._trades_to_dataframe(trades)
        
        # Generate filename
        start_time = datetime.fromtimestamp(trades[0].timestamp / 1000)
        end_time = datetime.fromtimestamp(trades[-1].timestamp / 1000)
        
        filename = self._generate_filename(
            "trades",
            symbol,
            "tick",
            start_time,
            end_time
        )
        
        file_path = self.trades_path / filename
        
        # Store data
        self._save_dataframe(df, file_path)
        
        logger.info(f"Stored {len(trades)} trades to {file_path}")
        return str(file_path)
    
    def get_stored_symbols(self, data_type: str = "candles") -> List[str]:
        """
        Get list of symbols with stored data.
        
        Args:
            data_type (str): Type of data ('candles', 'tickers', 'trades')
            
        Returns:
            List[str]: List of symbols
        """
        if data_type == "candles":
            path = self.candles_path
            pattern = f"candles_*_*.{self.config.format}"
        elif data_type == "tickers":
            path = self.tickers_path
            pattern = f"tickers_*_*.{self.config.format}"
        elif data_type == "trades":
            path = self.trades_path
            pattern = f"trades_*_*.{self.config.format}"
        else:
            raise ValueError(f"Unknown data type: {data_type}")
        
        symbols = set()
        for file_path in path.glob(pattern):
            try:
                # Extract symbol from filename
                parts = file_path.stem.split('_')
                if len(parts) >= 3:
                    symbol = parts[1]
                    symbols.add(symbol)
            except:
                continue
        
        return sorted(list(symbols))
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get storage statistics and information.
        
        Returns:
            Dict[str, Any]: Storage information
        """
        info = {
            'base_path': str(self.base_path),
            'format': self.config.format,
            'total_files': 0,
            'total_size_mb': 0.0,
            'data_types': {}
        }
        
        for data_type, path in [
            ('candles', self.candles_path),
            ('tickers', self.tickers_path),
            ('orderbooks', self.orderbooks_path),
            ('trades', self.trades_path)
        ]:
            files = list(path.glob(f"*.{self.config.format}"))
            total_size = sum(f.stat().st_size for f in files)
            
            info['data_types'][data_type] = {
                'file_count': len(files),
                'size_mb': total_size / (1024 * 1024),
                'symbols': len(set(self._extract_symbol_from_filename(f.name) for f in files))
            }
            
            info['total_files'] += len(files)
            info['total_size_mb'] += total_size / (1024 * 1024)
        
        return info
    
    def cleanup_old_files(self, days_old: int = 30) -> int:
        """
        Remove files older than specified days.
        
        Args:
            days_old (int): Number of days to keep
            
        Returns:
            int: Number of files removed
        """
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
        removed_count = 0
        
        for path in [self.candles_path, self.tickers_path, self.orderbooks_path, self.trades_path]:
            for file_path in path.glob(f"*.{self.config.format}"):
                if file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        removed_count += 1
                        logger.info(f"Removed old file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {file_path}: {e}")
        
        return removed_count
    
    def _generate_filename(
        self,
        data_type: str,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime
    ) -> str:
        """Generate filename for data storage."""
        start_str = start_time.strftime("%Y%m%d_%H%M%S")
        end_str = end_time.strftime("%Y%m%d_%H%M%S")
        
        filename = f"{data_type}_{symbol}_{interval}_{start_str}_{end_str}.{self.config.format}"
        return filename
    
    def _extract_symbol_from_filename(self, filename: str) -> str:
        """Extract symbol from filename."""
        try:
            parts = filename.split('_')
            return parts[1] if len(parts) > 1 else "unknown"
        except:
            return "unknown"
    
    def _candles_to_dataframe(self, candles: List[Candle]) -> pd.DataFrame:
        """Convert candles to DataFrame."""
        data = []
        for candle in candles:
            row = asdict(candle)
            # Remove raw_data for storage efficiency
            row.pop('raw_data', None)
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Convert timestamp to datetime for better indexing
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df
    
    def _dataframe_to_candles(self, df: pd.DataFrame) -> List[Candle]:
        """Convert DataFrame to candles."""
        candles = []
        for _, row in df.iterrows():
            candle = Candle(
                timestamp=int(row['timestamp']),
                symbol=row['symbol'],
                interval=row['interval'],
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=float(row['volume']),
                quote_volume=row.get('quote_volume'),
                trade_count=row.get('trade_count'),
                taker_buy_volume=row.get('taker_buy_volume'),
                taker_buy_quote_volume=row.get('taker_buy_quote_volume')
            )
            candles.append(candle)
        
        return candles
    
    def _tickers_to_dataframe(self, tickers: List[Ticker]) -> pd.DataFrame:
        """Convert tickers to DataFrame."""
        data = []
        for ticker in tickers:
            row = asdict(ticker)
            row.pop('raw_data', None)
            data.append(row)
        
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df
    
    def _trades_to_dataframe(self, trades: List[Trade]) -> pd.DataFrame:
        """Convert trades to DataFrame."""
        data = []
        for trade in trades:
            row = asdict(trade)
            row.pop('raw_data', None)
            data.append(row)
        
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df
    
    def _save_dataframe(self, df: pd.DataFrame, file_path: Path):
        """Save DataFrame to file."""
        if self.config.format == "parquet":
            df.to_parquet(
                file_path,
                compression=self.config.compression,
                index=False
            )
        elif self.config.format == "csv":
            df.to_csv(file_path, index=False)
        elif self.config.format == "json":
            df.to_json(file_path, orient='records', date_format='iso')
        else:
            raise ValueError(f"Unsupported format: {self.config.format}")
    
    def _load_dataframe(self, file_path: Path) -> pd.DataFrame:
        """Load DataFrame from file."""
        if self.config.format == "parquet":
            return pd.read_parquet(file_path)
        elif self.config.format == "csv":
            return pd.read_csv(file_path)
        elif self.config.format == "json":
            return pd.read_json(file_path, orient='records')
        else:
            raise ValueError(f"Unsupported format: {self.config.format}")