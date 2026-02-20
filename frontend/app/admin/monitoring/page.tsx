'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  TrendingUp,
  TrendingDown,
  Zap,
  Database,
  Globe,
  Server,
  RefreshCw,
} from 'lucide-react';

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  uptime: number;
  lastCheck: Date;
  responseTime: number;
}

interface CircuitBreakerStatus {
  service: string;
  state: 'closed' | 'open' | 'half-open';
  failures: number;
  lastFailure: Date | null;
}

interface ActivityLog {
  id: string;
  timestamp: Date;
  type: 'success' | 'warning' | 'error';
  service: string;
  message: string;
}

export default function MonitoringPage() {
  const [services, setServices] = useState<ServiceHealth[]>([
    {
      name: 'WordPress API',
      status: 'healthy',
      uptime: 99.98,
      lastCheck: new Date(),
      responseTime: 145,
    },
    {
      name: 'Vercel API',
      status: 'healthy',
      uptime: 100,
      lastCheck: new Date(),
      responseTime: 89,
    },
    {
      name: 'Round Table',
      status: 'healthy',
      uptime: 99.95,
      lastCheck: new Date(),
      responseTime: 234,
    },
    {
      name: 'Database',
      status: 'healthy',
      uptime: 100,
      lastCheck: new Date(),
      responseTime: 12,
    },
  ]);

  const [circuitBreakers, setCircuitBreakers] = useState<CircuitBreakerStatus[]>([
    {
      service: 'WordPress Sync',
      state: 'closed',
      failures: 0,
      lastFailure: null,
    },
    {
      service: 'Vercel Deployment',
      state: 'closed',
      failures: 0,
      lastFailure: null,
    },
    {
      service: 'Round Table Competition',
      state: 'closed',
      failures: 0,
      lastFailure: null,
    },
  ]);

  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([
    {
      id: '1',
      timestamp: new Date(Date.now() - 120000),
      type: 'success',
      service: 'WordPress',
      message: 'Post published successfully (ID: 1234)',
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 300000),
      type: 'success',
      service: 'Vercel',
      message: 'Deployment completed: https://devskyy.vercel.app',
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 480000),
      type: 'success',
      service: 'Round Table',
      message: 'Competition completed - Winner: Anthropic Claude',
    },
  ]);

  const [isRefreshing, setIsRefreshing] = useState(false);

  const refreshMetrics = async () => {
    setIsRefreshing(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Update last check times
    setServices((prev) =>
      prev.map((service) => ({
        ...service,
        lastCheck: new Date(),
        responseTime: Math.floor(Math.random() * 300) + 10,
      }))
    );

    setIsRefreshing(false);
  };

  const getStatusIcon = (status: ServiceHealth['status']) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="h-5 w-5 text-green-400" />;
      case 'degraded':
        return <AlertCircle className="h-5 w-5 text-yellow-400" />;
      case 'down':
        return <AlertCircle className="h-5 w-5 text-red-400" />;
    }
  };

  const getStatusBadge = (status: ServiceHealth['status']) => {
    const variants = {
      healthy: 'bg-green-500/10 text-green-400 border-green-500/30',
      degraded: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
      down: 'bg-red-500/10 text-red-400 border-red-500/30',
    };

    return (
      <Badge className={`${variants[status]} border`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const getCircuitBreakerBadge = (state: CircuitBreakerStatus['state']) => {
    const variants = {
      closed: 'bg-green-500/10 text-green-400 border-green-500/30',
      'half-open': 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
      open: 'bg-red-500/10 text-red-400 border-red-500/30',
    };

    return (
      <Badge className={`${variants[state]} border`}>
        {state === 'closed' ? 'Closed (Normal)' : state === 'half-open' ? 'Half-Open (Testing)' : 'Open (Failed)'}
      </Badge>
    );
  };

  const getActivityIcon = (type: ActivityLog['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-400" />;
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-yellow-400" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-400" />;
    }
  };

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
  };

  useEffect(() => {
    // Auto-refresh every 30 seconds
    const interval = setInterval(refreshMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="container mx-auto py-8 space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-display text-4xl luxury-text-gradient mb-2">System Monitoring</h1>
            <p className="text-gray-400">Real-time health and performance metrics</p>
          </div>
          <Button
            onClick={refreshMetrics}
            disabled={isRefreshing}
            variant="outline"
            className="border-gray-700"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>

        {/* Service Health Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {services.map((service, index) => (
            <motion.div
              key={service.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <Card className="bg-gray-900 border-gray-800">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(service.status)}
                      <h3 className="font-semibold">{service.name}</h3>
                    </div>
                    {getStatusBadge(service.status)}
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Uptime</span>
                      <span className="font-semibold">{service.uptime}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Response Time</span>
                      <span className="font-semibold">{service.responseTime}ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Last Check</span>
                      <span className="text-xs text-gray-500">
                        {formatTimestamp(service.lastCheck)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Circuit Breaker Status */}
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-rose-400" />
                Circuit Breaker Status
              </CardTitle>
              <CardDescription>Self-healing service protection</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {circuitBreakers.map((breaker) => (
                  <div
                    key={breaker.service}
                    className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg"
                  >
                    <div>
                      <p className="font-semibold mb-1">{breaker.service}</p>
                      <p className="text-sm text-gray-400">
                        {breaker.failures} failures
                        {breaker.lastFailure && ` · Last: ${formatTimestamp(breaker.lastFailure)}`}
                      </p>
                    </div>
                    {getCircuitBreakerBadge(breaker.state)}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* System Metrics */}
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-rose-400" />
                System Metrics
              </CardTitle>
              <CardDescription>Performance and resource usage</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <TrendingUp className="h-5 w-5 text-green-400" />
                    <div>
                      <p className="font-semibold">API Requests/min</p>
                      <p className="text-sm text-gray-400">Last 5 minutes</p>
                    </div>
                  </div>
                  <span className="text-2xl font-bold">142</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="h-5 w-5 text-green-400" />
                    <div>
                      <p className="font-semibold">Success Rate</p>
                      <p className="text-sm text-gray-400">Last hour</p>
                    </div>
                  </div>
                  <span className="text-2xl font-bold">99.8%</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Clock className="h-5 w-5 text-blue-400" />
                    <div>
                      <p className="font-semibold">Avg Response Time</p>
                      <p className="text-sm text-gray-400">Last hour</p>
                    </div>
                  </div>
                  <span className="text-2xl font-bold">156ms</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Activity Log */}
        <Card className="bg-gray-900 border-gray-800 mt-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-rose-400" />
              Recent Activity
            </CardTitle>
            <CardDescription>Latest system events and operations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {activityLogs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-start gap-3 p-4 bg-gray-800/50 rounded-lg hover:bg-gray-800 transition-colors"
                >
                  {getActivityIcon(log.type)}
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <p className="font-semibold">{log.service}</p>
                      <span className="text-xs text-gray-500">
                        {formatTimestamp(log.timestamp)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400">{log.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
