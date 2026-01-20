import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import React, { useState, useEffect, useCallback } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';
import { Activity, AlertCircle, CheckCircle, Settings, TrendingUp, Zap, Code, ShoppingCart, Palette, Shield, BarChart3, Clock, Users, Layers, Download, Play, RefreshCw, Search } from 'lucide-react';
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
        }
        catch (error) {
            console.error('Failed to fetch metrics:', error);
        }
        finally {
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
        return (_jsx("div", { className: `${darkMode ? 'bg-slate-950 text-white' : 'bg-white text-slate-900'} min-h-screen flex items-center justify-center`, children: _jsxs("div", { className: "text-center", children: [_jsx("div", { className: "animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4" }), _jsx("p", { className: "text-lg", children: "Loading DevSkyy Dashboard..." })] }) }));
    }
    return (_jsxs("div", { className: `${darkMode ? 'bg-slate-950 text-white' : 'bg-linear-to-br from-slate-50 to-slate-100 text-slate-900'} min-h-screen`, children: [_jsx("header", { className: `${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border-b sticky top-0 z-40`, children: _jsx("div", { className: "max-w-7xl mx-auto px-6 py-4", children: _jsxs("div", { className: "flex justify-between items-center", children: [_jsxs("div", { className: "flex items-center gap-3", children: [_jsx("div", { className: "h-10 w-10 bg-linear-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center", children: _jsx(Layers, { className: "h-6 w-6 text-white" }) }), _jsxs("div", { children: [_jsx("h1", { className: "text-2xl font-bold", children: "DevSkyy Enterprise" }), _jsx("p", { className: "text-xs opacity-60", children: "v6.0 \u00E2\u20AC\u00A2 Production Dashboard" })] })] }), _jsxs("div", { className: "flex items-center gap-4", children: [_jsxs("div", { className: "hidden md:flex items-center gap-2 bg-opacity-20 bg-green-500 px-3 py-1 rounded-full", children: [_jsx(Activity, { className: "h-4 w-4 text-green-400 animate-pulse" }), _jsx("span", { className: "text-sm font-medium", children: "All Systems Operational" })] }), _jsx("button", { onClick: () => setAutoRefresh(!autoRefresh), className: `p-2 rounded-lg transition-all ${autoRefresh ? 'bg-purple-500 text-white' : darkMode ? 'bg-slate-800 text-slate-400' : 'bg-slate-200 text-slate-600'}`, children: _jsx(RefreshCw, { className: "h-5 w-5" }) }), _jsx("button", { onClick: () => setDarkMode(!darkMode), className: `p-2 rounded-lg transition-all ${darkMode ? 'bg-slate-800 text-yellow-400' : 'bg-slate-200 text-slate-600'}`, children: darkMode ? 'â˜€ï¸' : 'ðŸŒ™' })] })] }) }) }), _jsxs("main", { className: "max-w-7xl mx-auto px-6 py-8", children: [_jsxs("div", { className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8", children: [_jsx(MetricCard, { icon: _jsx(Palette, { className: "h-6 w-6" }), title: "Theme Builder", value: metrics.themeBuilder.themesGenerated, subtitle: `${metrics.themeBuilder.successRate}% success rate`, trend: "+12%", status: metrics.themeBuilder.status, darkMode: darkMode }), _jsx(MetricCard, { icon: _jsx(Shield, { className: "h-6 w-6" }), title: "Self-Healing", value: metrics.selfHealing.issuesFound, subtitle: `${metrics.selfHealing.autoFixed} auto-fixed`, trend: "+8%", status: metrics.selfHealing.status, darkMode: darkMode }), _jsx(MetricCard, { icon: _jsx(ShoppingCart, { className: "h-6 w-6" }), title: "Product Manager", value: metrics.productManager.totalProducts, subtitle: `${metrics.productManager.productsCreated} this week`, trend: "+5%", status: metrics.productManager.status, darkMode: darkMode }), _jsx(MetricCard, { icon: _jsx(TrendingUp, { className: "h-6 w-6" }), title: "System Health", value: `${metrics.system.uptime}%`, subtitle: `${metrics.system.apiLatency}ms latency`, trend: "Optimal", status: "healthy", darkMode: darkMode })] }), _jsx("div", { className: `${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg mb-8 overflow-hidden`, children: _jsx("div", { className: "flex flex-wrap", children: ['overview', 'themeBuilder', 'selfHealing', 'products', 'analytics'].map((tab) => (_jsx("button", { onClick: () => setActiveTab(tab), className: `flex-1 px-6 py-3 font-medium transition-all border-b-2 ${activeTab === tab
                                    ? 'border-purple-500 text-purple-400'
                                    : darkMode
                                        ? 'border-transparent text-slate-400 hover:text-slate-300'
                                        : 'border-transparent text-slate-600 hover:text-slate-900'}`, children: tab.charAt(0).toUpperCase() + tab.slice(1).replace(/([A-Z])/g, ' $1') }, tab))) }) }), activeTab === 'overview' && _jsx(OverviewTab, { metrics: metrics, darkMode: darkMode }), activeTab === 'themeBuilder' && _jsx(ThemeBuilderTab, { metrics: metrics, darkMode: darkMode }), activeTab === 'selfHealing' && _jsx(SelfHealingTab, { metrics: metrics, darkMode: darkMode }), activeTab === 'products' && _jsx(ProductsTab, { metrics: metrics, darkMode: darkMode }), activeTab === 'analytics' && _jsx(AnalyticsTab, { metrics: metrics, darkMode: darkMode })] })] }));
}
function MetricCard({ icon, title, value, subtitle, trend, status, darkMode }) {
    return (_jsxs("div", { className: `${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-6 hover:shadow-lg transition-all`, children: [_jsxs("div", { className: "flex justify-between items-start mb-4", children: [_jsx("div", { className: `p-2 rounded-lg ${status === 'healthy' ? 'bg-green-500 bg-opacity-20 text-green-400' : 'bg-red-500 bg-opacity-20 text-red-400'}`, children: icon }), _jsx("span", { className: "text-xs font-bold text-purple-400", children: trend })] }), _jsx("h3", { className: `text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-600'} mb-1`, children: title }), _jsx("p", { className: "text-3xl font-bold mb-2", children: value }), _jsx("p", { className: `text-xs ${darkMode ? 'text-slate-500' : 'text-slate-500'}`, children: subtitle })] }));
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
    return (_jsxs("div", { className: "space-y-8", children: [_jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-2 gap-8", children: [_jsx(ChartCard, { title: "Agent Performance", darkMode: darkMode, children: _jsx(ResponsiveContainer, { width: "100%", height: 300, children: _jsxs(BarChart, { data: performanceData, children: [_jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: darkMode ? '#334155' : '#e2e8f0' }), _jsx(XAxis, { stroke: darkMode ? '#94a3b8' : '#64748b' }), _jsx(YAxis, { stroke: darkMode ? '#94a3b8' : '#64748b' }), _jsx(Tooltip, { contentStyle: {
                                            backgroundColor: darkMode ? '#1e293b' : '#f8fafc',
                                            border: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`,
                                            borderRadius: '8px',
                                            color: darkMode ? '#e2e8f0' : '#1e293b'
                                        } }), _jsx(Bar, { dataKey: "value", fill: "#8b5cf6", radius: [8, 8, 0, 0] })] }) }) }), _jsx(ChartCard, { title: "24-Hour Activity", darkMode: darkMode, children: _jsx(ResponsiveContainer, { width: "100%", height: 300, children: _jsxs(AreaChart, { data: timeSeriesData, children: [_jsx("defs", { children: _jsxs("linearGradient", { id: "colorThemes", x1: "0", y1: "0", x2: "0", y2: "1", children: [_jsx("stop", { offset: "5%", stopColor: "#8b5cf6", stopOpacity: 0.8 }), _jsx("stop", { offset: "95%", stopColor: "#8b5cf6", stopOpacity: 0 })] }) }), _jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: darkMode ? '#334155' : '#e2e8f0' }), _jsx(XAxis, { stroke: darkMode ? '#94a3b8' : '#64748b' }), _jsx(YAxis, { stroke: darkMode ? '#94a3b8' : '#64748b' }), _jsx(Tooltip, { contentStyle: {
                                            backgroundColor: darkMode ? '#1e293b' : '#f8fafc',
                                            border: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`,
                                            borderRadius: '8px'
                                        } }), _jsx(Area, { type: "monotone", dataKey: "themes", stroke: "#8b5cf6", fillOpacity: 1, fill: "url(#colorThemes)" })] }) }) })] }), _jsxs("div", { className: `${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-6`, children: [_jsx("h3", { className: "text-lg font-bold mb-4", children: "Recent Activity" }), _jsxs("div", { className: "space-y-3", children: [_jsx(ActivityItem, { icon: _jsx(Palette, { className: "h-4 w-4" }), title: "Theme generated", desc: "Luxury Fashion theme for luxury_fashion_co", time: "2 min ago", darkMode: darkMode }), _jsx(ActivityItem, { icon: _jsx(CheckCircle, { className: "h-4 w-4" }), title: "Code scan completed", desc: "42 issues found, 28 auto-fixed", time: "5 min ago", darkMode: darkMode }), _jsx(ActivityItem, { icon: _jsx(ShoppingCart, { className: "h-4 w-4" }), title: "Bulk product import", desc: "250 products imported successfully", time: "15 min ago", darkMode: darkMode })] })] })] }));
}
function ThemeBuilderTab({ metrics, darkMode }) {
    return (_jsxs("div", { className: "space-y-8", children: [_jsxs("div", { className: "grid grid-cols-1 md:grid-cols-3 gap-4", children: [_jsx(StatBox, { label: "Themes Generated", value: metrics.themeBuilder.themesGenerated, darkMode: darkMode }), _jsx(StatBox, { label: "Avg Generation Time", value: `${metrics.themeBuilder.avgGenerationTime}s`, darkMode: darkMode }), _jsx(StatBox, { label: "Success Rate", value: `${metrics.themeBuilder.successRate}%`, darkMode: darkMode })] }), _jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-2 gap-8", children: [_jsx(ChartCard, { title: "Themes by Type", darkMode: darkMode, children: _jsx(ResponsiveContainer, { width: "100%", height: 300, children: _jsxs(PieChart, { children: [_jsxs(Pie, { data: [
                                            { name: 'Luxury Fashion', value: 45 },
                                            { name: 'Streetwear', value: 35 },
                                            { name: 'Minimalist', value: 25 },
                                            { name: 'Vintage', value: 15 },
                                            { name: 'Other', value: 15 }
                                        ], cx: "50%", cy: "50%", labelLine: false, label: ({ name, value }) => `${name}: ${value}`, outerRadius: 80, fill: "#8b5cf6", dataKey: "value", children: [_jsx(Cell, { fill: "#8b5cf6" }), _jsx(Cell, { fill: "#06b6d4" }), _jsx(Cell, { fill: "#ec4899" }), _jsx(Cell, { fill: "#f59e0b" }), _jsx(Cell, { fill: "#10b981" })] }), _jsx(Tooltip, {})] }) }) }), _jsx(ChartCard, { title: "Export Formats", darkMode: darkMode, children: _jsx("div", { className: "space-y-4", children: [
                                { format: 'ZIP Packages', count: 156, percentage: 65 },
                                { format: 'JSON Export', count: 52, percentage: 22 },
                                { format: 'Direct Upload', count: 35, percentage: 13 }
                            ].map((item) => (_jsxs("div", { children: [_jsxs("div", { className: "flex justify-between mb-1", children: [_jsx("span", { className: "text-sm font-medium", children: item.format }), _jsx("span", { className: "text-sm text-purple-400", children: item.count })] }), _jsx("div", { className: `${darkMode ? 'bg-slate-800' : 'bg-slate-200'} rounded-full h-2 overflow-hidden`, children: _jsx("div", { className: "bg-linear-to-r from-purple-500 to-blue-500 h-full", style: { width: `${item.percentage}%` } }) })] }, item.format))) }) })] }), _jsxs("div", { className: `${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-6`, children: [_jsx("h3", { className: "text-lg font-bold mb-4", children: "Generate New Theme" }), _jsxs("div", { className: "grid grid-cols-1 md:grid-cols-2 gap-4", children: [_jsx("input", { type: "text", placeholder: "Brand Name", className: `px-4 py-2 rounded-lg border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-300'}` }), _jsxs("select", { className: `px-4 py-2 rounded-lg border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-300'}`, children: [_jsx("option", { children: "Luxury Fashion" }), _jsx("option", { children: "Streetwear" }), _jsx("option", { children: "Minimalist" })] }), _jsxs("button", { className: "col-span-full bg-linear-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white px-6 py-2 rounded-lg font-bold transition-all flex items-center justify-center gap-2", children: [_jsx(Play, { className: "h-4 w-4" }), "Generate Theme"] })] })] })] }));
}
function SelfHealingTab({ metrics, darkMode }) {
    const severityData = [
        { severity: 'Critical', count: 23, percentage: 0.2 },
        { severity: 'High', count: 145, percentage: 1.1 },
        { severity: 'Medium', count: 892, percentage: 7.0 },
        { severity: 'Low', count: 11787, percentage: 91.7 }
    ];
    return (_jsxs("div", { className: "space-y-8", children: [_jsxs("div", { className: "grid grid-cols-1 md:grid-cols-4 gap-4", children: [_jsx(StatBox, { label: "Total Scans", value: metrics.selfHealing.totalScans, darkMode: darkMode }), _jsx(StatBox, { label: "Issues Found", value: metrics.selfHealing.issuesFound, darkMode: darkMode }), _jsx(StatBox, { label: "Auto-Fixed", value: metrics.selfHealing.autoFixed, darkMode: darkMode }), _jsx(StatBox, { label: "Avg Scan Time", value: `${metrics.selfHealing.scanAvgTime}s`, darkMode: darkMode })] }), _jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-2 gap-8", children: [_jsx(ChartCard, { title: "Issues by Severity", darkMode: darkMode, children: _jsx(ResponsiveContainer, { width: "100%", height: 300, children: _jsxs(BarChart, { data: severityData, children: [_jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: darkMode ? '#334155' : '#e2e8f0' }), _jsx(XAxis, { dataKey: "severity", stroke: darkMode ? '#94a3b8' : '#64748b' }), _jsx(YAxis, { stroke: darkMode ? '#94a3b8' : '#64748b' }), _jsx(Tooltip, { contentStyle: {
                                            backgroundColor: darkMode ? '#1e293b' : '#f8fafc',
                                            border: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`,
                                            borderRadius: '8px'
                                        } }), _jsx(Bar, { dataKey: "count", fill: "#ef4444", radius: [8, 8, 0, 0] })] }) }) }), _jsx(ChartCard, { title: "Remediation Statistics", darkMode: darkMode, children: _jsxs("div", { className: "space-y-6", children: [_jsxs("div", { children: [_jsxs("div", { className: "flex justify-between mb-2", children: [_jsx("span", { className: "text-sm font-medium", children: "Auto-Fix Success" }), _jsx("span", { className: "text-purple-400 font-bold", children: "74%" })] }), _jsx("div", { className: `${darkMode ? 'bg-slate-800' : 'bg-slate-200'} rounded-full h-3 overflow-hidden`, children: _jsx("div", { className: "bg-linear-to-r from-green-500 to-emerald-500 h-full", style: { width: '74%' } }) })] }), _jsxs("div", { children: [_jsxs("div", { className: "flex justify-between mb-2", children: [_jsx("span", { className: "text-sm font-medium", children: "Critical Issues Resolved" }), _jsx("span", { className: "text-blue-400 font-bold", children: "96%" })] }), _jsx("div", { className: `${darkMode ? 'bg-slate-800' : 'bg-slate-200'} rounded-full h-3 overflow-hidden`, children: _jsx("div", { className: "bg-linear-to-r from-blue-500 to-cyan-500 h-full", style: { width: '96%' } }) })] })] }) })] }), _jsxs("div", { className: `${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-6`, children: [_jsx("h3", { className: "text-lg font-bold mb-4", children: "Trigger Code Scan" }), _jsxs("div", { className: "flex gap-4", children: [_jsx("input", { type: "text", placeholder: "Directory path (e.g., ./src)", className: `flex-1 px-4 py-2 rounded-lg border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-300'}` }), _jsxs("button", { className: "bg-linear-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white px-6 py-2 rounded-lg font-bold transition-all flex items-center gap-2", children: [_jsx(Zap, { className: "h-4 w-4" }), "Scan"] })] })] })] }));
}
function ProductsTab({ metrics, darkMode }) {
    return (_jsxs("div", { className: "space-y-8", children: [_jsxs("div", { className: "grid grid-cols-1 md:grid-cols-4 gap-4", children: [_jsx(StatBox, { label: "Total Products", value: metrics.productManager.totalProducts, darkMode: darkMode }), _jsx(StatBox, { label: "Created This Week", value: metrics.productManager.productsCreated, darkMode: darkMode }), _jsx(StatBox, { label: "Inventory Updates", value: metrics.productManager.inventoryUpdates, darkMode: darkMode }), _jsx(StatBox, { label: "Avg Response", value: `${metrics.productManager.avgResponse}ms`, darkMode: darkMode })] }), _jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-2 gap-8", children: [_jsx(ChartCard, { title: "Product Status Distribution", darkMode: darkMode, children: _jsx(ResponsiveContainer, { width: "100%", height: 300, children: _jsxs(PieChart, { children: [_jsxs(Pie, { data: [
                                            { name: 'Published', value: 1050 },
                                            { name: 'Draft', value: 150 },
                                            { name: 'Pending', value: 35 },
                                            { name: 'Archived', value: 15 }
                                        ], cx: "50%", cy: "50%", outerRadius: 80, fill: "#8b5cf6", dataKey: "value", children: [_jsx(Cell, { fill: "#10b981" }), _jsx(Cell, { fill: "#3b82f6" }), _jsx(Cell, { fill: "#f59e0b" }), _jsx(Cell, { fill: "#6b7280" })] }), _jsx(Tooltip, {})] }) }) }), _jsx(ChartCard, { title: "Top Categories", darkMode: darkMode, children: _jsx("div", { className: "space-y-3", children: [
                                { category: 'Jackets', count: 256, growth: '+12%' },
                                { category: 'Dresses', count: 198, growth: '+8%' },
                                { category: 'Accessories', count: 187, growth: '+5%' },
                                { category: 'Footwear', count: 156, growth: '+3%' }
                            ].map((item) => (_jsxs("div", { className: "flex justify-between items-center", children: [_jsx("span", { className: "font-medium", children: item.category }), _jsxs("div", { className: "flex items-center gap-3", children: [_jsx("span", { className: "text-slate-400", children: item.count }), _jsx("span", { className: "text-green-400 text-sm", children: item.growth })] })] }, item.category))) }) })] }), _jsxs("div", { className: `${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-6`, children: [_jsx("h3", { className: "text-lg font-bold mb-4", children: "Create New Product" }), _jsxs("div", { className: "grid grid-cols-1 md:grid-cols-3 gap-4", children: [_jsx("input", { type: "text", placeholder: "Product Name", className: `px-4 py-2 rounded-lg border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-300'}` }), _jsx("input", { type: "text", placeholder: "SKU", className: `px-4 py-2 rounded-lg border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-300'}` }), _jsx("input", { type: "number", placeholder: "Price", className: `px-4 py-2 rounded-lg border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-300'}` }), _jsxs("button", { className: "col-span-full bg-linear-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white px-6 py-2 rounded-lg font-bold transition-all flex items-center justify-center gap-2", children: [_jsx(ShoppingCart, { className: "h-4 w-4" }), "Create Product"] })] })] })] }));
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
    return (_jsxs("div", { className: "space-y-8", children: [_jsx(ChartCard, { title: "System Health Analysis", darkMode: darkMode, children: _jsx(ResponsiveContainer, { width: "100%", height: 400, children: _jsxs(RadarChart, { data: radarData, children: [_jsx(PolarGrid, { stroke: darkMode ? '#334155' : '#e2e8f0' }), _jsx(PolarAngleAxis, { dataKey: "subject", stroke: darkMode ? '#94a3b8' : '#64748b' }), _jsx(PolarRadiusAxis, { stroke: darkMode ? '#94a3b8' : '#64748b' }), _jsx(Radar, { name: "Health Score", dataKey: "A", stroke: "#8b5cf6", fill: "#8b5cf6", fillOpacity: 0.6 }), _jsx(Tooltip, { contentStyle: {
                                    backgroundColor: darkMode ? '#1e293b' : '#f8fafc',
                                    border: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`,
                                    borderRadius: '8px'
                                } })] }) }) }), _jsxs("div", { className: "grid grid-cols-1 md:grid-cols-2 gap-8", children: [_jsx(ChartCard, { title: "CPU Usage", darkMode: darkMode, children: _jsxs("div", { className: "space-y-4", children: [_jsx("div", { className: "text-center py-8", children: _jsxs("div", { className: "relative inline-flex items-center justify-center w-32 h-32", children: [_jsx("div", { className: "absolute w-full h-full rounded-full border-8 border-slate-700 border-t-purple-500 animate-spin" }), _jsxs("div", { className: "text-3xl font-bold", children: [metrics.system.cpuUsage, "%"] })] }) }), _jsx("p", { className: "text-center text-sm text-slate-400", children: "Current usage within optimal range" })] }) }), _jsx(ChartCard, { title: "Memory Usage", darkMode: darkMode, children: _jsxs("div", { className: "space-y-4", children: [_jsx("div", { className: "text-center py-8", children: _jsxs("div", { className: "relative inline-flex items-center justify-center w-32 h-32", children: [_jsx("div", { className: "absolute w-full h-full rounded-full border-8 border-slate-700 border-t-blue-500 animate-spin" }), _jsxs("div", { className: "text-3xl font-bold", children: [metrics.system.memoryUsage, "%"] })] }) }), _jsx("p", { className: "text-center text-sm text-slate-400", children: "Memory allocation optimal" })] }) })] }), _jsx(ChartCard, { title: "Monthly Performance Summary", darkMode: darkMode, children: _jsx(ResponsiveContainer, { width: "100%", height: 300, children: _jsxs(LineChart, { data: [
                            { month: 'Jan', themes: 120, scans: 340, products: 420 },
                            { month: 'Feb', themes: 150, scans: 380, products: 520 },
                            { month: 'Mar', themes: 180, scans: 420, products: 620 },
                            { month: 'Apr', themes: 220, scans: 480, products: 750 }
                        ], children: [_jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: darkMode ? '#334155' : '#e2e8f0' }), _jsx(XAxis, { stroke: darkMode ? '#94a3b8' : '#64748b' }), _jsx(YAxis, { stroke: darkMode ? '#94a3b8' : '#64748b' }), _jsx(Tooltip, { contentStyle: {
                                    backgroundColor: darkMode ? '#1e293b' : '#f8fafc',
                                    border: `1px solid ${darkMode ? '#334155' : '#e2e8f0'}`,
                                    borderRadius: '8px'
                                } }), _jsx(Legend, {}), _jsx(Line, { type: "monotone", dataKey: "themes", stroke: "#8b5cf6", strokeWidth: 2, dot: { fill: '#8b5cf6' } }), _jsx(Line, { type: "monotone", dataKey: "scans", stroke: "#06b6d4", strokeWidth: 2, dot: { fill: '#06b6d4' } }), _jsx(Line, { type: "monotone", dataKey: "products", stroke: "#10b981", strokeWidth: 2, dot: { fill: '#10b981' } })] }) }) })] }));
}
function ChartCard({ title, children, darkMode }) {
    return (_jsxs("div", { className: `${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-6`, children: [_jsx("h3", { className: "text-lg font-bold mb-4", children: title }), children] }));
}
function StatBox({ label, value, darkMode }) {
    return (_jsxs("div", { className: `${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} border rounded-lg p-4`, children: [_jsx("p", { className: `text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-600'}`, children: label }), _jsx("p", { className: "text-2xl font-bold mt-1", children: value })] }));
}
function ActivityItem({ icon, title, desc, time, darkMode }) {
    return (_jsxs("div", { className: "flex gap-3 pb-3 border-b border-opacity-10 border-white", children: [_jsx("div", { className: "text-purple-400 mt-1", children: icon }), _jsxs("div", { className: "flex-1", children: [_jsx("p", { className: "font-medium", children: title }), _jsx("p", { className: `text-sm ${darkMode ? 'text-slate-400' : 'text-slate-600'}`, children: desc })] }), _jsx("span", { className: `text-xs ${darkMode ? 'text-slate-500' : 'text-slate-500'}`, children: time })] }));
}
//# sourceMappingURL=DevSkyyDashboard.js.map
