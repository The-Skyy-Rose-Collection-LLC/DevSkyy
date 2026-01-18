/**
 * ARTryOnViewer - Web-based AR Try-On for SkyyRose Collections
 *
 * Integrates webcam capture with FASHN API for virtual garment try-on.
 * Supports collection-themed UI styling for BLACK ROSE, LOVE HURTS, SIGNATURE.
 */

/** AR-specific performance metrics for webcam-based try-on */
interface ARMetrics {
  fps: number;
  frameTime: number;
  captureCount: number;
  lastCaptureTime: number;
}

export interface ARProduct {
  id: string;
  name: string;
  sku: string;
  price: number;
  garmentImageUrl: string;
  category: 'tops' | 'bottoms' | 'dresses' | 'outerwear' | 'full_body';
  collection: 'black_rose' | 'love_hurts' | 'signature';
  variants?: Array<{
    id: string;
    name: string;
    garmentImageUrl: string;
  }>;
}

export interface ARTryOnConfig {
  container: HTMLElement;
  collection: 'black_rose' | 'love_hurts' | 'signature';
  fashnApiEndpoint?: string;
  onTryOnComplete?: (resultUrl: string, product: ARProduct) => void;
  onError?: (error: Error) => void;
  onAddToCart?: (product: ARProduct, variantId?: string) => void;
}

interface CollectionTheme {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  text: string;
}

const COLLECTION_THEMES: Record<string, CollectionTheme> = {
  black_rose: {
    primary: '#C0C0C0',
    secondary: '#1A1A1A',
    accent: '#8B0000',
    background: 'rgba(10, 10, 15, 0.95)',
    text: '#E8E8E8',
  },
  love_hurts: {
    primary: '#B76E79',
    secondary: '#2D1F2D',
    accent: '#FFD700',
    background: 'rgba(45, 31, 45, 0.95)',
    text: '#F5E6E8',
  },
  signature: {
    primary: '#C9A962',
    secondary: '#1A1A1A',
    accent: '#F5F5DC',
    background: 'rgba(26, 26, 26, 0.95)',
    text: '#F5F5F5',
  },
};

export class ARTryOnViewer {
  private config: ARTryOnConfig;
  private theme: CollectionTheme;
  private container: HTMLElement;

  private videoElement: HTMLVideoElement | null = null;
  private canvasElement: HTMLCanvasElement | null = null;
  private resultOverlay: HTMLDivElement | null = null;
  private controlsPanel: HTMLDivElement | null = null;
  private loadingIndicator: HTMLDivElement | null = null;

  private mediaStream: MediaStream | null = null;
  private currentProduct: ARProduct | null = null;
  private selectedVariantId: string | null = null;
  private isProcessing = false;
  private metrics: ARMetrics = {
    fps: 0,
    frameTime: 0,
    captureCount: 0,
    lastCaptureTime: 0,
  };

  constructor(config: ARTryOnConfig) {
    this.config = config;
    this.theme = (COLLECTION_THEMES[config.collection] ?? COLLECTION_THEMES['signature']) as CollectionTheme;
    this.container = config.container;
  }

  async initialize(): Promise<void> {
    this.createUI();
    await this.initializeCamera();
    this.setupEventListeners();
  }

  private createUI(): void {
    this.container.style.position = 'relative';
    this.container.style.width = '100%';
    this.container.style.height = '100%';
    this.container.style.backgroundColor = this.theme.background;
    this.container.style.overflow = 'hidden';

    // Video element for webcam feed
    this.videoElement = document.createElement('video');
    this.videoElement.autoplay = true;
    this.videoElement.playsInline = true;
    this.videoElement.muted = true;
    Object.assign(this.videoElement.style, {
      position: 'absolute',
      top: '0',
      left: '0',
      width: '100%',
      height: '100%',
      objectFit: 'cover',
      transform: 'scaleX(-1)',
    });
    this.container.appendChild(this.videoElement);

    // Canvas for capturing frames
    this.canvasElement = document.createElement('canvas');
    this.canvasElement.style.display = 'none';
    this.container.appendChild(this.canvasElement);

    // Result overlay for try-on results
    this.resultOverlay = document.createElement('div');
    Object.assign(this.resultOverlay.style, {
      position: 'absolute',
      top: '0',
      left: '0',
      width: '100%',
      height: '100%',
      display: 'none',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      zIndex: '10',
    });
    this.container.appendChild(this.resultOverlay);

    // Controls panel
    this.controlsPanel = document.createElement('div');
    Object.assign(this.controlsPanel.style, {
      position: 'absolute',
      bottom: '20px',
      left: '50%',
      transform: 'translateX(-50%)',
      display: 'flex',
      gap: '16px',
      padding: '16px 24px',
      backgroundColor: this.theme.background,
      borderRadius: '12px',
      border: `1px solid ${this.theme.primary}`,
      zIndex: '5',
    });
    this.container.appendChild(this.controlsPanel);

    this.createControlButtons();
    this.createLoadingIndicator();
  }

  private createControlButtons(): void {
    if (!this.controlsPanel) return;

    // Capture button
    const captureBtn = this.createButton('Capture', () => this.captureAndTryOn());
    captureBtn.style.backgroundColor = this.theme.primary;
    captureBtn.style.color = this.theme.secondary;
    this.controlsPanel.appendChild(captureBtn);

    // Switch camera button
    const switchBtn = this.createButton('Switch Camera', () => this.switchCamera());
    this.controlsPanel.appendChild(switchBtn);

    // Close button
    const closeBtn = this.createButton('Close', () => this.close());
    closeBtn.style.backgroundColor = 'transparent';
    closeBtn.style.border = `1px solid ${this.theme.primary}`;
    this.controlsPanel.appendChild(closeBtn);
  }

  private createButton(text: string, onClick: () => void): HTMLButtonElement {
    const button = document.createElement('button');
    button.textContent = text;
    Object.assign(button.style, {
      padding: '12px 24px',
      fontSize: '14px',
      fontWeight: '600',
      fontFamily: 'Inter, sans-serif',
      color: this.theme.text,
      backgroundColor: this.theme.secondary,
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
    });
    button.addEventListener('click', onClick);
    button.addEventListener('mouseenter', () => {
      button.style.opacity = '0.9';
      button.style.transform = 'scale(1.02)';
    });
    button.addEventListener('mouseleave', () => {
      button.style.opacity = '1';
      button.style.transform = 'scale(1)';
    });
    return button;
  }

  private createLoadingIndicator(): void {
    this.loadingIndicator = document.createElement('div');
    Object.assign(this.loadingIndicator.style, {
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      display: 'none',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '16px',
      zIndex: '15',
    });

    // Spinner element
    const spinner = document.createElement('div');
    Object.assign(spinner.style, {
      width: '48px',
      height: '48px',
      border: `3px solid ${this.theme.secondary}`,
      borderTop: `3px solid ${this.theme.primary}`,
      borderRadius: '50%',
      animation: 'ar-spin 1s linear infinite',
    });
    this.loadingIndicator.appendChild(spinner);

    // Loading text
    const loadingText = document.createElement('p');
    loadingText.textContent = 'Processing try-on...';
    Object.assign(loadingText.style, {
      color: this.theme.text,
      fontSize: '14px',
      fontFamily: 'Inter, sans-serif',
      margin: '0',
    });
    this.loadingIndicator.appendChild(loadingText);

    this.container.appendChild(this.loadingIndicator);

    // Add keyframes for spinner animation
    const styleSheet = document.createElement('style');
    styleSheet.textContent = `
      @keyframes ar-spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(styleSheet);
  }

  private async initializeCamera(): Promise<void> {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });

      if (this.videoElement) {
        this.videoElement.srcObject = this.mediaStream;
      }
    } catch (error) {
      console.error('[ARTryOnViewer] Camera initialization failed:', error);
      this.config.onError?.(error instanceof Error ? error : new Error('Camera access denied'));
    }
  }

  private async switchCamera(): Promise<void> {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
    }

    const currentFacingMode = this.mediaStream?.getVideoTracks()[0]?.getSettings().facingMode;
    const newFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';

    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: newFacingMode,
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });

      if (this.videoElement) {
        this.videoElement.srcObject = this.mediaStream;
        this.videoElement.style.transform = newFacingMode === 'user' ? 'scaleX(-1)' : 'scaleX(1)';
      }
    } catch (error) {
      console.error('[ARTryOnViewer] Camera switch failed:', error);
    }
  }

  private setupEventListeners(): void {
    window.addEventListener('resize', () => this.handleResize());
  }

  private handleResize(): void {
    if (this.canvasElement && this.videoElement) {
      this.canvasElement.width = this.videoElement.videoWidth;
      this.canvasElement.height = this.videoElement.videoHeight;
    }
  }

  setProduct(product: ARProduct): void {
    this.currentProduct = product;
    this.selectedVariantId = null;
    this.updateProductInfoPanel();
  }

  selectVariant(variantId: string): void {
    this.selectedVariantId = variantId;
    this.updateProductInfoPanel();
  }

  private updateProductInfoPanel(): void {
    const existingPanel = this.container.querySelector('.ar-product-info');
    if (existingPanel) {
      existingPanel.remove();
    }

    if (!this.currentProduct) return;

    const panel = document.createElement('div');
    panel.className = 'ar-product-info';
    Object.assign(panel.style, {
      position: 'absolute',
      top: '20px',
      left: '20px',
      padding: '16px',
      backgroundColor: this.theme.background,
      borderRadius: '8px',
      border: `1px solid ${this.theme.primary}`,
      maxWidth: '250px',
      zIndex: '5',
    });

    // Product name
    const nameEl = document.createElement('h3');
    nameEl.textContent = this.currentProduct.name;
    Object.assign(nameEl.style, {
      color: this.theme.primary,
      fontSize: '16px',
      fontWeight: '600',
      margin: '0 0 8px 0',
      fontFamily: 'Inter, sans-serif',
    });
    panel.appendChild(nameEl);

    // Product price
    const priceEl = document.createElement('p');
    priceEl.textContent = `$${this.currentProduct.price.toFixed(2)}`;
    Object.assign(priceEl.style, {
      color: this.theme.text,
      fontSize: '14px',
      margin: '0 0 12px 0',
      fontFamily: 'Inter, sans-serif',
    });
    panel.appendChild(priceEl);

    // Variants (if available)
    if (this.currentProduct.variants && this.currentProduct.variants.length > 0) {
      const variantsContainer = document.createElement('div');
      Object.assign(variantsContainer.style, {
        display: 'flex',
        gap: '8px',
        flexWrap: 'wrap',
      });

      this.currentProduct.variants.forEach(variant => {
        const variantBtn = document.createElement('button');
        variantBtn.textContent = variant.name;
        const isSelected = this.selectedVariantId === variant.id;
        Object.assign(variantBtn.style, {
          padding: '6px 12px',
          fontSize: '12px',
          backgroundColor: isSelected ? this.theme.primary : 'transparent',
          color: isSelected ? this.theme.secondary : this.theme.text,
          border: `1px solid ${this.theme.primary}`,
          borderRadius: '4px',
          cursor: 'pointer',
          fontFamily: 'Inter, sans-serif',
        });
        variantBtn.addEventListener('click', () => this.selectVariant(variant.id));
        variantsContainer.appendChild(variantBtn);
      });

      panel.appendChild(variantsContainer);
    }

    this.container.appendChild(panel);
  }

  private async captureAndTryOn(): Promise<void> {
    if (!this.videoElement || !this.canvasElement || !this.currentProduct || this.isProcessing) {
      return;
    }

    this.isProcessing = true;
    this.showLoading(true);

    try {
      // Capture frame from video
      const ctx = this.canvasElement.getContext('2d');
      if (!ctx) throw new Error('Canvas context unavailable');

      this.canvasElement.width = this.videoElement.videoWidth;
      this.canvasElement.height = this.videoElement.videoHeight;

      // Flip horizontally if using front camera
      ctx.save();
      ctx.scale(-1, 1);
      ctx.drawImage(this.videoElement, -this.canvasElement.width, 0);
      ctx.restore();

      const modelImageUrl = this.canvasElement.toDataURL('image/jpeg', 0.9);

      // Get garment URL (use variant if selected)
      let garmentUrl = this.currentProduct.garmentImageUrl;
      if (this.selectedVariantId && this.currentProduct.variants) {
        const variant = this.currentProduct.variants.find(v => v.id === this.selectedVariantId);
        if (variant) {
          garmentUrl = variant.garmentImageUrl;
        }
      }

      // Call FASHN API for try-on
      const resultUrl = await this.processTryOn(modelImageUrl, garmentUrl);

      this.showResult(resultUrl);
      this.config.onTryOnComplete?.(resultUrl, this.currentProduct);

    } catch (error) {
      console.error('[ARTryOnViewer] Try-on failed:', error);
      this.config.onError?.(error instanceof Error ? error : new Error('Try-on processing failed'));
    } finally {
      this.isProcessing = false;
      this.showLoading(false);
    }
  }

  private async processTryOn(modelImageUrl: string, garmentImageUrl: string): Promise<string> {
    const endpoint = this.config.fashnApiEndpoint || '/api/v1/virtual-tryon';

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model_image_url: modelImageUrl,
        garment_image_url: garmentImageUrl,
        category: this.currentProduct?.category || 'tops',
        mode: 'balanced',
      }),
    });

    if (!response.ok) {
      throw new Error(`Try-on API error: ${response.status}`);
    }

    const data = await response.json();
    return data.result_url || data.output_url;
  }

  private showResult(resultUrl: string): void {
    if (!this.resultOverlay) return;

    // Clear previous content
    while (this.resultOverlay.firstChild) {
      this.resultOverlay.removeChild(this.resultOverlay.firstChild);
    }

    // Result image
    const resultImg = document.createElement('img');
    resultImg.src = resultUrl;
    Object.assign(resultImg.style, {
      maxWidth: '90%',
      maxHeight: '80%',
      objectFit: 'contain',
      borderRadius: '8px',
    });
    this.resultOverlay.appendChild(resultImg);

    // Action buttons container
    const actionsContainer = document.createElement('div');
    Object.assign(actionsContainer.style, {
      position: 'absolute',
      bottom: '20px',
      display: 'flex',
      gap: '16px',
    });

    // Add to Cart button
    const addToCartBtn = this.createButton('Add to Cart', () => {
      if (this.currentProduct) {
        this.config.onAddToCart?.(this.currentProduct, this.selectedVariantId || undefined);
      }
    });
    addToCartBtn.style.backgroundColor = this.theme.primary;
    addToCartBtn.style.color = this.theme.secondary;
    actionsContainer.appendChild(addToCartBtn);

    // Try Again button
    const tryAgainBtn = this.createButton('Try Again', () => this.hideResult());
    actionsContainer.appendChild(tryAgainBtn);

    // Download button
    const downloadBtn = this.createButton('Download', () => this.downloadResult(resultUrl));
    actionsContainer.appendChild(downloadBtn);

    this.resultOverlay.appendChild(actionsContainer);
    this.resultOverlay.style.display = 'flex';
  }

  private hideResult(): void {
    if (this.resultOverlay) {
      this.resultOverlay.style.display = 'none';
    }
  }

  private downloadResult(url: string): void {
    const link = document.createElement('a');
    link.href = url;
    link.download = `skyyrose-tryon-${Date.now()}.jpg`;
    link.click();
  }

  private showLoading(show: boolean): void {
    if (this.loadingIndicator) {
      this.loadingIndicator.style.display = show ? 'flex' : 'none';
    }
  }

  captureSnapshot(): string | null {
    if (!this.videoElement || !this.canvasElement) return null;

    const ctx = this.canvasElement.getContext('2d');
    if (!ctx) return null;

    this.canvasElement.width = this.videoElement.videoWidth;
    this.canvasElement.height = this.videoElement.videoHeight;

    ctx.save();
    ctx.scale(-1, 1);
    ctx.drawImage(this.videoElement, -this.canvasElement.width, 0);
    ctx.restore();

    return this.canvasElement.toDataURL('image/jpeg', 0.9);
  }

  getMetrics(): ARMetrics {
    return { ...this.metrics };
  }

  close(): void {
    this.dispose();
  }

  dispose(): void {
    // Stop media stream
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }

    // Clear container
    while (this.container.firstChild) {
      this.container.removeChild(this.container.firstChild);
    }

    // Reset references
    this.videoElement = null;
    this.canvasElement = null;
    this.resultOverlay = null;
    this.controlsPanel = null;
    this.loadingIndicator = null;
    this.currentProduct = null;
  }
}

export default ARTryOnViewer;
