/**
 * Page Object Models
 * ==================
 *
 * Reusable page objects for E2E tests following the Page Object Model pattern.
 * These abstract UI interactions for better test maintainability.
 */

import type { Page, Locator } from '@playwright/test';

// =============================================================================
// LOGIN PAGE
// =============================================================================

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly rememberMeCheckbox: Locator;
  readonly forgotPasswordLink: Locator;

  constructor(page: Page) {
    this.page = page;

    this.usernameInput = page.locator(
      '[data-testid="username"], input[name="username"], input[type="email"], #username, #email'
    ).first();

    this.passwordInput = page.locator(
      '[data-testid="password"], input[name="password"], input[type="password"], #password'
    ).first();

    this.submitButton = page.locator(
      '[data-testid="login-submit"], button[type="submit"], button:has-text("Sign in"), button:has-text("Login"), button:has-text("Log in")'
    ).first();

    this.errorMessage = page.locator(
      '[data-testid="error-message"], [role="alert"], .error-message, .error, .toast-error'
    ).first();

    this.rememberMeCheckbox = page.locator(
      '[data-testid="remember-me"], input[name="remember"], #remember-me'
    ).first();

    this.forgotPasswordLink = page.locator(
      'a:has-text("Forgot"), a:has-text("Reset"), [data-testid="forgot-password"]'
    ).first();
  }

  async goto() {
    await this.page.goto('/login');
    await this.page.waitForLoadState('networkidle');
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async loginWithRemember(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.rememberMeCheckbox.check();
    await this.submitButton.click();
  }

  async waitForRedirect(urlPattern: string | RegExp = /\/(admin|dashboard|home)?$/) {
    await this.page.waitForURL(urlPattern, { timeout: 15000 });
  }

  async getErrorText(): Promise<string | null> {
    try {
      return await this.errorMessage.textContent({ timeout: 3000 });
    } catch {
      return null;
    }
  }
}

// =============================================================================
// DASHBOARD PAGE
// =============================================================================

export class DashboardPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly statsCards: Locator;
  readonly productCount: Locator;
  readonly orderCount: Locator;
  readonly syncStatus: Locator;
  readonly agentsList: Locator;
  readonly userMenu: Locator;
  readonly logoutButton: Locator;
  readonly sidebar: Locator;
  readonly mainContent: Locator;

  constructor(page: Page) {
    this.page = page;

    this.heading = page.locator('h1, [data-testid="dashboard-title"]').first();

    this.statsCards = page.locator(
      '[data-testid="stat-card"], .stat-card, [class*="stats"], [class*="metric"], [class*="card"]'
    );

    this.productCount = page.locator(
      '[data-testid="product-count"], :has-text("Products") >> nth=0'
    );

    this.orderCount = page.locator(
      '[data-testid="order-count"], :has-text("Orders") >> nth=0'
    );

    this.syncStatus = page.locator(
      '[data-testid="sync-status"], :has-text("Sync")'
    ).first();

    this.agentsList = page.locator(
      '[data-testid="agents-list"], [data-testid="agent-card"], .agent-card, .agent-list'
    );

    this.userMenu = page.locator(
      '[data-testid="user-menu"], [aria-label="User menu"], button:has([data-testid="avatar"]), .user-menu'
    ).first();

    this.logoutButton = page.locator(
      '[data-testid="logout"], button:has-text("Logout"), button:has-text("Log out"), button:has-text("Sign out"), a:has-text("Logout")'
    ).first();

    this.sidebar = page.locator(
      '[data-testid="sidebar"], aside, nav[role="navigation"], .sidebar'
    ).first();

    this.mainContent = page.locator(
      '[data-testid="main-content"], main, .main-content, #main'
    ).first();
  }

  async goto() {
    await this.page.goto('/admin');
    await this.page.waitForLoadState('networkidle');
  }

  async gotoHome() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
  }

  async openUserMenu() {
    await this.userMenu.click();
  }

  async logout() {
    try {
      await this.openUserMenu();
      await this.logoutButton.click();
    } catch {
      // Direct logout button without menu
      await this.logoutButton.click();
    }
  }

  async getStatsCount(): Promise<number> {
    return await this.statsCards.count();
  }

  async navigateTo(linkText: string) {
    await this.sidebar.locator(`a:has-text("${linkText}")`).first().click();
    await this.page.waitForLoadState('networkidle');
  }
}

// =============================================================================
// AGENTS PAGE
// =============================================================================

export class AgentsPage {
  readonly page: Page;
  readonly agentCards: Locator;
  readonly searchInput: Locator;
  readonly filterDropdown: Locator;

  constructor(page: Page) {
    this.page = page;

    this.agentCards = page.locator(
      '[data-testid="agent-card"], .agent-card, [class*="agent"]'
    );

    this.searchInput = page.locator(
      '[data-testid="agent-search"], input[placeholder*="Search"], input[name="search"]'
    ).first();

    this.filterDropdown = page.locator(
      '[data-testid="agent-filter"], select, [role="combobox"]'
    ).first();
  }

  async goto() {
    await this.page.goto('/agents');
    await this.page.waitForLoadState('networkidle');
  }

  async getAgentCount(): Promise<number> {
    return await this.agentCards.count();
  }

  async selectAgent(name: string) {
    await this.agentCards.locator(`:has-text("${name}")`).first().click();
    await this.page.waitForLoadState('networkidle');
  }

  async searchAgents(query: string) {
    await this.searchInput.fill(query);
    await this.page.waitForLoadState('networkidle');
  }
}

// =============================================================================
// AGENT DETAIL PAGE
// =============================================================================

export class AgentDetailPage {
  readonly page: Page;
  readonly agentName: Locator;
  readonly agentStatus: Locator;
  readonly startButton: Locator;
  readonly stopButton: Locator;
  readonly executeButton: Locator;
  readonly taskInput: Locator;
  readonly toolsList: Locator;
  readonly statsSection: Locator;

  constructor(page: Page) {
    this.page = page;

    this.agentName = page.locator(
      '[data-testid="agent-name"], h1, h2'
    ).first();

    this.agentStatus = page.locator(
      '[data-testid="agent-status"], .status, [class*="status"]'
    ).first();

    this.startButton = page.locator(
      '[data-testid="start-agent"], button:has-text("Start"), button:has-text("Run")'
    ).first();

    this.stopButton = page.locator(
      '[data-testid="stop-agent"], button:has-text("Stop")'
    ).first();

    this.executeButton = page.locator(
      '[data-testid="execute-task"], button:has-text("Execute"), button:has-text("Submit")'
    ).first();

    this.taskInput = page.locator(
      '[data-testid="task-input"], textarea, input[name="task"]'
    ).first();

    this.toolsList = page.locator(
      '[data-testid="tools-list"], .tools, [class*="tool"]'
    );

    this.statsSection = page.locator(
      '[data-testid="agent-stats"], .stats, [class*="statistics"]'
    ).first();
  }

  async goto(agentType: string) {
    await this.page.goto(`/agents/${agentType}`);
    await this.page.waitForLoadState('networkidle');
  }

  async executeTask(task: string) {
    await this.taskInput.fill(task);
    await this.executeButton.click();
  }

  async startAgent() {
    await this.startButton.click();
  }

  async stopAgent() {
    await this.stopButton.click();
  }

  async getStatus(): Promise<string | null> {
    return await this.agentStatus.textContent();
  }
}

// =============================================================================
// PRODUCTS PAGE
// =============================================================================

export class ProductsPage {
  readonly page: Page;
  readonly productTable: Locator;
  readonly productRows: Locator;
  readonly searchInput: Locator;
  readonly createButton: Locator;
  readonly syncButton: Locator;
  readonly pagination: Locator;

  constructor(page: Page) {
    this.page = page;

    this.productTable = page.locator(
      '[data-testid="products-table"], table, .products-list'
    ).first();

    this.productRows = page.locator(
      '[data-testid="product-row"], tbody tr, .product-item'
    );

    this.searchInput = page.locator(
      '[data-testid="product-search"], input[placeholder*="Search"]'
    ).first();

    this.createButton = page.locator(
      '[data-testid="create-product"], button:has-text("Create"), button:has-text("Add")'
    ).first();

    this.syncButton = page.locator(
      '[data-testid="sync-products"], button:has-text("Sync")'
    ).first();

    this.pagination = page.locator(
      '[data-testid="pagination"], .pagination, nav[aria-label="Pagination"]'
    ).first();
  }

  async goto() {
    await this.page.goto('/admin/products');
    await this.page.waitForLoadState('networkidle');
  }

  async getProductCount(): Promise<number> {
    return await this.productRows.count();
  }

  async searchProducts(query: string) {
    await this.searchInput.fill(query);
    await this.page.waitForLoadState('networkidle');
  }

  async selectProduct(sku: string) {
    await this.productRows.locator(`:has-text("${sku}")`).first().click();
    await this.page.waitForLoadState('networkidle');
  }

  async triggerSync() {
    await this.syncButton.click();
  }

  async goToPage(pageNumber: number) {
    await this.pagination.locator(`button:has-text("${pageNumber}")`).click();
    await this.page.waitForLoadState('networkidle');
  }
}

// =============================================================================
// EXPORT ALL PAGE OBJECTS
// =============================================================================

export const pages = {
  LoginPage,
  DashboardPage,
  AgentsPage,
  AgentDetailPage,
  ProductsPage,
};
