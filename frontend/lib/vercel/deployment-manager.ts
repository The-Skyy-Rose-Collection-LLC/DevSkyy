/**
 * Vercel Deployment Manager
 * Programmatic deployment, monitoring, and analytics via Vercel API
 */

interface VercelConfig {
  token: string
  teamId?: string
  projectId?: string
}

interface Deployment {
  uid: string
  name: string
  url: string
  created: number
  state: 'BUILDING' | 'ERROR' | 'INITIALIZING' | 'QUEUED' | 'READY' | 'CANCELED'
  type: 'LAMBDAS'
  creator: {
    uid: string
    username: string
  }
  meta: Record<string, string>
  target?: 'production' | 'preview'
  aliasAssigned?: boolean
  aliasError?: any
}

interface DeploymentEvent {
  type: string
  created: number
  payload: {
    message: string
    info?: any
  }
}

interface Project {
  id: string
  name: string
  accountId: string
  createdAt: number
  updatedAt: number
  framework: string
  devCommand: string
  buildCommand: string
  installCommand: string
  outputDirectory: string
  publicSource: boolean
  rootDirectory: string
  env: Array<{
    key: string
    value: string
    target: string[]
  }>
}

interface EnvironmentVariable {
  key: string
  value: string
  target: ('production' | 'preview' | 'development')[]
  type?: 'secret' | 'encrypted' | 'plain'
  id?: string
}

export class VercelDeploymentManager {
  private config: VercelConfig
  private baseUrl = 'https://api.vercel.com'

  constructor(config: VercelConfig) {
    this.config = config
  }

  // ==========================================================================
  // DEPLOYMENTS
  // ==========================================================================

  /**
   * Create a new deployment
   */
  async createDeployment(options: {
    name: string
    files: Array<{ file: string; data: string }>
    target?: 'production' | 'preview'
    projectSettings?: {
      framework?: string
      buildCommand?: string
      outputDirectory?: string
      installCommand?: string
      devCommand?: string
    }
  }): Promise<Deployment> {
    const body: any = {
      name: options.name,
      files: options.files,
      target: options.target || 'preview',
    }

    if (this.config.projectId) {
      body.projectId = this.config.projectId
    }

    if (options.projectSettings) {
      body.projectSettings = options.projectSettings
    }

    return this.request('POST', '/v13/deployments', body)
  }

  /**
   * Get deployment by ID
   */
  async getDeployment(deploymentId: string): Promise<Deployment> {
    return this.request('GET', `/v13/deployments/${deploymentId}`)
  }

  /**
   * List deployments
   */
  async listDeployments(options?: {
    limit?: number
    since?: number
    until?: number
    state?: string
    target?: 'production' | 'preview'
  }): Promise<{ deployments: Deployment[] }> {
    const query = this.buildQuery(options)
    return this.request('GET', `/v6/deployments${query}`)
  }

  /**
   * Cancel deployment
   */
  async cancelDeployment(deploymentId: string): Promise<{ state: string }> {
    return this.request('PATCH', `/v12/deployments/${deploymentId}/cancel`)
  }

  /**
   * Delete deployment
   */
  async deleteDeployment(deploymentId: string): Promise<{ state: string }> {
    return this.request('DELETE', `/v13/deployments/${deploymentId}`)
  }

  /**
   * Get deployment events (build logs)
   */
  async getDeploymentEvents(deploymentId: string): Promise<DeploymentEvent[]> {
    const response = await this.request('GET', `/v3/deployments/${deploymentId}/events`)
    return response
  }

  /**
   * Get deployment files
   */
  async getDeploymentFiles(deploymentId: string): Promise<any[]> {
    return this.request('GET', `/v6/deployments/${deploymentId}/files`)
  }

  // ==========================================================================
  // PROJECTS
  // ==========================================================================

  /**
   * Create project
   */
  async createProject(options: {
    name: string
    framework?: string
    buildCommand?: string
    outputDirectory?: string
    installCommand?: string
    devCommand?: string
    rootDirectory?: string
    environmentVariables?: EnvironmentVariable[]
  }): Promise<Project> {
    const body: any = {
      name: options.name,
    }

    if (options.framework) body.framework = options.framework
    if (options.buildCommand) body.buildCommand = options.buildCommand
    if (options.outputDirectory) body.outputDirectory = options.outputDirectory
    if (options.installCommand) body.installCommand = options.installCommand
    if (options.devCommand) body.devCommand = options.devCommand
    if (options.rootDirectory) body.rootDirectory = options.rootDirectory
    if (options.environmentVariables) body.environmentVariables = options.environmentVariables

    const query = this.config.teamId ? `?teamId=${this.config.teamId}` : ''
    return this.request('POST', `/v10/projects${query}`, body)
  }

  /**
   * Get project
   */
  async getProject(projectIdOrName: string): Promise<Project> {
    const query = this.config.teamId ? `?teamId=${this.config.teamId}` : ''
    return this.request('GET', `/v9/projects/${projectIdOrName}${query}`)
  }

  /**
   * List projects
   */
  async listProjects(options?: {
    limit?: number
    search?: string
  }): Promise<{ projects: Project[] }> {
    const params: any = { ...options }
    if (this.config.teamId) params.teamId = this.config.teamId

    const query = this.buildQuery(params)
    return this.request('GET', `/v9/projects${query}`)
  }

  /**
   * Update project
   */
  async updateProject(projectIdOrName: string, updates: Partial<Project>): Promise<Project> {
    const query = this.config.teamId ? `?teamId=${this.config.teamId}` : ''
    return this.request('PATCH', `/v9/projects/${projectIdOrName}${query}`, updates)
  }

  /**
   * Delete project
   */
  async deleteProject(projectIdOrName: string): Promise<void> {
    const query = this.config.teamId ? `?teamId=${this.config.teamId}` : ''
    return this.request('DELETE', `/v9/projects/${projectIdOrName}${query}`)
  }

  // ==========================================================================
  // ENVIRONMENT VARIABLES
  // ==========================================================================

  /**
   * Create environment variable
   */
  async createEnvVariable(
    projectIdOrName: string,
    variable: EnvironmentVariable
  ): Promise<EnvironmentVariable> {
    const query = this.config.teamId ? `?teamId=${this.config.teamId}` : ''
    return this.request('POST', `/v10/projects/${projectIdOrName}/env${query}`, variable)
  }

  /**
   * List environment variables
   */
  async listEnvVariables(projectIdOrName: string): Promise<{ envs: EnvironmentVariable[] }> {
    const query = this.config.teamId ? `?teamId=${this.config.teamId}` : ''
    return this.request('GET', `/v9/projects/${projectIdOrName}/env${query}`)
  }

  /**
   * Update environment variable
   */
  async updateEnvVariable(
    projectIdOrName: string,
    envId: string,
    updates: Partial<EnvironmentVariable>
  ): Promise<EnvironmentVariable> {
    const query = this.config.teamId ? `?teamId=${this.config.teamId}` : ''
    return this.request('PATCH', `/v9/projects/${projectIdOrName}/env/${envId}${query}`, updates)
  }

  /**
   * Delete environment variable
   */
  async deleteEnvVariable(projectIdOrName: string, envId: string): Promise<void> {
    const query = this.config.teamId ? `?teamId=${this.config.teamId}` : ''
    return this.request('DELETE', `/v9/projects/${projectIdOrName}/env/${envId}${query}`)
  }

  /**
   * Bulk upload environment variables from .env file
   */
  async syncEnvVariables(
    projectIdOrName: string,
    envVars: Record<string, string>,
    target: ('production' | 'preview' | 'development')[] = ['production', 'preview', 'development']
  ): Promise<{ created: number; updated: number; errors: string[] }> {
    const result = {
      created: 0,
      updated: 0,
      errors: [] as string[]
    }

    try {
      // Get existing env vars
      const existing = await this.listEnvVariables(projectIdOrName)
      const existingMap = new Map(
        existing.envs.map(env => [env.key, env])
      )

      // Create or update each variable
      for (const [key, value] of Object.entries(envVars)) {
        try {
          const existingVar = existingMap.get(key)

          if (existingVar) {
            // Update existing
            await this.updateEnvVariable(projectIdOrName, existingVar.id!, {
              value,
              target
            })
            result.updated++
          } else {
            // Create new
            await this.createEnvVariable(projectIdOrName, {
              key,
              value,
              target,
              type: 'encrypted'
            })
            result.created++
          }
        } catch (error) {
          result.errors.push(`Failed to sync ${key}: ${error}`)
        }
      }

      return result
    } catch (error) {
      result.errors.push(`Failed to sync env variables: ${error}`)
      return result
    }
  }

  // ==========================================================================
  // DOMAINS
  // ==========================================================================

  /**
   * Add domain to project
   */
  async addDomain(projectIdOrName: string, domain: string): Promise<any> {
    const query = this.config.teamId ? `?teamId=${this.config.teamId}` : ''
    return this.request('POST', `/v10/projects/${projectIdOrName}/domains${query}`, {
      name: domain
    })
  }

  /**
   * List project domains
   */
  async listDomains(projectIdOrName: string): Promise<{ domains: any[] }> {
    const query = this.config.teamId ? `?teamId=${this.config.teamId}` : ''
    return this.request('GET', `/v9/projects/${projectIdOrName}/domains${query}`)
  }

  /**
   * Remove domain from project
   */
  async removeDomain(projectIdOrName: string, domain: string): Promise<void> {
    const query = this.config.teamId ? `?teamId=${this.config.teamId}` : ''
    return this.request('DELETE', `/v9/projects/${projectIdOrName}/domains/${domain}${query}`)
  }

  // ==========================================================================
  // ALIASES
  // ==========================================================================

  /**
   * Create alias for deployment
   */
  async createAlias(deploymentId: string, alias: string): Promise<any> {
    return this.request('POST', `/v2/deployments/${deploymentId}/aliases`, {
      alias
    })
  }

  /**
   * List aliases for deployment
   */
  async listAliases(deploymentId: string): Promise<{ aliases: string[] }> {
    return this.request('GET', `/v2/deployments/${deploymentId}/aliases`)
  }

  // ==========================================================================
  // LOGS
  // ==========================================================================

  /**
   * Get deployment logs
   */
  async getDeploymentLogs(deploymentId: string, options?: {
    limit?: number
    since?: number
    until?: number
    direction?: 'forward' | 'backward'
  }): Promise<any> {
    const query = this.buildQuery(options)
    return this.request('GET', `/v2/deployments/${deploymentId}/events${query}`)
  }

  // ==========================================================================
  // MONITORING & ANALYTICS
  // ==========================================================================

  /**
   * Get deployment checks (health checks)
   */
  async getDeploymentChecks(deploymentId: string): Promise<any> {
    return this.request('GET', `/v1/deployments/${deploymentId}/checks`)
  }

  /**
   * Get project analytics
   */
  async getProjectAnalytics(projectIdOrName: string, options?: {
    from?: number
    to?: number
    limit?: number
  }): Promise<any> {
    const query = this.buildQuery(options)
    return this.request('GET', `/v1/projects/${projectIdOrName}/analytics${query}`)
  }

  // ==========================================================================
  // UTILITIES
  // ==========================================================================

  /**
   * Deploy from Git repository
   */
  async deployFromGit(options: {
    projectName: string
    gitSource: {
      type: 'github' | 'gitlab' | 'bitbucket'
      repo: string
      ref?: string
    }
    target?: 'production' | 'preview'
  }): Promise<Deployment> {
    const body: any = {
      name: options.projectName,
      gitSource: options.gitSource,
      target: options.target || 'preview'
    }

    if (this.config.projectId) {
      body.projectId = this.config.projectId
    }

    return this.request('POST', '/v13/deployments', body)
  }

  /**
   * Promote preview deployment to production
   */
  async promoteToProduction(deploymentId: string): Promise<Deployment> {
    return this.request('POST', `/v13/deployments/${deploymentId}/promote`)
  }

  /**
   * Redeploy (create new deployment from existing one)
   */
  async redeploy(deploymentId: string, target?: 'production' | 'preview'): Promise<Deployment> {
    const deployment = await this.getDeployment(deploymentId)

    return this.request('POST', '/v13/deployments', {
      name: deployment.name,
      target: target || deployment.target,
      deploymentId
    })
  }

  /**
   * Get team info
   */
  async getTeam(): Promise<any> {
    if (!this.config.teamId) {
      throw new Error('Team ID not configured')
    }
    return this.request('GET', `/v2/teams/${this.config.teamId}`)
  }

  /**
   * Get user info
   */
  async getUser(): Promise<any> {
    return this.request('GET', '/v2/user')
  }

  // ==========================================================================
  // PRIVATE METHODS
  // ==========================================================================

  private async request(method: string, endpoint: string, body?: any): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`

    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.token}`,
      },
    }

    if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      options.body = JSON.stringify(body)
    }

    const response = await fetch(url, options)

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }))
      throw new Error(`Vercel API error: ${response.status} ${error.message || error.error?.message}`)
    }

    return response.json()
  }

  private buildQuery(params?: Record<string, any>): string {
    if (!params || Object.keys(params).length === 0) return ''

    const queryParams = new URLSearchParams()

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => queryParams.append(key, String(v)))
        } else {
          queryParams.append(key, String(value))
        }
      }
    })

    return `?${queryParams.toString()}`
  }
}

/**
 * Get Vercel deployment manager instance
 */
export function getVercelDeploymentManager(): VercelDeploymentManager | null {
  const token = process.env.VERCEL_TOKEN
  const teamId = process.env.VERCEL_TEAM_ID
  const projectId = process.env.VERCEL_PROJECT_ID

  if (!token) {
    console.warn('VERCEL_TOKEN not configured')
    return null
  }

  return new VercelDeploymentManager({
    token,
    teamId,
    projectId
  })
}
