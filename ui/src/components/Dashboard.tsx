import { useBots, useGlobalMetrics } from '@/hooks/useBots'
import BotCard from '@/components/BotCard'
import { Link } from '@tanstack/react-router'

/**
 * Dashboard component that displays an overview of all trading bots
 * and key performance metrics.
 */
const Dashboard = () => {
  const { data: bots, isLoading: botsLoading, isError: botsError } = useBots()
  const { data: metrics, isLoading: metricsLoading, isError: metricsError } = useGlobalMetrics()

  if (botsLoading || metricsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading dashboard...</div>
      </div>
    )
  }

  if (botsError || metricsError) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-red-600">Error loading dashboard data</div>
      </div>
    )
  }

  const activeBots = bots?.filter(bot => bot.status === 'running') || []
  const totalBots = bots?.length || 0

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Trading Dashboard</h1>
          <p className="text-gray-600 mt-1">Monitor and manage your trading bots</p>
        </div>
        <Link 
          to="/bots" 
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          View All Bots
        </Link>
      </div>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100">
              <span className="text-2xl">🤖</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Bots</p>
              <p className="text-2xl font-bold text-gray-900">{totalBots}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100">
              <span className="text-2xl">✅</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Bots</p>
              <p className="text-2xl font-bold text-gray-900">{activeBots.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-yellow-100">
              <span className="text-2xl">💰</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total P&L</p>
              <p className="text-2xl font-bold text-gray-900">
                {metrics?.total_pnl ? `$${metrics.total_pnl.toFixed(2)}` : '$0.00'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100">
              <span className="text-2xl">📈</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Trades</p>
              <p className="text-2xl font-bold text-gray-900">
                {metrics?.total_trades || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Bots */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Recent Bots</h2>
          <Link 
            to="/bots" 
            className="text-blue-600 hover:text-blue-700 font-medium text-sm"
          >
            View all →
          </Link>
        </div>
        
        {totalBots === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
            <span className="text-4xl mb-4 block">🤖</span>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No trading bots yet</h3>
            <p className="text-gray-600 mb-4">Get started by creating your first trading bot.</p>
            <Link 
              to="/bots" 
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Create Bot
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {bots?.slice(0, 6).map((bot) => (
              <BotCard key={bot.id} bot={bot} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard