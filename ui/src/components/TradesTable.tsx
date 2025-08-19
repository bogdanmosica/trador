// This component displays a paginated table of trade history.
import React from 'react';
import { Trade } from '@/types/bots';

interface TradesTableProps {
  trades: Trade[];
}

const TradesTable: React.FC<TradesTableProps> = ({ trades }) => {
  return (
    <div className="border p-4 rounded-lg shadow-sm">
      <h3 className="text-lg font-semibold">Trade History</h3>
      <table className="min-w-full divide-y divide-gray-200">
        <thead>
          <tr>
            <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
            <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
            <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Side</th>
            <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
            <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {trades.map((trade, index) => (
            <tr key={index}>
              <td className="px-6 py-4 whitespace-nowrap">{new Date(trade.timestamp).toLocaleString()}</td>
              <td className="px-6 py-4 whitespace-nowrap">{trade.symbol}</td>
              <td className="px-6 py-4 whitespace-nowrap">{trade.side}</td>
              <td className="px-6 py-4 whitespace-nowrap">{trade.price}</td>
              <td className="px-6 py-4 whitespace-nowrap">{trade.quantity}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {/* Placeholder for pagination */}
      <div className="mt-4 text-center text-sm text-gray-500">Pagination controls here</div>
    </div>
  );
};

export default TradesTable;
