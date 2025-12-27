import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import {
  Activity, AlertCircle, CheckCircle, Settings, TrendingUp,
  Zap, Code, ShoppingCart, Palette, Shield, BarChart3,
  Clock, Users, Layers, Download, Play, RefreshCw, Search
} from 'lucide-react';

export default function DevSkyyDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [darkMode, setDarkMode] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState('all');
  const [dateRange, setDateRange] = useState('7d');
  const [metrics, setMetrics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Mock API data - replace with real API calls
  const fetchMetrics = useCallback(async () => {
    setIsLoading(true);
    try {
      // Simulating API call - replace with real endpoints
      const data = {
        themeBuilder: {
          themesGenerated: 156,
          totalExports: 289,
          avgGenerationTime: 1.8,
          successRate: 98.5,
          activeThemes: 45,
          status: 'healthy'
        },
        selfHealing: {
          totalScans: 3450,
          issuesFound: 12847,
          autoFixed: 9234,
          criticalIssues: 23,
          scanAvgTime: 4.2,
          status: 'healthy'
        },
        productManager: {
          totalProducts: 1250,
          productsCreated: 45,
          inventoryUpdates: 234,
          bulkOperations: 12,
          avgResponse: 250,
          status: 'healthy'
        },
        system: {
          uptime: 99.8,
          apiLatency: 45,
          dbHealth: 99.2,
          cpuUsage: 34,
          memoryUsage: 62
        }
      };
      setMetrics(data);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    if (autoRefresh) {
      const interval = setInterval(fetchMetrics, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, fetchMetrics]);

  if (!metrics || isLoading) {
    return (
      <div className={`${darkMode ? 'bg-slate-950 text-white' : 'bg-white text-slate-900'} min-h-screen flex items-center justify-center`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-lg">Loading DevSkyy Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`${darkMode ? 'bg-slate-950 text-white' : 'bg-gradient-to-br from-slate-50 to-slate-100 text-slate-900'} min-h-screen`}>
      {/* Header */}
      <header className={`${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border-b sticky top-0 z-40`}>
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                <Layers className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">DevSkyy Enterprise</h1>
                <p className="text-xs opacity-60">v6.0 â€¢ Production Dashboard</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center gap-2 bg-opacity-20 bg-green-500 px-3 py-1 rounded-full">
                <Activity className="h-4 w-4 text-green-400 animate-pulse" />
                <span className="text-sm font-medium">All Systems Operational</span>
              </div>

              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`p-2 rounded-lg transition-all ${autoRefresh ? 'bg-purple-500 text-white' : darkMode ? 'bg-slate-800 text-slate-400' : 'bg-slate-200 text-slate-600'}`}
              >
                <RefreshCw className="h-5 w-5" />
              </button>

              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`p-2 rounded-lg transition-all ${darkMode ? 'bg-slate-800 text-yellow-400' : 'bg-slate-200 text-slate-600'}`}
              >
                {darkMode ? 'â˜€ï¸' : 'ðŸŒ™'}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <MetricCard
            icon={<Palette className="h-6 w-6" />}
            title="Theme Builder"
            value={metrics.themeBuilder.themesGenerated}
            subtitle={`${metrics.themeBuilder.successRate}% success rate`}
            trend="+12%"
            status={metrics.themeBuilder.status}
            darkMode={darkMode}
          />
          <MetricCard
            icon={<Shield className="h-6 w-6" />}
            title="Self-Healing"
            value={metrics.selfHealing.issuesFound}
            subtitle={`${metrics.selfHealing.autoFixed} auto-fixed`}
            trend="+8%"
            status={metrics.selfHealing.status}
            darkMode={darkMode}
          />
          <MetricCard
            icon={<ShoppingCart className="h-6 w-6" />}
            title="Product Manager"
            value={metrics.productManager.totalProducts}
            subtitle={`${metrics.productManager.productsCreated} this week`}
            trend="+5%"
            status={metrics.productManager.status}
            darkMode={darkMode}
          />
          <MetricCard
            icon={<TrendingUp className="h-6 w-6" />}
            title="System Health"
            value={`${metrics.system.uptime}%`}
            subtitle={`${metrics.system.apiLatency}ms latency`}
            trend="Optimal"
            status="healthy"
            darkMode={darkMode}
          />
        </div>

        {/* Navigation Tabs */}
        <div className={`${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg mb-8 overflow-hidden`}>
          <div className="flex flex-wrap">
            {['overview', 'themeBuilder', 'selfHealing', 'products', 'analytics'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 px-6 py-3 font-medium transition-all border-b-2 ${
                  activeTab === tab
                    ? 'border-purple-500 text-purple-400'
                    : darkMode
                    ? 'border-transparent text-slate-400 hover:text-slate-300'
                    : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1).replace(/([A-Z])/g, ' $1')}
              </button>
            ))}
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && <OverviewTab metrics={metrics} darkMode={darkMode} />}

        {/* Theme Builder Tab */}
        {activeTab === 'themeBuilder' && <ThemeBuilderTab metrics={metrics} darkMode={darkMode} />}

        {/* Self-Healing Tab */}
        {activeTab === 'selfHealing' && <SelfHealingTab metrics={metrics} darkMode={darkMode} />}

        {/* Products Tab */}
        {activeTab === 'products' && <ProductsTab metrics={metrics} darkMode={darkMode} />}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && <AnalyticsTab metrics={metrics} darkMode={darkMode} />}
      </main>
    </div>
  );
}

function MetricCard({ icon, title, value, subtitle, trend, status, darkMode }) {
  return (
    <div className={`${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-6 hover:shadow-lg transition-all`}>
      <div className="flex justify-between items-start mb-4">
        <div className={`p-2 rounded-lg ${status === 'healthy' ? 'bg-green-500 bg-opacity-20 text-green-400' : 'bg-red-500 bg-opacity-20 text-red-400'}`}>
          {icon}
        </div>
        <span className="text-xs font-bold text-purple-400">{trend}</span>
      </div>
      <h3 className={`text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-600'} mb-1`}>{title}</h3>
      <p className="text-3xl font-bold mb-2">{value}</p>
      <p className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-500'}`}>{subtitle}</p>
    </div>
  );
}

function OverviewTab({ metrics, darkMode }) {
  const performanceData = [
    { name: 'Theme Gen', value: 98 },
    { name: 'Code Scan', value: 95 },
    { name: 'Products', value: 99 },
    { name: 'API', value: 97 }
  ];

  const timeSeriesData = [
    { time: '00:00', themes: 12, scans: 45, products: 23 },
    { time: '04:00', themes: 19, scans: 52, products: 34 },
    { time: '08:00', themes: 28, scans: 67, products: 45 },
    { time: '12:00', themes: 35, scans: 89, products: 67 },
    { time: '16:00', themes: 42, scans: 102, products: 89 },
    { time: '20:00', themes: 38, scans: 95, products: 78 },
    { time: '24:00', themes: 45, scans: 112, products: 95 }
  ];

  return (
    <div className="space-y-8">
      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Performance Overview */}
        <ChartCard title="Agent Performance" darkMode={darkMode}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#334155' : '#e2e8f0'} />
              <XAxis stroke={darkMode ? '#94a3b8' : '#64748b'} />
              <YAxis stroke={darkMode ? '#94a3b8' : '#64748b'} />
              <Tooltip
                contentStyle={{
                  backgroundColor: darkMode ? '#1e293b' : '#f8fafc',
                  border: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`,
                  borderRadius: '8px',
                  color: darkMode ? '#e2e8f0' : '#1e293b'
                }}
              />
              <Bar dataKey="value" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Activity Timeline */}
        <ChartCard title="24-Hour Activity" darkMode={darkMode}>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={timeSeriesData}>
              <defs>
                <linearGradient id="colorThemes" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#334155' : '#e2e8f0'} />
              <XAxis stroke={darkMode ? '#94a3b8' : '#64748b'} />
              <YAxis stroke={darkMode ? '#94a3b8' : '#64748b'} />
              <Tooltip
                contentStyle={{
                  backgroundColor: darkMode ? '#1e293b' : '#f8fafc',
                  border: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`,
                  borderRadius: '8px'
                }}
              />
              <Area type="monotone" dataKey="themes" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorThemes)" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Recent Activity */}
      <div className={`${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-6`}>
        <h3 className="text-lg font-bold mb-4">Recent Activity</h3>
        <div className="space-y-3">
          <ActivityItem
            icon={<Palette className="h-4 w-4" />}
            title="Theme generated"
            desc="Luxury Fashion theme for luxury_fashion_co"
            time="2 min ago"
            darkMode={darkMode}
          />
          <ActivityItem
            icon={<CheckCircle className="h-4 w-4" />}
            title="Code scan completed"
            desc="42 issues found, 28 auto-fixed"
            time="5 min ago"
            darkMode={darkMode}
          />
          <ActivityItem
            icon={<ShoppingCart className="h-4 w-4" />}
            title="Bulk product import"
            desc="250 products imported successfully"
            time="15 min ago"
            darkMode={darkMode}
          />
        </div>
      </div>
    </div>
  );
}

function ThemeBuilderTab({ metrics, darkMode }) {
  return (
    <div className="space-y-8">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatBox label="Themes Generated" value={metrics.themeBuilder.themesGenerated} darkMode={darkMode} />
        <StatBox label="Avg Generation Time" value={`${metrics.themeBuilder.avgGenerationTime}s`} darkMode={darkMode} />
        <StatBox label="Success Rate" value={`${metrics.themeBuilder.successRate}%`} darkMode={darkMode} />
      </div>

      {/* Theme Types Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <ChartCard title="Themes by Type" darkMode={darkMode}>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Luxury Fashion', value: 45 },
                  { name: 'Streetwear', value: 35 },
                  { name: 'Minimalist', value: 25 },
                  { name: 'Vintage', value: 15 },
                  { name: 'Other', value: 15 }
                ]}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8b5cf6"
                dataKey="value"
              >
                <Cell fill="#8b5cf6" />
                <Cell fill="#06b6d4" />
                <Cell fill="#ec4899" />
                <Cell fill="#f59e0b" />
                <Cell fill="#10b981" />
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Export Formats */}
        <ChartCard title="Export Formats" darkMode={darkMode}>
          <div className="space-y-4">
            {[
              { format: 'ZIP Packages', count: 156, percentage: 65 },
              { format: 'JSON Export', count: 52, percentage: 22 },
              { format: 'Direct Upload', count: 35, percentage: 13 }
            ].map((item) => (
              <div key={item.format}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium">{item.format}</span>
                  <span className="text-sm text-purple-400">{item.count}</span>
                </div>
                <div className={`${darkMode ? 'bg-slate-800' : 'bg-slate-200'} rounded-full h-2 overflow-hidden`}>
                  <div
                    className="bg-gradient-to-r from-purple-500 to-blue-500 h-full"
                    style={{ width: `${item.percentage}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      {/* Theme Builder Actions */}
      <div className={`${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-6`}>
        <h3 className="text-lg font-bold mb-4">Generate New Theme</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input type="text" placeholder="Brand Name" className={`px-4 py-2 rounded-lg border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-300'}`} />
          <select className={`px-4 py-2 rounded-lg border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-300'}`}>
            <option>Luxury Fashion</option>
            <option>Streetwear</option>
            <option>Minimalist</option>
          </select>
          <button className="col-span-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white px-6 py-2 rounded-lg font-bold transition-all flex items-center justify-center gap-2">
            <Play className="h-4 w-4" />
            Generate Theme
          </button>
        </div>
      </div>
    </div>
  );
}

function SelfHealingTab({ metrics, darkMode }) {
  const severityData = [
    { severity: 'Critical', count: 23, percentage: 0.2 },
    { severity: 'High', count: 145, percentage: 1.1 },
    { severity: 'Medium', count: 892, percentage: 7.0 },
    { severity: 'Low', count: 11787, percentage: 91.7 }
  ];

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatBox label="Total Scans" value={metrics.selfHealing.totalScans} darkMode={darkMode} />
        <StatBox label="Issues Found" value={metrics.selfHealing.issuesFound} darkMode={darkMode} />
        <StatBox label="Auto-Fixed" value={metrics.selfHealing.autoFixed} darkMode={darkMode} />
        <StatBox label="Avg Scan Time" value={`${metrics.selfHealing.scanAvgTime}s`} darkMode={darkMode} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Severity Distribution */}
        <ChartCard title="Issues by Severity" darkMode={darkMode}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={severityData}>
              <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#334155' : '#e2e8f0'} />
              <XAxis dataKey="severity" stroke={darkMode ? '#94a3b8' : '#64748b'} />
              <YAxis stroke={darkMode ? '#94a3b8' : '#64748b'} />
              <Tooltip
                contentStyle={{
                  backgroundColor: darkMode ? '#1e293b' : '#f8fafc',
                  border: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`,
                  borderRadius: '8px'
                }}
              />
              <Bar dataKey="count" fill="#ef4444" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Fix Success Rate */}
        <ChartCard title="Remediation Statistics" darkMode={darkMode}>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Auto-Fix Success</span>
                <span className="text-purple-400 font-bold">74%</span>
              </div>
              <div className={`${darkMode ? 'bg-slate-800' : 'bg-slate-200'} rounded-full h-3 overflow-hidden`}>
                <div className="bg-gradient-to-r from-green-500 to-emerald-500 h-full" style={{ width: '74%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Critical Issues Resolved</span>
                <span className="text-blue-400 font-bold">96%</span>
              </div>
              <div className={`${darkMode ? 'bg-slate-800' : 'bg-slate-200'} rounded-full h-3 overflow-hidden`}>
                <div className="bg-gradient-to-r from-blue-500 to-cyan-500 h-full" style={{ width: '96%' }}></div>
              </div>
            </div>
          </div>
        </ChartCard>
      </div>

      {/* Scan Trigger */}
      <div className={`${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-6`}>
        <h3 className="text-lg font-bold mb-4">Trigger Code Scan</h3>
        <div className="flex gap-4">
          <input type="text" placeholder="Directory path (e.g., ./src)" className={`flex-1 px-4 py-2 rounded-lg border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-300'}`} />
          <button className="bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white px-6 py-2 rounded-lg font-bold transition-all flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Scan
          </button>
        </div>
      </div>
    </div>
  );
}

function ProductsTab({ metrics, darkMode }) {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatBox label="Total Products" value={metrics.productManager.totalProducts} darkMode={darkMode} />
        <StatBox label="Created This Week" value={metrics.productManager.productsCreated} darkMode={darkMode} />
        <StatBox label="Inventory Updates" value={metrics.productManager.inventoryUpdates} darkMode={darkMode} />
        <StatBox label="Avg Response" value={`${metrics.productManager.avgResponse}ms`} darkMode={darkMode} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Product Status */}
        <ChartCard title="Product Status Distribution" darkMode={darkMode}>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Published', value: 1050 },
                  { name: 'Draft', value: 150 },
                  { name: 'Pending', value: 35 },
                  { name: 'Archived', value: 15 }
                ]}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8b5cf6"
                dataKey="value"
              >
                <Cell fill="#10b981" />
                <Cell fill="#3b82f6" />
                <Cell fill="#f59e0b" />
                <Cell fill="#6b7280" />
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Variant Distribution */}
        <ChartCard title="Top Categories" darkMode={darkMode}>
          <div className="space-y-3">
            {[
              { category: 'Jackets', count: 256, growth: '+12%' },
              { category: 'Dresses', count: 198, growth: '+8%' },
              { category: 'Accessories', count: 187, growth: '+5%' },
              { category: 'Footwear', count: 156, growth: '+3%' }
            ].map((item) => (
              <div key={item.category} className="flex justify-between items-center">
                <span className="font-medium">{item.category}</span>
                <div className="flex items-center gap-3">
                  <span className="text-slate-400">{item.count}</span>
                  <span className="text-green-400 text-sm">{item.growth}</span>
                </div>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      {/* Product Actions */}
      <div className={`${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-6`}>
        <h3 className="text-lg font-bold mb-4">Create New Product</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input type="text" placeholder="Product Name" className={`px-4 py-2 rounded-lg border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-300'}`} />
          <input type="text" placeholder="SKU" className={`px-4 py-2 rounded-lg border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-300'}`} />
          <input type="number" placeholder="Price" className={`px-4 py-2 rounded-lg border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-300'}`} />
          <button className="col-span-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white px-6 py-2 rounded-lg font-bold transition-all flex items-center justify-center gap-2">
            <ShoppingCart className="h-4 w-4" />
            Create Product
          </button>
        </div>
      </div>
    </div>
  );
}

function AnalyticsTab({ metrics, darkMode }) {
  const radarData = [
    { subject: 'Performance', A: 86, fullMark: 100 },
    { subject: 'Reliability', A: 95, fullMark: 100 },
    { subject: 'Security', A: 92, fullMark: 100 },
    { subject: 'Scalability', A: 88, fullMark: 100 },
    { subject: 'Efficiency', A: 90, fullMark: 100 },
    { subject: 'User Experience', A: 87, fullMark: 100 }
  ];

  return (
    <div className="space-y-8">
      {/* System Health Radar */}
      <ChartCard title="System Health Analysis" darkMode={darkMode}>
        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={radarData}>
            <PolarGrid stroke={darkMode ? '#334155' : '#e2e8f0'} />
            <PolarAngleAxis dataKey="subject" stroke={darkMode ? '#94a3b8' : '#64748b'} />
            <PolarRadiusAxis stroke={darkMode ? '#94a3b8' : '#64748b'} />
            <Radar name="Health Score" dataKey="A" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
            <Tooltip
              contentStyle={{
                backgroundColor: darkMode ? '#1e293b' : '#f8fafc',
                border: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`,
                borderRadius: '8px'
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Resource Usage */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <ChartCard title="CPU Usage" darkMode={darkMode}>
          <div className="space-y-4">
            <div className="text-center py-8">
              <div className="relative inline-flex items-center justify-center w-32 h-32">
                <div className="absolute w-full h-full rounded-full border-8 border-slate-700 border-t-purple-500 animate-spin"></div>
                <div className="text-3xl font-bold">{metrics.system.cpuUsage}%</div>
              </div>
            </div>
            <p className="text-center text-sm text-slate-400">Current usage within optimal range</p>
          </div>
        </ChartCard>

        <ChartCard title="Memory Usage" darkMode={darkMode}>
          <div className="space-y-4">
            <div className="text-center py-8">
              <div className="relative inline-flex items-center justify-center w-32 h-32">
                <div className="absolute w-full h-full rounded-full border-8 border-slate-700 border-t-blue-500 animate-spin"></div>
                <div className="text-3xl font-bold">{metrics.system.memoryUsage}%</div>
              </div>
            </div>
            <p className="text-center text-sm text-slate-400">Memory allocation optimal</p>
          </div>
        </ChartCard>
      </div>

      {/* Monthly Summary */}
      <ChartCard title="Monthly Performance Summary" darkMode={darkMode}>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart
            data={[
              { month: 'Jan', themes: 120, scans: 340, products: 420 },
              { month: 'Feb', themes: 150, scans: 380, products: 520 },
              { month: 'Mar', themes: 180, scans: 420, products: 620 },
              { month: 'Apr', themes: 220, scans: 480, products: 750 }
            ]}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#334155' : '#e2e8f0'} />
            <XAxis stroke={darkMode ? '#94a3b8' : '#64748b'} />
            <YAxis stroke={darkMode ? '#94a3b8' : '#64748b'} />
            <Tooltip
              contentStyle={{
                backgroundColor: darkMode ? '#1e293b' : '#f8fafc',
                border: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`,
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Line type="monotone" dataKey="themes" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6' }} />
            <Line type="monotone" dataKey="scans" stroke="#06b6d4" strokeWidth={2} dot={{ fill: '#06b6d4' }} />
            <Line type="monotone" dataKey="products" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981' }} />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

function ChartCard({ title, children, darkMode }) {
  return (
    <div className={`${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-6`}>
      <h3 className="text-lg font-bold mb-4">{title}</h3>
      {children}
    </div>
  );
}

function StatBox({ label, value, darkMode }) {
  return (
    <div className={`${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-4`}>
      <p className={`text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}

function ActivityItem({ icon, title, desc, time, darkMode }) {
  return (
    <div className="flex gap-3 pb-3 border-b border-opacity-10 border-white">
      <div className="text-purple-400 mt-1">{icon}</div>
      <div className="flex-1">
        <p className="font-medium">{title}</p>
        <p className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>{desc}</p>
      </div>
      <span className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-500'}`}>{time}</span>
    </div>
  );
}
