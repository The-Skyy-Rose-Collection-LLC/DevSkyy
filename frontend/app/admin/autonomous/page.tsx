'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { selfHealingService } from '@/lib/autonomous/self-healing-service'
import { CheckCircle2, XCircle, AlertCircle, Activity } from 'lucide-react'

export default function AutonomousAgentsPage() {
  const [healthStatus, setHealthStatus] = useState<any[]>([])
  const [circuitBreakers, setCircuitBreakers] = useState<any[]>([])

  useEffect(() => {
    // Update health status every 5 seconds
    const interval = setInterval(() => {
      setHealthStatus(selfHealingService.getHealthStatus())
      setCircuitBreakers(selfHealingService.getCircuitBreakerStatus())
    }, 5000)

    // Initial load
    setHealthStatus(selfHealingService.getHealthStatus())
    setCircuitBreakers(selfHealingService.getCircuitBreakerStatus())

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="container mx-auto py-8 space-y-8">
      <h1 className="font-display text-4xl luxury-text-gradient">
        Autonomous Agents
      </h1>

      <p className="text-gray-400">
        Monitor and control autonomous operations across the DevSkyy platform.
      </p>

      {/* Health Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-green-400" />
            <CardTitle>System Health</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {healthStatus.length === 0 ? (
            <p className="text-gray-500">No health checks recorded yet</p>
          ) : (
            <div className="space-y-3">
              {healthStatus.map((check, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 rounded-lg bg-gray-900/50 border border-gray-800"
                >
                  <div className="flex items-center gap-3">
                    {check.healthy ? (
                      <CheckCircle2 className="h-5 w-5 text-green-400" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-400" />
                    )}
                    <div>
                      <p className="font-semibold">{check.service}</p>
                      <p className="text-sm text-gray-400">
                        Last check: {new Date(check.lastCheck).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge
                      variant={check.healthy ? 'default' : 'destructive'}
                      className={check.healthy ? 'bg-green-500/20 text-green-400' : ''}
                    >
                      {check.healthy ? 'Healthy' : `Failed (${check.consecutiveFailures}x)`}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Circuit Breakers */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-yellow-400" />
            <CardTitle>Circuit Breakers</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {circuitBreakers.length === 0 ? (
            <p className="text-gray-500">No circuit breakers active</p>
          ) : (
            <div className="space-y-3">
              {circuitBreakers.map((breaker, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 rounded-lg bg-gray-900/50 border border-gray-800"
                >
                  <div className="flex items-center gap-3">
                    <AlertCircle
                      className={`h-5 w-5 ${
                        breaker.open ? 'text-red-400' : 'text-green-400'
                      }`}
                    />
                    <div>
                      <p className="font-semibold">{breaker.service}</p>
                      <p className="text-sm text-gray-400">
                        Failures: {breaker.failures}
                      </p>
                    </div>
                  </div>
                  <Badge
                    variant={breaker.open ? 'destructive' : 'default'}
                    className={!breaker.open ? 'bg-green-500/20 text-green-400' : ''}
                  >
                    {breaker.open ? 'OPEN' : 'CLOSED'}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* WordPress Auto-Sync */}
      <Card>
        <CardHeader>
          <CardTitle>WordPress Operations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold mb-2">Auto-Sync</h3>
            <p className="text-sm text-gray-400">
              Automatically sync Round Table results to WordPress as published posts
            </p>
            <Badge className="mt-2 bg-green-500/20 text-green-400">
              Active
            </Badge>
          </div>

          <div>
            <h3 className="font-semibold mb-2">Menu Management</h3>
            <p className="text-sm text-gray-400">
              Autonomous agent can manage WordPress menus and navigation
            </p>
            <Badge className="mt-2 bg-blue-500/20 text-blue-400">
              Enabled
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Content Generation Agent */}
      <Card>
        <CardHeader>
          <CardTitle>Content Generation Agent</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-400">
            Uses LLM Round Table outputs to generate product descriptions, scene descriptions, and marketing content
          </p>
          <Badge className="mt-3 bg-purple-500/20 text-purple-400">
            Ready
          </Badge>
        </CardContent>
      </Card>

      {/* 3D Scene Builder Agent */}
      <Card>
        <CardHeader>
          <CardTitle>3D Scene Builder Agent</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-400">
            Builds 3D environments from LLM scene descriptions for luxury product visualization
          </p>
          <Badge className="mt-3 bg-cyan-500/20 text-cyan-400">
            Ready
          </Badge>
        </CardContent>
      </Card>
    </div>
  )
}
