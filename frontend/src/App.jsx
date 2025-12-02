import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Activity, RefreshCw, HelpCircle, Bell } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

function App() {
  const [stocks, setStocks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showGuide, setShowGuide] = useState(false)
  const [notificationsEnabled, setNotificationsEnabled] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [marketMood, setMarketMood] = useState(null)
  const [showSmallAccountOnly, setShowSmallAccountOnly] = useState(false)

  const requestNotificationPermission = async () => {
    if (!("Notification" in window)) {
      console.log("Browser doesn't support notifications");
      return;
    }

    // If already granted, just send a test notification
    if (Notification.permission === "granted") {
      new Notification("Stock Advisor", {
        body: "✓ Notifications are enabled. You'll get alerts for Strong Buy/Sell signals.",
        icon: "/vite.svg"
      });
      return;
    }

    // If denied, can't request again
    if (Notification.permission === "denied") {
      console.log("Notifications blocked by user");
      return;
    }

    // Request permission (this will show browser popup)
    try {
      const permission = await Notification.requestPermission();
      setNotificationsEnabled(permission === "granted");

      if (permission === "granted") {
        new Notification("Stock Advisor", {
          body: "✓ Notifications enabled! You'll get alerts for Strong Buy/Sell signals.",
          icon: "/vite.svg"
        });
      }
    } catch (error) {
      console.error("Error requesting notification permission:", error);
    }
  }

  const sendNotification = (type, count) => {
    if (notificationsEnabled && count > 0) {
      const messages = {
        buy: `Found ${count} "Strong Buy" ${count === 1 ? 'opportunity' : 'opportunities'}! Check the dashboard.`,
        sell: `⚠️ ${count} "Strong Sell" ${count === 1 ? 'signal' : 'signals'}! Consider exiting positions.`
      };
      new Notification("Stock Advisor Alert", {
        body: messages[type],
        icon: "/vite.svg"
      });
    }
  }

  const fetchRecommendations = async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setLoading(true)
    }
    setError(null)
    try {
      const response = await fetch('/api/recommendations')
      if (!response.ok) {
        throw new Error('Failed to fetch data')
      }
      const data = await response.json()
      setStocks(data)

      // Extract market mood from first stock (all have same market mood)
      if (data.length > 0 && data[0].market_mood) {
        setMarketMood(data[0].market_mood)
      }

      // Check for Strong Buys and Strong Sells
      const strongBuys = data.filter(s => s.recommendation === "Strong Buy").length
      const strongSells = data.filter(s => s.recommendation === "Strong Sell").length

      if (strongBuys > 0) {
        sendNotification('buy', strongBuys)
      }
      if (strongSells > 0) {
        sendNotification('sell', strongSells)
      }

    } catch (err) {
      setError(err.message)
    } finally {
      if (isManualRefresh) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    fetchRecommendations(true) // Initial load shows spinner

    // Safely check for notification permission
    try {
      if ("Notification" in window && Notification.permission === "granted") {
        setNotificationsEnabled(true)
      }
    } catch (e) {
      console.log("Notification API not supported")
    }
  }, [])

  // Auto-refresh every 5 minutes
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      console.log("Auto-refreshing stock data...")
      fetchRecommendations(false) // Auto-refresh doesn't show spinner
    }, 5 * 60 * 1000) // 5 minutes

    return () => clearInterval(interval)
  }, [autoRefresh])

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="mb-12">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-accent to-purple-500 bg-clip-text text-transparent">
              StockAdvisor.AI
            </h1>
            <p className="text-gray-400 mt-2">Daily Canadian & US Stock Recommendations</p>
          </div>
          <div className="flex gap-4">
            <button
              onClick={requestNotificationPermission}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${notificationsEnabled ? 'bg-success/10 text-success' : 'bg-secondary text-gray-400 hover:text-white'
                }`}
              title={notificationsEnabled ? "Notifications Enabled" : "Enable Notifications"}
            >
              <Bell size={20} />
            </button>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${autoRefresh ? 'bg-accent/20 text-accent' : 'bg-secondary text-gray-400 hover:text-white'
                }`}
              title={autoRefresh ? "Auto-Refresh: ON (every 5 min)" : "Auto-Refresh: OFF"}
            >
              <RefreshCw size={20} className={autoRefresh ? "animate-spin" : ""} />
              {autoRefresh ? "Auto: ON" : "Auto: OFF"}
            </button>
            <button
              onClick={() => setShowGuide(true)}
              className="flex items-center gap-2 px-4 py-2 bg-secondary text-white rounded-lg hover:bg-secondary/80 transition-colors"
            >
              <HelpCircle size={20} />
              Strategy Guide
            </button>
            <button
              onClick={() => setShowSmallAccountOnly(!showSmallAccountOnly)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${showSmallAccountOnly ? 'bg-purple-500 text-white' : 'bg-secondary text-gray-400 hover:text-white'
                }`}
              title="Show only stocks under $50 (Good for small accounts)"
            >
              <TrendingUp size={20} />
              {showSmallAccountOnly ? "Budget: <$50" : "All Stocks"}
            </button>
            <button
              onClick={() => fetchRecommendations(true)}
              className="flex items-center gap-2 px-4 py-2 bg-accent/10 text-accent rounded-lg hover:bg-accent/20 transition-colors"
            >
              <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
              Refresh Now
            </button>
          </div>
        </div>
      </header>

      {marketMood && (
        <div className="glass-card mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-4xl">{marketMood.icon}</span>
            <div>
              <h3 className="text-lg font-bold">Market Mood: {marketMood.label}</h3>
              <p className="text-sm text-gray-400">Sentiment Score: {marketMood.sentiment}</p>
            </div>
          </div>
          <div className="flex-1 ml-8">
            <p className="text-xs text-gray-400 mb-2">Top Market Headlines:</p>
            <ul className="text-xs text-gray-300 space-y-1">
              {marketMood.headlines.map((headline, i) => (
                <li key={i}>• {headline}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <AnimatePresence>
        {showGuide && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowGuide(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="glass-card max-w-2xl w-full"
              onClick={e => e.stopPropagation()}
            >
              <h2 className="text-2xl font-bold mb-4 text-accent">How to Use StockAdvisor.AI</h2>
              <div className="space-y-4 text-gray-300">
                <p>
                  Our "Robot Advisor" analyzes market trends and news sentiment to give you a daily edge.
                </p>
                <div className="bg-black/20 p-4 rounded-lg border-l-4 border-success">
                  <h3 className="font-bold text-white mb-1">🚀 The "Strong Buy" Signal</h3>
                  <p className="text-sm">
                    Look for stocks labeled <strong>Strong Buy</strong> with a Confidence Score <strong>above 85%</strong>.
                    This means technical indicators (RSI, MACD) and News Sentiment are ALL positive.
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-black/20 p-4 rounded-lg">
                    <h3 className="font-bold text-white mb-1">📈 Buy</h3>
                    <p className="text-sm">Good potential. Confidence 65-84%. Worth watching or small position.</p>
                  </div>
                  <div className="bg-black/20 p-4 rounded-lg">
                    <h3 className="font-bold text-white mb-1">✋ Hold</h3>
                    <p className="text-sm">Mixed signals. Market is undecided. Wait for a clearer trend.</p>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-4">
                  *Disclaimer: This is an AI-based analysis tool, not financial advice. Past performance does not guarantee future results. Always do your own research.
                </p>
                <button
                  onClick={() => setShowGuide(false)}
                  className="w-full mt-6 py-2 bg-accent text-black font-bold rounded-lg hover:bg-accent/90 transition-colors"
                >
                  Got it, let's trade!
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {error && (
        <div className="bg-danger/10 text-danger p-4 rounded-lg mb-8 border border-danger/20">
          Error: {error}. Is the backend running?
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-card h-64 animate-pulse"></div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {stocks
            .filter(stock => !showSmallAccountOnly || stock.price < 50)
            .map((stock, index) => (
              <StockCard key={stock.ticker} stock={stock} index={index} />
            ))}
        </div>
      )}
    </div>
  )
}

function StockCard({ stock, index }) {
  const isPositive = stock.change_percent >= 0
  const isBuy = stock.recommendation.includes("Buy")
  const currency = stock.ticker.includes('.TO') ? 'CAD' : 'USD'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="glass-card hover:border-accent/50 transition-colors group"
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h2 className="text-2xl font-bold">{stock.ticker}</h2>
          <div className={`flex items-center gap-1 ${isPositive ? 'text-success' : 'text-danger'}`}>
            {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
            <span className="font-mono">${stock.price.toFixed(2)} {currency}</span>
            <span className="text-sm">({stock.change_percent > 0 ? '+' : ''}{stock.change_percent.toFixed(2)}%)</span>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-bold ${isBuy ? 'bg-success/20 text-success' : 'bg-yellow-500/20 text-yellow-500'
          }`}>
          {stock.recommendation}
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <div className="flex justify-between text-sm text-gray-400 mb-1">
            <span>Confidence Score</span>
            <span>{stock.confidence_score.toFixed(1)}%</span>
          </div>
          <div className="h-2 bg-secondary rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-accent"
              style={{ width: `${stock.confidence_score}%` }}
            ></div>
          </div>
        </div>

        <div className="bg-black/20 p-3 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
            <Activity size={14} /> Analysis
          </h3>
          <ul className="text-xs text-gray-400 space-y-1">
            {stock.reasoning.slice(0, 3).map((reason, i) => (
              <li key={i}>• {reason}</li>
            ))}
          </ul>
        </div>

        {stock.confidence_score > 65 && (
          <button
            onClick={(e) => {
              e.preventDefault();
              const ticker = stock.ticker.replace('.TO', '');
              navigator.clipboard.writeText(ticker);
              alert(`Ticker "${ticker}" copied to clipboard! Pasting it in Wealthsimple...`);
              window.open('https://my.wealthsimple.com/app/trade', '_blank');
            }}
            className={`block w-full mt-4 py-2 text-center rounded-lg font-semibold transition-colors ${stock.recommendation === "Strong Buy"
              ? "bg-success text-black hover:bg-success/90"
              : "bg-blue-500 text-white hover:bg-blue-600"
              }`}
          >
            Trade on Wealthsimple →
          </button>
        )}
      </div>
    </motion.div>
  )
}

export default App
