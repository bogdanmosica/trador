"""
Data Validator

Validates market data for quality, consistency, and completeness.
Detects anomalies, missing data, and potential data quality issues.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import logging
import statistics

from ..models import Candle, Ticker, OrderBook, Trade, validate_candle, validate_ticker


logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates market data quality and consistency.
    
    Provides comprehensive validation for different types of market data
    including outlier detection, consistency checks, and data quality metrics.
    """
    
    def __init__(
        self,
        outlier_threshold: float = 3.0,
        price_gap_threshold: float = 0.1,
        volume_spike_threshold: float = 5.0
    ):
        """
        Initialize data validator.
        
        Args:
            outlier_threshold (float): Standard deviation threshold for outliers
            price_gap_threshold (float): Maximum allowed price gap (as percentage)
            volume_spike_threshold (float): Volume spike detection threshold
        """
        self.outlier_threshold = outlier_threshold
        self.price_gap_threshold = price_gap_threshold
        self.volume_spike_threshold = volume_spike_threshold
    
    def validate_candle_sequence(
        self,
        candles: List[Candle],
        strict: bool = False
    ) -> Dict[str, Any]:
        """
        Validate a sequence of candles for consistency and quality.
        
        Args:
            candles (List[Candle]): List of candles to validate
            strict (bool): Enable strict validation rules
            
        Returns:
            Dict[str, Any]: Validation results with issues and statistics
        """
        if not candles:
            return {
                'valid': False,
                'issues': ['Empty candle list'],
                'statistics': {}
            }
        
        issues = []
        statistics_data = {}
        
        # Basic validation for each candle
        invalid_candles = []
        for i, candle in enumerate(candles):
            if not validate_candle(candle):
                invalid_candles.append(i)
                issues.append(f"Invalid candle at index {i}")
        
        # Check chronological order
        timestamp_issues = self._check_chronological_order(candles)
        issues.extend(timestamp_issues)
        
        # Check for gaps in timeline
        gap_issues = self._check_timeline_gaps(candles)
        issues.extend(gap_issues)
        
        # Check for price anomalies
        price_issues = self._check_price_anomalies(candles)
        issues.extend(price_issues)
        
        # Check volume anomalies
        volume_issues = self._check_volume_anomalies(candles)
        issues.extend(volume_issues)
        
        # Check OHLC relationships
        ohlc_issues = self._check_ohlc_relationships(candles)
        issues.extend(ohlc_issues)
        
        # Calculate statistics
        if candles:
            prices = [c.close for c in candles]
            volumes = [c.volume for c in candles]
            
            statistics_data = {
                'total_candles': len(candles),
                'invalid_candles': len(invalid_candles),
                'price_range': [min(prices), max(prices)],
                'average_price': statistics.mean(prices),
                'price_volatility': statistics.stdev(prices) if len(prices) > 1 else 0,
                'average_volume': statistics.mean(volumes),
                'volume_volatility': statistics.stdev(volumes) if len(volumes) > 1 else 0,
                'time_span_hours': (candles[-1].timestamp - candles[0].timestamp) / (1000 * 3600)
            }
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'statistics': statistics_data,
            'invalid_candle_indices': invalid_candles
        }
    
    def validate_ticker_data(
        self,
        tickers: List[Ticker]
    ) -> Dict[str, Any]:
        """
        Validate ticker data for consistency.
        
        Args:
            tickers (List[Ticker]): List of tickers to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        if not tickers:
            return {
                'valid': False,
                'issues': ['Empty ticker list'],
                'statistics': {}
            }
        
        issues = []
        statistics_data = {}
        
        # Basic validation for each ticker
        invalid_tickers = []
        for i, ticker in enumerate(tickers):
            if not validate_ticker(ticker):
                invalid_tickers.append(i)
                issues.append(f"Invalid ticker at index {i}")
        
        # Check bid/ask spread reasonableness
        spread_issues = self._check_ticker_spreads(tickers)
        issues.extend(spread_issues)
        
        # Check price consistency
        price_consistency_issues = self._check_ticker_price_consistency(tickers)
        issues.extend(price_consistency_issues)
        
        # Calculate statistics
        if tickers:
            prices = [t.price for t in tickers]
            spreads = [t.spread for t in tickers if t.spread is not None]
            
            statistics_data = {
                'total_tickers': len(tickers),
                'invalid_tickers': len(invalid_tickers),
                'price_range': [min(prices), max(prices)],
                'average_price': statistics.mean(prices),
                'average_spread': statistics.mean(spreads) if spreads else 0,
                'symbols': list(set(t.symbol for t in tickers))
            }
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'statistics': statistics_data,
            'invalid_ticker_indices': invalid_tickers
        }
    
    def validate_order_book(
        self,
        order_book: OrderBook
    ) -> Dict[str, Any]:
        """
        Validate order book data for consistency.
        
        Args:
            order_book (OrderBook): Order book to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        issues = []
        
        # Check basic structure
        if not order_book.bids:
            issues.append("No bid levels found")
        
        if not order_book.asks:
            issues.append("No ask levels found")
        
        # Check bid/ask sorting
        if order_book.bids:
            bid_prices = [bid.price for bid in order_book.bids]
            if bid_prices != sorted(bid_prices, reverse=True):
                issues.append("Bid levels not sorted in descending order")
        
        if order_book.asks:
            ask_prices = [ask.price for ask in order_book.asks]
            if ask_prices != sorted(ask_prices):
                issues.append("Ask levels not sorted in ascending order")
        
        # Check spread
        if order_book.best_bid and order_book.best_ask:
            if order_book.best_bid.price >= order_book.best_ask.price:
                issues.append("Invalid spread: bid >= ask")
        
        # Check for zero quantities
        zero_qty_bids = sum(1 for bid in order_book.bids if bid.quantity <= 0)
        zero_qty_asks = sum(1 for ask in order_book.asks if ask.quantity <= 0)
        
        if zero_qty_bids > 0:
            issues.append(f"{zero_qty_bids} bid levels with zero or negative quantity")
        
        if zero_qty_asks > 0:
            issues.append(f"{zero_qty_asks} ask levels with zero or negative quantity")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'statistics': {
                'bid_levels': len(order_book.bids),
                'ask_levels': len(order_book.asks),
                'spread': order_book.spread,
                'mid_price': order_book.mid_price,
                'bid_depth': order_book.get_bid_depth(),
                'ask_depth': order_book.get_ask_depth()
            }
        }
    
    def validate_trade_sequence(
        self,
        trades: List[Trade]
    ) -> Dict[str, Any]:
        """
        Validate a sequence of trades for consistency.
        
        Args:
            trades (List[Trade]): List of trades to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        if not trades:
            return {
                'valid': False,
                'issues': ['Empty trade list'],
                'statistics': {}
            }
        
        issues = []
        
        # Check chronological order
        timestamps = [trade.timestamp for trade in trades]
        if timestamps != sorted(timestamps):
            issues.append("Trades not in chronological order")
        
        # Check for duplicate trade IDs
        trade_ids = [trade.trade_id for trade in trades]
        if len(trade_ids) != len(set(trade_ids)):
            issues.append("Duplicate trade IDs found")
        
        # Check price and quantity validity
        invalid_trades = []
        for i, trade in enumerate(trades):
            if trade.price <= 0:
                invalid_trades.append(i)
                issues.append(f"Invalid price in trade {i}")
            
            if trade.quantity <= 0:
                invalid_trades.append(i)
                issues.append(f"Invalid quantity in trade {i}")
        
        # Calculate statistics
        prices = [t.price for t in trades]
        quantities = [t.quantity for t in trades]
        volumes = [t.notional_value for t in trades]
        
        statistics_data = {
            'total_trades': len(trades),
            'invalid_trades': len(set(invalid_trades)),
            'price_range': [min(prices), max(prices)],
            'total_volume': sum(volumes),
            'average_trade_size': statistics.mean(quantities),
            'buy_trades': sum(1 for t in trades if t.side == 'buy'),
            'sell_trades': sum(1 for t in trades if t.side == 'sell')
        }
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'statistics': statistics_data,
            'invalid_trade_indices': list(set(invalid_trades))
        }
    
    def detect_outliers(
        self,
        candles: List[Candle],
        field: str = 'close'
    ) -> List[int]:
        """
        Detect outliers in candle data using statistical methods.
        
        Args:
            candles (List[Candle]): List of candles to analyze
            field (str): Field to analyze for outliers ('close', 'volume', etc.)
            
        Returns:
            List[int]: Indices of outlier candles
        """
        if len(candles) < 3:
            return []
        
        values = []
        for candle in candles:
            if field == 'close':
                values.append(candle.close)
            elif field == 'volume':
                values.append(candle.volume)
            elif field == 'high':
                values.append(candle.high)
            elif field == 'low':
                values.append(candle.low)
            elif field == 'price_range':
                values.append(candle.high - candle.low)
            else:
                raise ValueError(f"Unsupported field: {field}")
        
        if len(values) < 3:
            return []
        
        # Calculate mean and standard deviation
        mean_val = statistics.mean(values)
        stdev_val = statistics.stdev(values)
        
        # Find outliers
        outliers = []
        for i, value in enumerate(values):
            z_score = abs(value - mean_val) / stdev_val if stdev_val > 0 else 0
            if z_score > self.outlier_threshold:
                outliers.append(i)
        
        return outliers
    
    def _check_chronological_order(self, candles: List[Candle]) -> List[str]:
        """Check if candles are in chronological order."""
        issues = []
        
        for i in range(1, len(candles)):
            if candles[i].timestamp <= candles[i-1].timestamp:
                issues.append(f"Candle {i} timestamp not greater than previous candle")
        
        return issues
    
    def _check_timeline_gaps(self, candles: List[Candle]) -> List[str]:
        """Check for unusual gaps in timeline."""
        if len(candles) < 2:
            return []
        
        issues = []
        
        # Calculate expected interval from first few candles
        intervals = []
        for i in range(1, min(6, len(candles))):
            interval = candles[i].timestamp - candles[i-1].timestamp
            intervals.append(interval)
        
        if not intervals:
            return []
        
        expected_interval = statistics.median(intervals)
        tolerance = expected_interval * 0.1  # 10% tolerance
        
        # Check for gaps
        for i in range(1, len(candles)):
            actual_interval = candles[i].timestamp - candles[i-1].timestamp
            
            if abs(actual_interval - expected_interval) > tolerance:
                if actual_interval > expected_interval * 2:
                    issues.append(f"Large gap detected between candles {i-1} and {i}")
                elif actual_interval < expected_interval * 0.5:
                    issues.append(f"Abnormally small interval between candles {i-1} and {i}")
        
        return issues
    
    def _check_price_anomalies(self, candles: List[Candle]) -> List[str]:
        """Check for price anomalies and large gaps."""
        if len(candles) < 2:
            return []
        
        issues = []
        
        for i in range(1, len(candles)):
            prev_close = candles[i-1].close
            current_open = candles[i].open
            
            # Check for large price gaps
            price_gap = abs(current_open - prev_close) / prev_close
            if price_gap > self.price_gap_threshold:
                issues.append(f"Large price gap ({price_gap:.2%}) between candles {i-1} and {i}")
        
        return issues
    
    def _check_volume_anomalies(self, candles: List[Candle]) -> List[str]:
        """Check for volume spikes and anomalies."""
        if len(candles) < 3:
            return []
        
        issues = []
        volumes = [c.volume for c in candles]
        median_volume = statistics.median(volumes)
        
        for i, candle in enumerate(candles):
            if candle.volume > median_volume * self.volume_spike_threshold:
                issues.append(f"Volume spike detected in candle {i} ({candle.volume:.2f} vs median {median_volume:.2f})")
        
        return issues
    
    def _check_ohlc_relationships(self, candles: List[Candle]) -> List[str]:
        """Check OHLC price relationships."""
        issues = []
        
        for i, candle in enumerate(candles):
            # High should be the highest price
            if not (candle.high >= candle.open and candle.high >= candle.close):
                issues.append(f"High price not highest in candle {i}")
            
            # Low should be the lowest price
            if not (candle.low <= candle.open and candle.low <= candle.close):
                issues.append(f"Low price not lowest in candle {i}")
            
            # Volume should be non-negative
            if candle.volume < 0:
                issues.append(f"Negative volume in candle {i}")
        
        return issues
    
    def _check_ticker_spreads(self, tickers: List[Ticker]) -> List[str]:
        """Check ticker bid/ask spreads for reasonableness."""
        issues = []
        
        for i, ticker in enumerate(tickers):
            if ticker.spread is not None and ticker.spread_percent is not None:
                # Check for unreasonably wide spreads (>5%)
                if ticker.spread_percent > 5.0:
                    issues.append(f"Unusually wide spread ({ticker.spread_percent:.2f}%) in ticker {i}")
                
                # Check for negative spreads
                if ticker.spread < 0:
                    issues.append(f"Negative spread in ticker {i}")
        
        return issues
    
    def _check_ticker_price_consistency(self, tickers: List[Ticker]) -> List[str]:
        """Check price consistency within ticker data."""
        issues = []
        
        for i, ticker in enumerate(tickers):
            # Price should be between bid and ask
            if ticker.bid is not None and ticker.ask is not None:
                if not (ticker.bid <= ticker.price <= ticker.ask):
                    issues.append(f"Price {ticker.price} not between bid {ticker.bid} and ask {ticker.ask} in ticker {i}")
        
        return issues