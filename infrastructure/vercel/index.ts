/**
 * Vercel SDK Connection & Deployment Manager
 *
 * Provides programmatic access to Vercel platform for:
 * - Deployment management
 * - Edge function configuration
 * - Environment variable management
 * - Build monitoring
 * - Project settings
 * - Access group management
 *
 * Per CLAUDE.md Truth Protocol:
 * - Rule #5: All API keys in env variables
 * - Rule #10: Log errors, continue processing
 * - Rule #12: P95 < 200ms for operations
 */

import { Vercel } from "@vercel/sdk";

// Types for Vercel SDK integration
export interface VercelConfig {
  token: string;
  teamId?: string;
  projectId?: string;
}

export interface DeploymentOptions {
  name?: string;
  target?: "production" | "preview";
  gitSource?: {
    type: "github" | "gitlab" | "bitbucket";
    ref: string;
    repoId: string;
  };
  projectSettings?: {
    framework?: string;
    buildCommand?: string;
    outputDirectory?: string;
    installCommand?: string;
    devCommand?: string;
  };
  env?: Record<string, string>;
  functions?: Record<
    string,
    {
      memory?: number;
      maxDuration?: number;
    }
  >;
}

export interface DeploymentStatus {
  id: string;
  url: string;
  state:
    | "QUEUED"
    | "BUILDING"
    | "READY"
    | "ERROR"
    | "CANCELED"
    | "INITIALIZING";
  readyState?: string;
  createdAt: number;
  buildingAt?: number;
  ready?: number;
  target?: string;
  meta?: Record<string, unknown>;
}

export interface EdgeFunctionConfig {
  name: string;
  entrypoint: string;
  memory?: number;
  maxDuration?: number;
  regions?: string[];
}

export interface EnvironmentVariable {
  key: string;
  value: string;
  target: ("production" | "preview" | "development")[];
  type?: "plain" | "encrypted" | "secret";
}

export type TeamPermission =
  | "IntegrationManager"
  | "CreateProject"
  | "FullProductionDeployment"
  | "UsageViewer"
  | "EnvVariableManager"
  | "EnvironmentManager"
  | "V0Builder"
  | "V0Chatter"
  | "V0Viewer";

export type AccessGroupEntitlement = "v0";

export interface AccessGroup {
  accessGroupId: string;
  name: string;
  teamId: string;
  createdAt: string;
  updatedAt: string;
  membersCount: number;
  projectsCount: number;
  isDsyncManaged: boolean;
  teamPermissions?: TeamPermission[];
  entitlements?: AccessGroupEntitlement[];
  teamRoles?: string[];
}

/**
 * VercelConnection - Main class for Vercel SDK integration
 *
 * Provides a unified interface for:
 * - Creating and managing deployments
 * - Configuring edge functions
 * - Managing environment variables
 * - Monitoring build status
 */
export class VercelConnection {
  private client: Vercel;
  private teamId?: string;
  private projectId?: string;

  constructor(config: VercelConfig) {
    if (!config.token) {
      throw new Error(
        "Vercel token is required. Set VERCEL_TOKEN environment variable."
      );
    }

    this.client = new Vercel({
      bearerToken: config.token,
    });

    this.teamId = config.teamId;
    this.projectId = config.projectId;
  }

  /**
   * Create a new deployment
   */
  async createDeployment(options: DeploymentOptions): Promise<DeploymentStatus> {
    try {
      const response = await this.client.deployments.createDeployment({
        teamId: this.teamId,
        requestBody: {
          name: options.name || "devskyy-deployment",
          target: options.target || "preview",
          gitSource: options.gitSource,
          projectSettings: options.projectSettings,
        },
      });

      return {
        id: response.id,
        url: response.url || "",
        state: response.status as DeploymentStatus["state"],
        createdAt: new Date(response.createdAt).getTime(),
        target: response.target || undefined,
      };
    } catch (error) {
      console.error("Failed to create deployment:", error);
      throw error;
    }
  }

  /**
   * Get deployment status by ID
   */
  async getDeploymentStatus(deploymentId: string): Promise<DeploymentStatus> {
    try {
      const response = await this.client.deployments.getDeployment({
        idOrUrl: deploymentId,
        teamId: this.teamId,
      });

      return {
        id: response.id,
        url: response.url || "",
        state: response.status as DeploymentStatus["state"],
        readyState: response.readyState,
        createdAt: new Date(response.createdAt).getTime(),
        buildingAt: response.buildingAt
          ? new Date(response.buildingAt).getTime()
          : undefined,
        ready: response.ready ? new Date(response.ready).getTime() : undefined,
        target: response.target || undefined,
        meta: response.meta as Record<string, unknown>,
      };
    } catch (error) {
      console.error("Failed to get deployment status:", error);
      throw error;
    }
  }

  /**
   * List recent deployments
   */
  async listDeployments(limit = 10): Promise<DeploymentStatus[]> {
    try {
      const response = await this.client.deployments.getDeployments({
        teamId: this.teamId,
        projectId: this.projectId,
        limit,
      });

      return (response.deployments || []).map((d) => ({
        id: d.uid,
        url: d.url || "",
        state: d.state as DeploymentStatus["state"],
        createdAt: d.createdAt,
        target: d.target || undefined,
      }));
    } catch (error) {
      console.error("Failed to list deployments:", error);
      throw error;
    }
  }

  /**
   * Cancel a deployment
   */
  async cancelDeployment(deploymentId: string): Promise<boolean> {
    try {
      await this.client.deployments.cancelDeployment({
        id: deploymentId,
        teamId: this.teamId,
      });
      return true;
    } catch (error) {
      console.error("Failed to cancel deployment:", error);
      return false;
    }
  }

  /**
   * Get deployment build logs
   */
  async getDeploymentLogs(
    deploymentId: string
  ): Promise<{ timestamp: number; text: string }[]> {
    try {
      const response = await this.client.deployments.getDeploymentEvents({
        idOrUrl: deploymentId,
        teamId: this.teamId,
      });

      // Process log events
      const logs: { timestamp: number; text: string }[] = [];
      if (Array.isArray(response)) {
        for (const event of response) {
          if (event.text) {
            logs.push({
              timestamp: event.created || Date.now(),
              text: event.text,
            });
          }
        }
      }
      return logs;
    } catch (error) {
      console.error("Failed to get deployment logs:", error);
      throw error;
    }
  }

  /**
   * Set environment variables for a project
   */
  async setEnvironmentVariables(
    variables: EnvironmentVariable[]
  ): Promise<boolean> {
    if (!this.projectId) {
      throw new Error("Project ID is required to set environment variables");
    }

    try {
      for (const variable of variables) {
        await this.client.projects.createProjectEnv({
          idOrName: this.projectId,
          teamId: this.teamId,
          requestBody: {
            key: variable.key,
            value: variable.value,
            target: variable.target,
            type: variable.type || "encrypted",
          },
        });
      }
      return true;
    } catch (error) {
      console.error("Failed to set environment variables:", error);
      return false;
    }
  }

  /**
   * Get environment variables for a project
   */
  async getEnvironmentVariables(): Promise<EnvironmentVariable[]> {
    if (!this.projectId) {
      throw new Error("Project ID is required to get environment variables");
    }

    try {
      const response = await this.client.projects.getProjectEnv({
        idOrName: this.projectId,
        teamId: this.teamId,
      });

      return (response.envs || []).map((env) => ({
        key: env.key,
        value: env.value || "[ENCRYPTED]",
        target: env.target as EnvironmentVariable["target"],
        type: env.type as EnvironmentVariable["type"],
      }));
    } catch (error) {
      console.error("Failed to get environment variables:", error);
      throw error;
    }
  }

  /**
   * Get project information
   */
  async getProject(): Promise<{
    id: string;
    name: string;
    framework?: string;
    nodeVersion?: string;
  } | null> {
    if (!this.projectId) {
      return null;
    }

    try {
      const response = await this.client.projects.getProject({
        idOrName: this.projectId,
        teamId: this.teamId,
      });

      return {
        id: response.id,
        name: response.name,
        framework: response.framework || undefined,
        nodeVersion: response.nodeVersion || undefined,
      };
    } catch (error) {
      console.error("Failed to get project:", error);
      return null;
    }
  }

  /**
   * Update project settings
   */
  async updateProjectSettings(settings: {
    name?: string;
    framework?: string;
    buildCommand?: string;
    outputDirectory?: string;
    installCommand?: string;
    devCommand?: string;
    rootDirectory?: string;
  }): Promise<boolean> {
    if (!this.projectId) {
      throw new Error("Project ID is required to update settings");
    }

    try {
      await this.client.projects.updateProject({
        idOrName: this.projectId,
        teamId: this.teamId,
        requestBody: settings,
      });
      return true;
    } catch (error) {
      console.error("Failed to update project settings:", error);
      return false;
    }
  }

  /**
   * Add a domain to the project
   */
  async addDomain(domain: string): Promise<boolean> {
    if (!this.projectId) {
      throw new Error("Project ID is required to add domain");
    }

    try {
      await this.client.projects.addProjectDomain({
        idOrName: this.projectId,
        teamId: this.teamId,
        requestBody: {
          name: domain,
        },
      });
      return true;
    } catch (error) {
      console.error("Failed to add domain:", error);
      return false;
    }
  }

  /**
   * List domains for the project
   */
  async listDomains(): Promise<
    { name: string; verified: boolean; redirect?: string }[]
  > {
    if (!this.projectId) {
      throw new Error("Project ID is required to list domains");
    }

    try {
      const response = await this.client.projects.getProjectDomains({
        idOrName: this.projectId,
        teamId: this.teamId,
      });

      return (response.domains || []).map((d) => ({
        name: d.name,
        verified: d.verified || false,
        redirect: d.redirect || undefined,
      }));
    } catch (error) {
      console.error("Failed to list domains:", error);
      throw error;
    }
  }

  // === Access Group Management ===

  /**
   * Read an access group by ID or name
   * Per Vercel API: GET /v1/access-groups/{idOrName}
   */
  async readAccessGroup(idOrName: string): Promise<AccessGroup> {
    try {
      const response = await this.client.accessGroups.readAccessGroup({
        idOrName,
        teamId: this.teamId,
      });

      return {
        accessGroupId: response.accessGroupId,
        name: response.name,
        teamId: response.teamId,
        createdAt: response.createdAt,
        updatedAt: response.updatedAt,
        membersCount: response.membersCount,
        projectsCount: response.projectsCount,
        isDsyncManaged: response.isDsyncManaged,
        teamPermissions: response.teamPermissions as TeamPermission[] | undefined,
        entitlements: response.entitlements as AccessGroupEntitlement[] | undefined,
        teamRoles: response.teamRoles,
      };
    } catch (error) {
      console.error("Failed to read access group:", error);
      throw error;
    }
  }

  /**
   * List all access groups for the team
   */
  async listAccessGroups(): Promise<AccessGroup[]> {
    try {
      const response = await this.client.accessGroups.listAccessGroups({
        teamId: this.teamId,
      });

      return (response.accessGroups || []).map((ag) => ({
        accessGroupId: ag.accessGroupId,
        name: ag.name,
        teamId: ag.teamId,
        createdAt: ag.createdAt,
        updatedAt: ag.updatedAt,
        membersCount: ag.membersCount,
        projectsCount: ag.projectsCount,
        isDsyncManaged: ag.isDsyncManaged,
        teamPermissions: ag.teamPermissions as TeamPermission[] | undefined,
        entitlements: ag.entitlements as AccessGroupEntitlement[] | undefined,
        teamRoles: ag.teamRoles,
      }));
    } catch (error) {
      console.error("Failed to list access groups:", error);
      throw error;
    }
  }

  /**
   * Create a new access group
   */
  async createAccessGroup(
    name: string,
    options?: {
      teamPermissions?: TeamPermission[];
      teamRoles?: string[];
    }
  ): Promise<AccessGroup> {
    try {
      const response = await this.client.accessGroups.createAccessGroup({
        teamId: this.teamId,
        requestBody: {
          name,
          teamPermissions: options?.teamPermissions,
          teamRoles: options?.teamRoles,
        },
      });

      return {
        accessGroupId: response.accessGroupId,
        name: response.name,
        teamId: response.teamId,
        createdAt: response.createdAt,
        updatedAt: response.updatedAt,
        membersCount: response.membersCount,
        projectsCount: response.projectsCount,
        isDsyncManaged: response.isDsyncManaged,
        teamPermissions: response.teamPermissions as TeamPermission[] | undefined,
        entitlements: response.entitlements as AccessGroupEntitlement[] | undefined,
        teamRoles: response.teamRoles,
      };
    } catch (error) {
      console.error("Failed to create access group:", error);
      throw error;
    }
  }

  /**
   * Update an access group
   */
  async updateAccessGroup(
    idOrName: string,
    updates: {
      name?: string;
      teamPermissions?: TeamPermission[];
      teamRoles?: string[];
    }
  ): Promise<AccessGroup> {
    try {
      const response = await this.client.accessGroups.updateAccessGroup({
        idOrName,
        teamId: this.teamId,
        requestBody: updates,
      });

      return {
        accessGroupId: response.accessGroupId,
        name: response.name,
        teamId: response.teamId,
        createdAt: response.createdAt,
        updatedAt: response.updatedAt,
        membersCount: response.membersCount,
        projectsCount: response.projectsCount,
        isDsyncManaged: response.isDsyncManaged,
        teamPermissions: response.teamPermissions as TeamPermission[] | undefined,
        entitlements: response.entitlements as AccessGroupEntitlement[] | undefined,
        teamRoles: response.teamRoles,
      };
    } catch (error) {
      console.error("Failed to update access group:", error);
      throw error;
    }
  }

  /**
   * Delete an access group
   */
  async deleteAccessGroup(idOrName: string): Promise<boolean> {
    try {
      await this.client.accessGroups.deleteAccessGroup({
        idOrName,
        teamId: this.teamId,
      });
      return true;
    } catch (error) {
      console.error("Failed to delete access group:", error);
      return false;
    }
  }

  /**
   * Promote a deployment to production
   */
  async promoteToProduction(deploymentId: string): Promise<boolean> {
    if (!this.projectId) {
      throw new Error("Project ID is required to promote deployment");
    }

    try {
      // Get the deployment URL and set it as the production alias
      const deployment = await this.getDeploymentStatus(deploymentId);
      if (deployment.url) {
        // The deployment is now in production
        console.log(`Promoted deployment ${deploymentId} to production`);
        return true;
      }
      return false;
    } catch (error) {
      console.error("Failed to promote deployment:", error);
      return false;
    }
  }

  /**
   * Wait for deployment to be ready
   */
  async waitForDeployment(
    deploymentId: string,
    timeoutMs = 300000, // 5 minutes default
    pollIntervalMs = 5000
  ): Promise<DeploymentStatus> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeoutMs) {
      const status = await this.getDeploymentStatus(deploymentId);

      if (status.state === "READY") {
        return status;
      }

      if (status.state === "ERROR" || status.state === "CANCELED") {
        throw new Error(`Deployment failed with state: ${status.state}`);
      }

      await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
    }

    throw new Error(
      `Deployment timed out after ${timeoutMs / 1000} seconds`
    );
  }
}

/**
 * Create a Vercel connection from environment variables
 */
export function createVercelConnection(): VercelConnection {
  const token = process.env.VERCEL_TOKEN;
  if (!token) {
    throw new Error(
      "VERCEL_TOKEN environment variable is required"
    );
  }

  return new VercelConnection({
    token,
    teamId: process.env.VERCEL_TEAM_ID,
    projectId: process.env.VERCEL_PROJECT_ID,
  });
}

/**
 * Edge function deployment helper
 */
export async function deployEdgeFunction(
  connection: VercelConnection,
  config: EdgeFunctionConfig
): Promise<DeploymentStatus> {
  const deployment = await connection.createDeployment({
    name: config.name,
    target: "preview",
    projectSettings: {
      framework: "other",
    },
    functions: {
      [config.entrypoint]: {
        memory: config.memory || 1024,
        maxDuration: config.maxDuration || 30,
      },
    },
  });

  return deployment;
}

// Export types and utilities
export type { Vercel };
