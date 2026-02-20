'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { getVercelDeploymentManager } from '@/lib/vercel/deployment-manager'
import {
  Rocket,
  Activity,
  Settings,
  Globe,
  GitBranch,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  ExternalLink,
  Play,
  Trash2
} from 'lucide-react'

export default function VercelAdminPage() {
  const [vercelManager, setVercelManager] = useState<any>(null)
  const [deployments, setDeployments] = useState<any[]>([])
  const [projects, setProjects] = useState<any[]>([])
  const [envVars, setEnvVars] = useState<any[]>([])
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const manager = getVercelDeploymentManager()
    setVercelManager(manager)

    if (manager) {
      loadData(manager)
    }
  }, [])

  const loadData = async (manager: any) => {
    setLoading(true)
    try {
      const [deploymentsData, projectsData, userData] = await Promise.all([
        manager.listDeployments({ limit: 10 }),
        manager.listProjects({ limit: 10 }),
        manager.getUser()
      ])

      setDeployments(deploymentsData.deployments || [])
      setProjects(projectsData.projects || [])
      setUser(userData)
    } catch (error) {
      console.error('Failed to load Vercel data:', error)
    }
    setLoading(false)
  }

  const loadEnvVars = async (projectId: string) => {
    if (!vercelManager) return
    try {
      const envData = await vercelManager.listEnvVariables(projectId)
      setEnvVars(envData.envs || [])
    } catch (error) {
      console.error('Failed to load env vars:', error)
    }
  }

  const promoteDeployment = async (deploymentId: string) => {
    if (!vercelManager) return
    try {
      setLoading(true)
      await vercelManager.promoteToProduction(deploymentId)
      loadData(vercelManager)
    } catch (error) {
      console.error('Failed to promote deployment:', error)
    }
    setLoading(false)
  }

  const getStateColor = (state: string) => {
    switch (state) {
      case 'READY':
        return 'text-green-400'
      case 'ERROR':
        return 'text-red-400'
      case 'BUILDING':
        return 'text-blue-400'
      case 'QUEUED':
        return 'text-yellow-400'
      default:
        return 'text-gray-400'
    }
  }

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'READY':
        return <CheckCircle2 className="h-4 w-4 text-green-400" />
      case 'ERROR':
        return <XCircle className="h-4 w-4 text-red-400" />
      case 'BUILDING':
        return <Loader2 className="h-4 w-4 text-blue-400 animate-spin" />
      case 'QUEUED':
        return <Clock className="h-4 w-4 text-yellow-400" />
      default:
        return <Activity className="h-4 w-4 text-gray-400" />
    }
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-4xl luxury-text-gradient">
            Vercel Deployment Manager
          </h1>
          <p className="text-gray-400 mt-2">
            Manage deployments, projects, and environment variables
          </p>
        </div>
        {user && (
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="font-semibold">{user.name || user.username}</p>
              <p className="text-sm text-gray-400">{user.email}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-rose-500 to-pink-500 flex items-center justify-center font-bold">
              {user.name?.charAt(0) || 'U'}
            </div>
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Rocket className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{deployments.length}</p>
                <p className="text-sm text-gray-400">Recent Deployments</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <GitBranch className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{projects.length}</p>
                <p className="text-sm text-gray-400">Active Projects</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Settings className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{envVars.length}</p>
                <p className="text-sm text-gray-400">Env Variables</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="deployments" className="space-y-6">
        <TabsList className="grid grid-cols-3 w-full">
          <TabsTrigger value="deployments">
            <Rocket className="mr-2 h-4 w-4" />
            Deployments
          </TabsTrigger>
          <TabsTrigger value="projects">
            <GitBranch className="mr-2 h-4 w-4" />
            Projects
          </TabsTrigger>
          <TabsTrigger value="env-vars">
            <Settings className="mr-2 h-4 w-4" />
            Environment Variables
          </TabsTrigger>
        </TabsList>

        {/* Deployments */}
        <TabsContent value="deployments">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Recent Deployments</CardTitle>
                  <CardDescription>View and manage your deployments</CardDescription>
                </div>
                <Button
                  onClick={() => vercelManager && loadData(vercelManager)}
                  disabled={loading}
                  size="sm"
                >
                  {loading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Activity className="mr-2 h-4 w-4" />
                  )}
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {deployments.length === 0 ? (
                <p className="text-gray-500">No deployments found</p>
              ) : (
                <div className="space-y-3">
                  {deployments.map((deployment) => (
                    <div
                      key={deployment.uid}
                      className="flex items-center justify-between p-4 rounded-lg bg-gray-900/50 border border-gray-800"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        {getStateIcon(deployment.state)}
                        <div>
                          <p className="font-semibold">{deployment.name}</p>
                          <div className="flex gap-3 mt-1">
                            <Badge variant="outline" className="text-xs">
                              {deployment.target || 'preview'}
                            </Badge>
                            <span className="text-xs text-gray-400">
                              {new Date(deployment.created).toLocaleString()}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <a
                          href={`https://${deployment.url}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <Button size="sm" variant="outline">
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                        </a>
                        {deployment.target === 'preview' && deployment.state === 'READY' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => promoteDeployment(deployment.uid)}
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Projects */}
        <TabsContent value="projects">
          <Card>
            <CardHeader>
              <CardTitle>Projects</CardTitle>
              <CardDescription>Your Vercel projects</CardDescription>
            </CardHeader>
            <CardContent>
              {projects.length === 0 ? (
                <p className="text-gray-500">No projects found</p>
              ) : (
                <div className="space-y-3">
                  {projects.map((project) => (
                    <div
                      key={project.id}
                      className="p-4 rounded-lg bg-gray-900/50 border border-gray-800 hover:border-rose-500/30 cursor-pointer"
                      onClick={() => loadEnvVars(project.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-semibold">{project.name}</p>
                          <div className="flex gap-2 mt-1">
                            <Badge variant="outline" className="text-xs">
                              {project.framework || 'Next.js'}
                            </Badge>
                            <span className="text-xs text-gray-400">
                              Updated {new Date(project.updatedAt).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        <Button size="sm" variant="outline">
                          <Settings className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Environment Variables */}
        <TabsContent value="env-vars">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Environment Variables</CardTitle>
                  <CardDescription>
                    {envVars.length > 0
                      ? `Showing ${envVars.length} variables`
                      : 'Select a project to view environment variables'}
                  </CardDescription>
                </div>
                {envVars.length > 0 && (
                  <Button size="sm">
                    <Settings className="mr-2 h-4 w-4" />
                    Add Variable
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {envVars.length === 0 ? (
                <p className="text-gray-500">Click on a project to load its environment variables</p>
              ) : (
                <div className="space-y-2">
                  {envVars.map((env) => (
                    <div
                      key={env.id}
                      className="flex items-center justify-between p-3 rounded bg-gray-900/50 border border-gray-800"
                    >
                      <div className="flex-1">
                        <p className="font-medium font-mono text-sm">{env.key}</p>
                        <div className="flex gap-2 mt-1">
                          {env.target.map((t: string) => (
                            <Badge key={t} variant="outline" className="text-xs">
                              {t}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="ghost">
                          <Settings className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="ghost">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
