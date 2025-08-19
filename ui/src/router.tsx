import { useState } from 'react';
import {
  createRouter,
  createRoute,
  createRootRoute,
  Outlet,
} from '@tanstack/react-router'
import { useBots, useBotStatus, useBotRisk, useBotTrades } from '@/hooks/useBots'
import BotCard from '@/components/BotCard'
import StrategyDetails from '@/components/StrategyDetails'
import TradesHistory from '@/components/TradesHistory'
import BotControls from '@/components/BotControls'
import RiskPanel from '@/components/RiskPanel'
import TradesTable from '@/components/TradesTable'
import Navigation from '@/components/Navigation'
import BotModal from '@/components/BotModal'
import Dashboard from '@/components/Dashboard'
import { Link } from '@tanstack/react-router'

// Root route
const rootRoute = createRootRoute({
  component: () => (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="container mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  ),
})

// Index route
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: Dashboard,
})

// Bots route
const botsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/bots',
  component: function BotsComponent() {
    const { data: bots, isLoading, isError, error } = useBots()
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-gray-600">Loading bots...</div>
        </div>
      )
    }

    if (isError) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-red-600">Error loading bots: {error?.message}</div>
        </div>
      )
    }

    const activeBots = bots?.filter(bot => bot.status === 'running') || []
    const inactiveBots = bots?.filter(bot => bot.status !== 'running') || []

    return (
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Trading Bots</h1>
            <p className="text-gray-600 mt-1">Manage all your trading bots</p>
          </div>
          <button 
            onClick={() => setIsCreateModalOpen(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            + New Bot
          </button>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Bots</p>
                <p className="text-2xl font-bold text-gray-900">{bots?.length || 0}</p>
              </div>
              <span className="text-2xl">🤖</span>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active</p>
                <p className="text-2xl font-bold text-green-600">{activeBots.length}</p>
              </div>
              <span className="text-2xl">✅</span>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Inactive</p>
                <p className="text-2xl font-bold text-gray-600">{inactiveBots.length}</p>
              </div>
              <span className="text-2xl">⏸️</span>
            </div>
          </div>
        </div>

        {/* Bots Grid */}
        {bots?.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
            <span className="text-4xl mb-4 block">🤖</span>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No trading bots yet</h3>
            <p className="text-gray-600 mb-4">Create your first bot to start automated trading.</p>
            <button 
              onClick={() => setIsCreateModalOpen(true)}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Create Your First Bot
            </button>
          </div>
        ) : (
          <div>
            {/* Active Bots */}
            {activeBots.length > 0 && (
              <div className="mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
                  Active Bots ({activeBots.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {activeBots.map((bot) => (
                    <BotCard key={bot.id} bot={bot} />
                  ))}
                </div>
              </div>
            )}

            {/* Inactive Bots */}
            {inactiveBots.length > 0 && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="w-3 h-3 bg-gray-400 rounded-full mr-2"></span>
                  Inactive Bots ({inactiveBots.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {inactiveBots.map((bot) => (
                    <BotCard key={bot.id} bot={bot} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Create Bot Modal */}
        <BotModal 
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          mode="create"
        />
      </div>
    )
  },
})

// Bot detail route
const botDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/bots/$botId',
  component: function BotDetailComponent() {
    const { botId } = botDetailRoute.useParams()
    const { data: status, isLoading, isError, error } = useBotStatus(botId)

    if (isLoading) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading bot details...</p>
          </div>
        </div>
      )
    }

    if (isError) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <span className="text-4xl mb-4 block">⚠️</span>
            <p className="text-red-600 text-lg">Error loading bot details</p>
            <p className="text-gray-500 text-sm mt-2">{error?.message}</p>
          </div>
        </div>
      )
    }

    if (!status) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <span className="text-4xl mb-4 block">🤖</span>
            <p className="text-gray-600 text-lg">Bot details not found</p>
          </div>
        </div>
      )
    }

    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                  <span className="mr-3">🤖</span>
                  {botId}
                </h1>
                <p className="text-gray-600 mt-1">Trading Bot Management Dashboard</p>
              </div>
              <Link 
                to="/bots/$botId/risk" 
                params={{ botId }} 
                className="inline-flex items-center px-4 py-2 bg-orange-50 hover:bg-orange-100 text-orange-700 border border-orange-200 rounded-lg text-sm font-medium transition-colors"
              >
                <span className="mr-2">⚠️</span>
                View Risk Analysis
              </Link>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="space-y-8">
            {/* Bot Controls */}
            <BotControls botId={botId} />

            {/* Strategy Details */}
            <StrategyDetails status={status} />

            {/* Trades History */}
            <TradesHistory botId={botId} />
          </div>
        </div>
        
        <Outlet />
      </div>
    )
  },
})

// Bot risk route
const botRiskRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/bots/$botId/risk',
  component: function BotRiskComponent() {
    const { botId } = botRiskRoute.useParams()
    const { data: risk, isLoading, isError, error } = useBotRisk(botId)

    if (isLoading) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading risk analysis...</p>
          </div>
        </div>
      )
    }

    if (isError) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <span className="text-4xl mb-4 block">⚠️</span>
            <p className="text-red-600 text-lg">Error loading risk data</p>
            <p className="text-gray-500 text-sm mt-2">{error?.message}</p>
          </div>
        </div>
      )
    }

    if (!risk) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <span className="text-4xl mb-4 block">📊</span>
            <p className="text-gray-600 text-lg">No risk data found</p>
          </div>
        </div>
      )
    }

    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                  <span className="mr-3">🛡️</span>
                  Risk Analysis - {botId}
                </h1>
                <p className="text-gray-600 mt-1">Real-time risk monitoring and safety controls</p>
              </div>
              <Link 
                to="/bots/$botId" 
                params={{ botId }} 
                className="inline-flex items-center px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-lg text-sm font-medium transition-colors"
              >
                <span className="mr-2">🤖</span>
                Back to Bot Details
              </Link>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <RiskPanel risk={risk} />
        </div>
      </div>
    )
  },
})

// Bot trades route
const botTradesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/bots/$botId/trades',
  component: function BotTradesComponent() {
    const { botId } = botTradesRoute.useParams()
    const { data: trades, isLoading, isError, error } = useBotTrades(botId)

    if (isLoading) return <div>Loading trades...</div>
    if (isError) return <div>Error loading trades: {error?.message}</div>
    if (!trades) return <div>No trades found.</div>

    return (
      <div className="p-4">
        <h2 className="text-xl font-bold mb-4">Trades for {botId}</h2>
        <TradesTable trades={trades} />
      </div>
    )
  },
})

// Create the route tree
const routeTree = rootRoute.addChildren([
  indexRoute,
  botsRoute,
  botDetailRoute,
  botRiskRoute,
  botTradesRoute,
])

// Create the router
export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}