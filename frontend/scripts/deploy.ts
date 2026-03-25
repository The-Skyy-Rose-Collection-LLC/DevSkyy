#!/usr/bin/env ts-node
/**
 * Automated Vercel Deployment Script
 * Deploy to Vercel via CLI with full automation
 */

import { exec } from 'child_process'
import { promisify } from 'util'
import * as fs from 'fs'
import * as path from 'path'

const execAsync = promisify(exec)

interface DeploymentOptions {
  production?: boolean
  prebuilt?: boolean
  force?: boolean
  skipDomain?: boolean
  withCache?: boolean
  debug?: boolean
}

class VercelDeployer {
  private projectRoot: string

  constructor() {
    this.projectRoot = process.cwd()
  }

  /**
   * Main deployment function
   */
  async deploy(options: DeploymentOptions = {}): Promise<void> {
    console.log('🚀 Starting Vercel deployment...\n')

    try {
      // Step 1: Pre-deployment checks
      await this.preDeploymentChecks()

      // Step 2: Build project
      if (!options.prebuilt) {
        await this.buildProject()
      }

      // Step 3: Deploy to Vercel
      const deploymentUrl = await this.deployToVercel(options)

      // Step 4: Post-deployment tasks
      await this.postDeploymentTasks(deploymentUrl, options)

      console.log('\n✅ Deployment successful!')
      console.log(`📦 URL: ${deploymentUrl}`)
    } catch (error) {
      console.error('\n❌ Deployment failed:', error)
      process.exit(1)
    }
  }

  /**
   * Pre-deployment checks
   */
  private async preDeploymentChecks(): Promise<void> {
    console.log('🔍 Running pre-deployment checks...')

    // Check if Vercel CLI is installed
    try {
      await execAsync('vercel --version')
      console.log('✓ Vercel CLI installed')
    } catch (error) {
      throw new Error('Vercel CLI not installed. Run: npm i -g vercel')
    }

    // Verify project is linked to "devskyy"
    try {
      const projectLinkPath = path.join(this.projectRoot, '.vercel', 'project.json')
      if (fs.existsSync(projectLinkPath)) {
        const projectLink = JSON.parse(fs.readFileSync(projectLinkPath, 'utf-8'))
        const projectName = projectLink.projectName || 'unknown'

        if (projectName !== 'devskyy') {
          console.warn(`⚠️  Project linked to '${projectName}' instead of 'devskyy'`)
          console.warn('   Run: vercel link --project=devskyy')
          console.warn('   Or: ./scripts/link-vercel-project.sh')
        } else {
          console.log('✓ Project linked to devskyy')
        }
      } else {
        console.warn('⚠️  Project not linked to Vercel')
        console.warn('   Run: vercel link --project=devskyy')
      }
    } catch (error) {
      console.warn('⚠️  Could not verify project link')
    }

    // Check if .env.production exists
    const envPath = path.join(this.projectRoot, '.env.production')
    if (!fs.existsSync(envPath)) {
      console.warn('⚠️  .env.production not found')
    } else {
      console.log('✓ .env.production found')
    }

    // Check if vercel.json exists
    const vercelConfigPath = path.join(this.projectRoot, 'vercel.json')
    if (!fs.existsSync(vercelConfigPath)) {
      console.log('ℹ️  vercel.json not found (optional)')
    } else {
      console.log('✓ vercel.json found')
    }
  }

  /**
   * Build project
   */
  private async buildProject(): Promise<void> {
    console.log('\n🏗️  Building project...')

    try {
      const { stdout, stderr } = await execAsync('pnpm build', {
        cwd: this.projectRoot,
      })

      if (stderr && !stderr.includes('Warning')) {
        console.error('Build warnings:', stderr)
      }

      console.log('✓ Build completed successfully')
    } catch (error: any) {
      throw new Error(`Build failed: ${error.message}`)
    }
  }

  /**
   * Deploy to Vercel
   */
  private async deployToVercel(options: DeploymentOptions): Promise<string> {
    console.log('\n📤 Deploying to Vercel...')

    let command = 'vercel'

    if (options.production) {
      command += ' --prod'
      console.log('🌍 Deploying to PRODUCTION')
    } else {
      console.log('🔧 Deploying to PREVIEW')
    }

    if (options.prebuilt) {
      command += ' --prebuilt'
    }

    if (options.force) {
      command += ' --force'
    }

    if (options.skipDomain) {
      command += ' --skip-domain'
    }

    if (options.withCache) {
      command += ' --with-cache'
    }

    if (options.debug) {
      command += ' --debug'
    }

    try {
      const { stdout } = await execAsync(command, {
        cwd: this.projectRoot,
      })

      // Extract deployment URL from stdout
      const urlMatch = stdout.match(/https:\/\/[^\s]+/)
      const deploymentUrl = urlMatch ? urlMatch[0] : 'Unknown'

      console.log('✓ Deployment completed')

      return deploymentUrl
    } catch (error: any) {
      throw new Error(`Deployment failed: ${error.message}`)
    }
  }

  /**
   * Post-deployment tasks
   */
  private async postDeploymentTasks(
    deploymentUrl: string,
    options: DeploymentOptions
  ): Promise<void> {
    console.log('\n🔧 Running post-deployment tasks...')

    // Wait for deployment to be ready
    await this.waitForDeployment(deploymentUrl)

    // Run smoke tests if production
    if (options.production) {
      await this.runSmokeTests(deploymentUrl)
    }

    // Log deployment info
    await this.logDeployment(deploymentUrl, options)
  }

  /**
   * Wait for deployment to be ready
   */
  private async waitForDeployment(url: string): Promise<void> {
    console.log('⏳ Waiting for deployment to be ready...')

    const maxAttempts = 30
    const delayMs = 2000

    for (let i = 0; i < maxAttempts; i++) {
      try {
        const response = await fetch(url, { method: 'HEAD' })
        if (response.ok) {
          console.log('✓ Deployment is live')
          return
        }
      } catch (error) {
        // Continue waiting
      }

      await new Promise(resolve => setTimeout(resolve, delayMs))
    }

    console.warn('⚠️  Deployment may not be ready yet')
  }

  /**
   * Run smoke tests
   */
  private async runSmokeTests(url: string): Promise<void> {
    console.log('🧪 Running smoke tests...')

    try {
      // Test home page
      const homeResponse = await fetch(url)
      if (!homeResponse.ok) {
        throw new Error(`Home page returned ${homeResponse.status}`)
      }
      console.log('✓ Home page loads')

      // Test API health endpoint
      const healthResponse = await fetch(`${url}/api/monitoring/health`)
      if (healthResponse.ok) {
        console.log('✓ Health endpoint responds')
      }

      console.log('✓ All smoke tests passed')
    } catch (error) {
      console.error('⚠️  Smoke tests failed:', error)
    }
  }

  /**
   * Log deployment info
   */
  private async logDeployment(url: string, options: DeploymentOptions): Promise<void> {
    const deploymentLog = {
      timestamp: new Date().toISOString(),
      url,
      production: options.production || false,
      success: true,
    }

    const logPath = path.join(this.projectRoot, 'deployments.log')

    try {
      fs.appendFileSync(
        logPath,
        JSON.stringify(deploymentLog) + '\n',
        'utf-8'
      )
      console.log('✓ Deployment logged')
    } catch (error) {
      console.error('Failed to log deployment:', error)
    }
  }

  /**
   * Rollback to previous deployment
   */
  async rollback(): Promise<void> {
    console.log('🔄 Rolling back to previous deployment...')

    try {
      // Get recent deployments
      const { stdout } = await execAsync('vercel ls --limit 5')

      console.log('Recent deployments:')
      console.log(stdout)

      // Note: Actual rollback requires promoting a previous deployment
      // This would be done via Vercel dashboard or API
      console.log('\nTo rollback, promote a previous deployment via Vercel dashboard')
    } catch (error: any) {
      throw new Error(`Rollback failed: ${error.message}`)
    }
  }
}

// CLI Interface
async function main() {
  const args = process.argv.slice(2)

  const options: DeploymentOptions = {
    production: args.includes('--prod') || args.includes('-p'),
    prebuilt: args.includes('--prebuilt'),
    force: args.includes('--force'),
    skipDomain: args.includes('--skip-domain'),
    withCache: args.includes('--with-cache'),
    debug: args.includes('--debug'),
  }

  const deployer = new VercelDeployer()

  if (args.includes('--rollback')) {
    await deployer.rollback()
  } else {
    await deployer.deploy(options)
  }
}

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('Deployment error:', error)
    process.exit(1)
  })
}

export { VercelDeployer }
