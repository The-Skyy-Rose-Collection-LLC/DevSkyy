import sharp from 'sharp';
import { fal } from '@fal-ai/serverless-client';
import Replicate from 'replicate';

interface LuxuryEnhanceOptions {
  removeBackground?: boolean;
  upscale?: boolean;
  applyLuxuryFilter?: boolean;
  targetWidth?: number;
  targetHeight?: number;
  quality?: number;
  format?: 'webp' | 'jpeg' | 'png' | 'avif';
}

interface EnhancedImage {
  buffer: Buffer;
  metadata: {
    width: number;
    height: number;
    format: string;
    size: number;
  };
  processingTime: number;
}

export class LuxuryImageProcessor {
  private replicate: Replicate;

  constructor() {
    this.replicate = new Replicate({
      auth: process.env.REPLICATE_API_TOKEN || '',
    });

    // Initialize fal client
    fal.config({
      credentials: process.env.FAL_KEY || '',
    });
  }

  /**
   * Enhance product image with luxury aesthetic
   */
  async enhanceProductImage(
    inputBuffer: Buffer,
    options: LuxuryEnhanceOptions = {}
  ): Promise<EnhancedImage> {
    const startTime = Date.now();

    const {
      removeBackground = true,
      upscale = true,
      applyLuxuryFilter = true,
      targetWidth = 2048,
      targetHeight = 2048,
      quality = 95,
      format = 'webp',
    } = options;

    let processedBuffer = inputBuffer;

    // Step 1: Remove background if requested
    if (removeBackground) {
      processedBuffer = await this.removeBackground(processedBuffer);
    }

    // Step 2: Upscale if requested
    if (upscale) {
      processedBuffer = await this.upscaleImage(processedBuffer);
    }

    // Step 3: Apply luxury color grading
    if (applyLuxuryFilter) {
      processedBuffer = await this.applyLuxuryGrading(processedBuffer);
    }

    // Step 4: Optimize and resize
    const finalImage = await sharp(processedBuffer)
      .resize(targetWidth, targetHeight, {
        fit: 'inside',
        withoutEnlargement: false,
      })
      [format]({ quality })
      .toBuffer({ resolveWithObject: true });

    return {
      buffer: finalImage.data,
      metadata: {
        width: finalImage.info.width,
        height: finalImage.info.height,
        format: finalImage.info.format,
        size: finalImage.info.size,
      },
      processingTime: Date.now() - startTime,
    };
  }

  /**
   * Remove background using RemBG
   */
  private async removeBackground(buffer: Buffer): Promise<Buffer> {
    try {
      // Use Replicate's background removal
      const output = await this.replicate.run(
        'cjwbw/rembg:fb8af171cfa1616ddcf1242c093f9c46bcada5ad4cf6f2fbe8b81b330ec5c003',
        {
          input: {
            image: buffer.toString('base64'),
          },
        }
      ) as string;

      // Download and return the result
      const response = await fetch(output);
      const arrayBuffer = await response.arrayBuffer();
      return Buffer.from(arrayBuffer);
    } catch (error) {
      console.error('Background removal failed:', error);
      return buffer; // Return original on error
    }
  }

  /**
   * Upscale image using FLUX or Stable Diffusion upscaler
   */
  private async upscaleImage(buffer: Buffer): Promise<Buffer> {
    try {
      // Use fal.ai for fast upscaling
      const result = await fal.subscribe('fal-ai/clarity-upscaler', {
        input: {
          image_url: `data:image/png;base64,${buffer.toString('base64')}`,
          prompt: 'luxury fashion product, high detail, professional photography',
          negative_prompt: 'blurry, low quality, distorted',
        },
      }) as { images: Array<{ url: string }> };

      const imageUrl = result.images[0].url;
      const response = await fetch(imageUrl);
      const arrayBuffer = await response.arrayBuffer();
      return Buffer.from(arrayBuffer);
    } catch (error) {
      console.error('Upscaling failed:', error);
      return buffer; // Return original on error
    }
  }

  /**
   * Apply luxury color grading (rose gold, warm tones)
   */
  private async applyLuxuryGrading(buffer: Buffer): Promise<Buffer> {
    // SkyyRose signature color grading
    const luxuryGraded = await sharp(buffer)
      .modulate({
        brightness: 1.05, // Slightly brighter
        saturation: 1.15, // More saturated
        hue: -5, // Shift towards rose/pink
      })
      .linear(1.1, -(128 * 0.1)) // Increase contrast
      .tint({ r: 183, g: 110, b: 121 }) // #B76E79 tint at low opacity
      .toBuffer();

    // Apply curves for luxury feel
    return sharp(luxuryGraded)
      .gamma(1.2) // Lift shadows
      .normalize() // Stretch histogram
      .sharpen({ sigma: 1 }) // Slight sharpening
      .toBuffer();
  }

  /**
   * Generate responsive image set (srcset)
   */
  async generateResponsiveSet(
    inputBuffer: Buffer,
    sizes: number[] = [320, 640, 960, 1280, 1920, 2560]
  ): Promise<Map<number, Buffer>> {
    const responseSet = new Map<number, Buffer>();

    await Promise.all(
      sizes.map(async (width) => {
        const resized = await sharp(inputBuffer)
          .resize(width, null, {
            fit: 'inside',
            withoutEnlargement: true,
          })
          .webp({ quality: 85 })
          .toBuffer();

        responseSet.set(width, resized);
      })
    );

    return responseSet;
  }

  /**
   * Generate blurhash placeholder
   */
  async generateBlurhash(buffer: Buffer): Promise<string> {
    const { encode } = await import('blurhash');

    // Resize to small size for blurhash
    const { data, info } = await sharp(buffer)
      .resize(32, 32, { fit: 'inside' })
      .ensureAlpha()
      .raw()
      .toBuffer({ resolveWithObject: true });

    return encode(
      new Uint8ClampedArray(data),
      info.width,
      info.height,
      4,
      4
    );
  }

  /**
   * Generate Open Graph image
   */
  async generateOGImage(options: {
    productName: string;
    collectionName: string;
    price: string;
    imageBuffer?: Buffer;
  }): Promise<Buffer> {
    const { ImageResponse } = await import('@vercel/og');

    const html = {
      type: 'div',
      props: {
        style: {
          display: 'flex',
          width: '1200px',
          height: '630px',
          backgroundColor: '#0f172a',
          backgroundImage: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
          fontFamily: 'system-ui',
        },
        children: [
          // Product image
          options.imageBuffer && {
            type: 'img',
            props: {
              src: `data:image/png;base64,${options.imageBuffer.toString('base64')}`,
              style: {
                width: '500px',
                height: '630px',
                objectFit: 'cover',
              },
            },
          },
          // Text content
          {
            type: 'div',
            props: {
              style: {
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                padding: '60px',
                flex: 1,
              },
              children: [
                {
                  type: 'div',
                  props: {
                    style: {
                      fontSize: '48px',
                      fontWeight: '300',
                      color: '#ffffff',
                      marginBottom: '20px',
                      letterSpacing: '2px',
                    },
                    children: options.productName,
                  },
                },
                {
                  type: 'div',
                  props: {
                    style: {
                      fontSize: '24px',
                      color: '#B76E79',
                      marginBottom: '40px',
                      letterSpacing: '4px',
                      textTransform: 'uppercase',
                    },
                    children: options.collectionName,
                  },
                },
                {
                  type: 'div',
                  props: {
                    style: {
                      fontSize: '36px',
                      fontWeight: '200',
                      color: '#ffffff',
                      letterSpacing: '1px',
                    },
                    children: options.price,
                  },
                },
                {
                  type: 'div',
                  props: {
                    style: {
                      fontSize: '18px',
                      color: '#B76E79',
                      marginTop: '60px',
                      letterSpacing: '3px',
                      textTransform: 'uppercase',
                    },
                    children: 'The Skyy Rose Collection',
                  },
                },
              ],
            },
          },
        ].filter(Boolean),
      },
    };

    const imageResponse = new ImageResponse(html as any, {
      width: 1200,
      height: 630,
    });

    const arrayBuffer = await imageResponse.arrayBuffer();
    return Buffer.from(arrayBuffer);
  }
}

// Export singleton instance
export const luxuryImageProcessor = new LuxuryImageProcessor();
