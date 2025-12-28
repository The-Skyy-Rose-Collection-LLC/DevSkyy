/**
 * 3D Asset Pipeline Dashboard
 * ===========================
 * SkyyRose 3D asset generation and management interface.
 * Features particle effects, real-time pipeline status, and asset preview.
 */

'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { threeDAPI } from '@/lib/api';
import { ModelViewer } from '@/components/ModelViewer';

// Types
interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
}

interface ThreeDJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  provider: string;
  prompt?: string;
  progress: number;
  result_url?: string;
  error_message?: string;
  created_at: string;
  processing_time_s?: number;
}

interface ThreeDProvider {
  id: string;
  name: string;
  description: string;
  supported_inputs: string[];
  avg_generation_time_s: number;
  available: boolean;
}

interface Service {
  name: string;
  status: 'connected' | 'disconnected';
}

// Animated particle background
const ParticleField: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    const particles: Particle[] = [];

    const resize = () => {
      canvas.width = canvas.offsetWidth * 2;
      canvas.height = canvas.offsetHeight * 2;
      ctx.scale(2, 2);
    };
    resize();

    // Create particles
    for (let i = 0; i < 80; i++) {
      particles.push({
        x: Math.random() * canvas.offsetWidth,
        y: Math.random() * canvas.offsetHeight,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        size: Math.random() * 2 + 0.5,
        opacity: Math.random() * 0.5 + 0.1,
      });
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight);

      particles.forEach((p, i) => {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0 || p.x > canvas.offsetWidth) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.offsetHeight) p.vy *= -1;

        // Draw particle
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(233, 30, 99, ${p.opacity})`;
        ctx.fill();

        // Draw connections
        particles.slice(i + 1).forEach((p2) => {
          const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
          if (dist < 100) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(233, 30, 99, ${0.1 * (1 - dist / 100)})`;
            ctx.stroke();
          }
        });
      });

      animationId = requestAnimationFrame(animate);
    };
    animate();

    return () => cancelAnimationFrame(animationId);
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />;
};

// Glowing orb component
interface GlowOrbProps {
  color: string;
  size: string;
  top: string;
  left: string;
  delay?: number;
}

const GlowOrb: React.FC<GlowOrbProps> = ({ color, size, top, left, delay = 0 }) => (
  <div
    className="absolute rounded-full blur-3xl animate-pulse"
    style={{
      background: `radial-gradient(circle, ${color}40 0%, transparent 70%)`,
      width: size,
      height: size,
      top,
      left,
      animationDelay: `${delay}s`,
      animationDuration: '4s',
    }}
  />
);

// Status indicator with pulse
type StatusType = 'active' | 'pending' | 'error' | 'idle';

const StatusPulse: React.FC<{ status: StatusType }> = ({ status }) => {
  const colors: Record<StatusType, string> = {
    active: 'bg-emerald-500',
    pending: 'bg-amber-500',
    error: 'bg-red-500',
    idle: 'bg-slate-500',
  };

  return (
    <div className="relative flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${colors[status]}`}>
        <div
          className={`absolute inset-0 w-2 h-2 rounded-full ${colors[status]} animate-ping`}
        />
      </div>
      <span className="text-xs uppercase tracking-wider text-slate-400">{status}</span>
    </div>
  );
};

// Metric card with glass effect
interface MetricCardProps {
  label: string;
  value: string;
  unit?: string;
  trend?: number;
  icon: string;
  accent?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  trend,
  icon,
  accent = false,
}) => (
  <div
    className={`relative group overflow-hidden rounded-2xl p-4 transition-all duration-500 hover:scale-[1.02] ${
      accent
        ? 'bg-gradient-to-br from-rose-500/20 to-purple-600/20 border border-rose-500/30'
        : 'bg-white/[0.03] border border-white/10'
    }`}
  >
    <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
    <div className="relative">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] uppercase tracking-[0.2em] text-slate-500">{label}</span>
        <span className="text-lg opacity-30">{icon}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span
          className={`text-3xl font-light tracking-tight ${accent ? 'text-rose-400' : 'text-white'}`}
        >
          {value}
        </span>
        {unit && <span className="text-sm text-slate-500">{unit}</span>}
      </div>
      {trend !== undefined && (
        <div className={`mt-2 text-xs ${trend > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
          {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% from last week
        </div>
      )}
    </div>
  </div>
);

// Pipeline stage visualization
interface PipelineStageProps {
  stage: string;
  status: 'complete' | 'active' | 'pending';
  time: string;
  active?: boolean;
}

const PipelineStage: React.FC<PipelineStageProps> = ({ stage, status, time, active = false }) => (
  <div
    className={`relative flex items-center gap-3 p-3 rounded-xl transition-all duration-300 ${
      active ? 'bg-rose-500/10 border border-rose-500/30' : 'bg-white/[0.02]'
    }`}
  >
    <div
      className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg ${
        status === 'complete'
          ? 'bg-emerald-500/20 text-emerald-400'
          : status === 'active'
            ? 'bg-rose-500/20 text-rose-400 animate-pulse'
            : 'bg-slate-800 text-slate-500'
      }`}
    >
      {status === 'complete' ? '✓' : status === 'active' ? '◉' : '○'}
    </div>
    <div className="flex-1">
      <div className="text-sm font-medium text-white">{stage}</div>
      <div className="text-xs text-slate-500">{time}</div>
    </div>
    {active && (
      <div className="w-16 h-1 bg-slate-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-rose-500 to-purple-500 animate-pulse"
          style={{ width: '60%' }}
        />
      </div>
    )}
  </div>
);

// 3D Preview with model-viewer or placeholder
interface Preview3DProps {
  generating: boolean;
  modelUrl?: string;
}

const Preview3D: React.FC<Preview3DProps> = ({ generating, modelUrl }) => {
  const [rotation, setRotation] = useState(0);

  useEffect(() => {
    if (!modelUrl) {
      const interval = setInterval(() => {
        setRotation((r) => (r + 1) % 360);
      }, 50);
      return () => clearInterval(interval);
    }
  }, [modelUrl]);

  return (
    <div className="relative aspect-square rounded-2xl bg-gradient-to-br from-slate-900 to-black overflow-hidden border border-white/5">
      {/* Grid pattern */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)`,
          backgroundSize: '20px 20px',
        }}
      />

      {modelUrl ? (
        /* Actual 3D Model Viewer */
        <ModelViewer
          src={modelUrl}
          alt="Generated 3D Asset"
          autoRotate
          cameraControls
          ar
          shadowIntensity={1}
          exposure={1}
          className="absolute inset-0"
        />
      ) : (
        /* Rotating 3D placeholder */
        <div className="absolute inset-0 flex items-center justify-center">
          <div
            className="relative w-32 h-32"
            style={{ transform: `rotateY(${rotation}deg)`, transformStyle: 'preserve-3d' }}
          >
            {/* Cube faces */}
            <div
              className="absolute inset-0 border-2 border-rose-500/30 bg-rose-500/5"
              style={{ transform: 'translateZ(64px)' }}
            />
            <div
              className="absolute inset-0 border-2 border-purple-500/30 bg-purple-500/5"
              style={{ transform: 'rotateY(90deg) translateZ(64px)' }}
            />
          </div>
        </div>
      )}

      {/* Generating overlay */}
      {generating && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center backdrop-blur-sm z-10">
          <div className="text-center">
            <div className="w-12 h-12 border-2 border-rose-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <div className="text-sm text-rose-400">Generating 3D Model</div>
            <div className="text-xs text-slate-500 mt-1">~8 seconds remaining</div>
          </div>
        </div>
      )}

      {/* Controls overlay */}
      <div className="absolute bottom-3 left-3 right-3 flex justify-between z-10">
        <div className="flex gap-1">
          {['↻', '⊕', '⊖'].map((icon, i) => (
            <button
              key={i}
              className="w-8 h-8 rounded-lg bg-black/50 border border-white/10 text-slate-400 text-xs hover:bg-white/10 hover:text-white transition-all"
            >
              {icon}
            </button>
          ))}
        </div>
        {!modelUrl && (
          <button className="px-3 h-8 rounded-lg bg-rose-500/20 border border-rose-500/30 text-rose-400 text-xs hover:bg-rose-500/30 transition-all">
            AR Preview
          </button>
        )}
      </div>
    </div>
  );
};

// Main Dashboard Component
export default function ThreeDPipelinePage() {
  const [activeTab, setActiveTab] = useState<'pipeline' | 'assets' | 'settings'>('pipeline');
  const [generating, setGenerating] = useState(false);
  const [uploadHover, setUploadHover] = useState(false);
  const [currentJob, setCurrentJob] = useState<ThreeDJob | null>(null);
  const [recentJobs, setRecentJobs] = useState<ThreeDJob[]>([]);
  const [providers, setProviders] = useState<ThreeDProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('trellis');
  const [pipelineStatus, setPipelineStatus] = useState<string>('operational');
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [providersData, jobsData, statusData] = await Promise.all([
          threeDAPI.getProviders().catch(() => []),
          threeDAPI.listJobs({ limit: 10 }).catch(() => []),
          threeDAPI.getStatus().catch(() => ({ status: 'unknown' })),
        ]);
        setProviders(providersData);
        setRecentJobs(jobsData);
        setPipelineStatus(statusData.status);
        if (providersData.length > 0) {
          setSelectedProvider(providersData[0].id);
        }
      } catch (err) {
        console.error('Failed to fetch 3D pipeline data:', err);
      }
    };
    fetchData();
  }, []);

  // Handle file upload and generation
  const handleGenerate = useCallback(async (file?: File) => {
    setGenerating(true);
    setError(null);

    try {
      let job: ThreeDJob;

      if (file) {
        // Upload file and generate
        job = await threeDAPI.generateFromUpload(
          file,
          selectedProvider as 'trellis' | 'tripo'
        );
      } else {
        // Demo: generate from text prompt (requires image for TRELLIS)
        job = await threeDAPI.generateFromText({
          prompt: 'SkyyRose luxury clothing item',
          provider: selectedProvider as 'trellis' | 'tripo',
        });
      }

      setCurrentJob(job);

      // Poll for completion
      const completedJob = await threeDAPI.pollJob(
        job.id,
        (updatedJob) => setCurrentJob(updatedJob),
        2000,
        60
      );

      setCurrentJob(completedJob);
      // Refresh recent jobs list
      const updatedJobs = await threeDAPI.listJobs({ limit: 10 });
      setRecentJobs(updatedJobs);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
      console.error('3D generation error:', err);
    } finally {
      setGenerating(false);
    }
  }, [selectedProvider]);

  // Handle file drop
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setUploadHover(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.type.startsWith('image/') || file.name.endsWith('.png') || file.name.endsWith('.jpg'))) {
      handleGenerate(file);
    }
  }, [handleGenerate]);

  // Handle file input change
  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleGenerate(file);
    }
  }, [handleGenerate]);

  // Convert job to display format
  const getJobDisplayInfo = (job: ThreeDJob) => {
    const timeAgo = getTimeAgo(job.created_at);
    return {
      name: job.prompt || `3D Asset ${job.id.slice(0, 8)}`,
      status: job.status === 'completed' ? 'complete' as const :
              job.status === 'processing' ? 'processing' as const : 'pending' as const,
      time: timeAgo,
      score: job.status === 'completed' ? 92 : null, // Placeholder score
    };
  };

  const getTimeAgo = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  // Convert providers to display format
  const models = providers.length > 0 ? providers.map(p => ({
    id: p.id,
    name: p.name,
    desc: `${p.description} • ~${p.avg_generation_time_s}s`,
    active: p.id === selectedProvider,
  })) : [
    { id: 'trellis', name: 'TRELLIS (Microsoft)', desc: 'HuggingFace Gradio • ~30s', active: selectedProvider === 'trellis' },
    { id: 'tripo', name: 'Tripo3D', desc: 'Commercial API • ~10s', active: selectedProvider === 'tripo' },
  ];

  const services: Service[] = [
    { name: 'WordPress', status: 'connected' },
    { name: 'WooCommerce', status: 'connected' },
    { name: 'Cloudflare R2', status: 'connected' },
    { name: 'Redis Queue', status: 'connected' },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white overflow-hidden -m-8">
      {/* Background effects */}
      <div className="fixed inset-0 pointer-events-none">
        <ParticleField />
        <GlowOrb color="#e91e63" size="600px" top="-200px" left="-200px" />
        <GlowOrb color="#9333ea" size="500px" top="60%" left="70%" delay={2} />
        <GlowOrb color="#06b6d4" size="400px" top="80%" left="10%" delay={1} />
      </div>

      {/* Noise overlay */}
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.015]"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E\")",
        }}
      />

      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-white/5 bg-black/20 backdrop-blur-xl">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-500 to-purple-600 flex items-center justify-center font-bold text-lg">
                    S
                  </div>
                  <div>
                    <div className="font-semibold tracking-wide">SKYYROSE</div>
                    <div className="text-[10px] text-slate-500 tracking-[0.3em]">
                      3D ASSET PIPELINE
                    </div>
                  </div>
                </div>
                <div className="h-8 w-px bg-white/10" />
                <StatusPulse status="active" />
              </div>

              <div className="flex items-center gap-4">
                <div className="flex bg-white/5 rounded-xl p-1">
                  {(['pipeline', 'assets', 'settings'] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`px-4 py-2 rounded-lg text-sm capitalize transition-all ${
                        activeTab === tab
                          ? 'bg-white/10 text-white'
                          : 'text-slate-500 hover:text-white'
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-rose-500 to-purple-600 border-2 border-white/20" />
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-6 py-8">
          {/* Metrics Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <MetricCard label="Assets Generated" value="1,247" trend={12} icon="◈" accent />
            <MetricCard label="Avg Generation" value="8.4" unit="sec" trend={-8} icon="◷" />
            <MetricCard label="Quality Score" value="92" unit="%" trend={3} icon="◉" />
            <MetricCard label="Cost This Month" value="$47" unit=".80" icon="◇" />
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Upload & Preview Column */}
            <div className="lg:col-span-2 space-y-6">
              {/* Upload Zone */}
              <div
                className={`relative rounded-2xl border-2 border-dashed transition-all duration-300 ${
                  uploadHover
                    ? 'border-rose-500 bg-rose-500/5'
                    : 'border-white/10 bg-white/[0.02]'
                }`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setUploadHover(true);
                }}
                onDragLeave={() => setUploadHover(false)}
                onDrop={handleDrop}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <div className="p-8 text-center">
                  <div
                    className={`w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center text-2xl transition-all ${
                      uploadHover
                        ? 'bg-rose-500/20 text-rose-400 scale-110'
                        : 'bg-white/5 text-slate-500'
                    }`}
                  >
                    ↑
                  </div>
                  <div className="text-lg font-medium mb-1">
                    {uploadHover ? 'Release to upload' : 'Drop product photos here'}
                  </div>
                  <div className="text-sm text-slate-500 mb-4">
                    or click to browse • PNG, JPG up to 10MB
                  </div>
                  {error && (
                    <div className="text-sm text-red-400 mb-4 p-2 rounded bg-red-500/10">
                      {error}
                    </div>
                  )}
                  <div className="flex justify-center gap-3">
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={generating}
                      className="px-6 py-3 rounded-xl bg-gradient-to-r from-rose-500 to-purple-600 font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                    >
                      {generating ? 'Generating...' : 'Upload & Generate'}
                    </button>
                    <button
                      onClick={() => handleGenerate()}
                      disabled={generating}
                      className="px-6 py-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all disabled:opacity-50"
                    >
                      Demo Generate
                    </button>
                  </div>
                </div>
              </div>

              {/* 3D Preview */}
              <div className="grid md:grid-cols-2 gap-6">
                <Preview3D generating={generating} modelUrl={currentJob?.result_url} />

                {/* Pipeline Stages */}
                <div className="space-y-3">
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-500 mb-4">
                    Pipeline Status
                  </div>
                  <PipelineStage stage="Image Processing" status="complete" time="0.2s" />
                  <PipelineStage stage="3D Generation" status="active" time="~8s" active />
                  <PipelineStage stage="2-LLM Validation" status="pending" time="~2s" />
                  <PipelineStage stage="Optimization" status="pending" time="~1s" />
                  <PipelineStage stage="CDN Deployment" status="pending" time="<1s" />
                </div>
              </div>
            </div>

            {/* Right Sidebar */}
            <div className="space-y-6">
              {/* Model Selection */}
              <div className="rounded-2xl bg-white/[0.02] border border-white/5 p-4">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500 mb-4">
                  Generation Model
                </div>
                <div className="space-y-2">
                  {models.map((model) => (
                    <div
                      key={model.id}
                      onClick={() => setSelectedProvider(model.id)}
                      className={`p-3 rounded-xl cursor-pointer transition-all ${
                        model.active
                          ? 'bg-gradient-to-r from-rose-500/20 to-purple-600/20 border border-rose-500/30'
                          : 'bg-white/[0.02] border border-transparent hover:border-white/10'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-sm">{model.name}</div>
                          <div className="text-xs text-slate-500">{model.desc}</div>
                        </div>
                        <div
                          className={`w-4 h-4 rounded-full border-2 ${
                            model.active ? 'border-rose-500 bg-rose-500' : 'border-slate-600'
                          }`}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Assets */}
              <div className="rounded-2xl bg-white/[0.02] border border-white/5 p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-500">
                    Recent Assets
                  </div>
                  <button className="text-xs text-rose-400 hover:text-rose-300">View All →</button>
                </div>
                <div className="space-y-2">
                  {recentJobs.length === 0 ? (
                    <div className="text-sm text-slate-500 text-center py-4">
                      No assets generated yet
                    </div>
                  ) : (
                    recentJobs.map((job) => {
                      const displayInfo = getJobDisplayInfo(job);
                      return (
                        <div
                          key={job.id}
                          className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 transition-all cursor-pointer"
                        >
                          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center text-xs text-slate-500">
                            3D
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium truncate">{displayInfo.name}</div>
                            <div className="text-xs text-slate-500">{displayInfo.time}</div>
                          </div>
                          {displayInfo.status === 'complete' ? (
                            <div className="text-xs px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-400">
                              {displayInfo.score}%
                            </div>
                          ) : displayInfo.status === 'processing' ? (
                            <div className="w-4 h-4 border-2 border-rose-500 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <div className="text-xs text-slate-500">queued</div>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Quick Stats */}
              <div className="rounded-2xl bg-gradient-to-br from-rose-500/10 to-purple-600/10 border border-rose-500/20 p-4">
                <div className="text-xs uppercase tracking-[0.2em] text-rose-400/70 mb-3">
                  This Week
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-2xl font-light text-white">87</div>
                    <div className="text-xs text-slate-500">Assets Created</div>
                  </div>
                  <div>
                    <div className="text-2xl font-light text-white">$12.40</div>
                    <div className="text-xs text-slate-500">Total Cost</div>
                  </div>
                  <div>
                    <div className="text-2xl font-light text-white">94%</div>
                    <div className="text-xs text-slate-500">Pass Rate</div>
                  </div>
                  <div>
                    <div className="text-2xl font-light text-white">8.1s</div>
                    <div className="text-xs text-slate-500">Avg Time</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Integration Status */}
          <div className="mt-8 rounded-2xl bg-white/[0.02] border border-white/5 p-4">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-6">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500">
                  DevSkyy Integration
                </div>
                <div className="flex items-center gap-4 flex-wrap">
                  {services.map((service, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-emerald-500" />
                      <span className="text-xs text-slate-400">{service.name}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="text-xs text-slate-500">
                2-LLM Validation: <span className="text-emerald-400">Active</span> • Claude Opus +
                GPT-4 Turbo
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
