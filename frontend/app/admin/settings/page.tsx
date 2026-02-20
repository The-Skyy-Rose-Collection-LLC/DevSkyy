'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Save,
  RefreshCw,
  Eye,
  EyeOff,
  Check,
  AlertCircle,
  Globe,
  Zap,
  Bot,
  Palette,
  Key,
  Settings as SettingsIcon,
} from 'lucide-react';

interface SettingsState {
  wordpress: {
    url: string;
    consumerKey: string;
    consumerSecret: string;
    autoSync: boolean;
  };
  vercel: {
    projectId: string;
    apiToken: string;
    orgId: string;
  };
  autonomous: {
    enabled: boolean;
    circuitBreakerThreshold: number;
    retryAttempts: number;
    retryDelay: number;
  };
  ui: {
    theme: 'light' | 'dark';
    typography: 'playfair' | 'inter' | 'system';
    accentColor: string;
  };
  system: {
    apiTimeout: number;
    maxConcurrentRequests: number;
    logLevel: 'debug' | 'info' | 'warn' | 'error';
  };
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsState>({
    wordpress: {
      url: '',
      consumerKey: '',
      consumerSecret: '',
      autoSync: true,
    },
    vercel: {
      projectId: '',
      apiToken: '',
      orgId: '',
    },
    autonomous: {
      enabled: true,
      circuitBreakerThreshold: 5,
      retryAttempts: 3,
      retryDelay: 2000,
    },
    ui: {
      theme: 'dark',
      typography: 'playfair',
      accentColor: '#B76E79',
    },
    system: {
      apiTimeout: 30000,
      maxConcurrentRequests: 10,
      logLevel: 'info',
    },
  });

  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      // Load from localStorage for now
      const stored = localStorage.getItem('devskyy-settings');
      if (stored) {
        setSettings(JSON.parse(stored));
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = async () => {
    setSaveStatus('saving');
    setErrorMessage('');

    try {
      // Save to localStorage for now
      localStorage.setItem('devskyy-settings', JSON.stringify(settings));

      // TODO: Also save to backend API
      // await api.settings.update(settings)

      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (error) {
      setSaveStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Failed to save settings');
    }
  };

  const toggleSecret = (key: string) => {
    setShowSecrets((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const maskSecret = (value: string, show: boolean) => {
    if (!value) return '';
    return show ? value : '•'.repeat(Math.min(value.length, 20));
  };

  const updateSetting = (section: keyof SettingsState, key: string, value: any) => {
    setSettings((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
  };

  return (
    <div className="container mx-auto py-8 space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-display text-4xl luxury-text-gradient mb-2">Settings</h1>
            <p className="text-gray-400">Configure your DevSkyy platform preferences</p>
          </div>
          <Button
            onClick={saveSettings}
            disabled={saveStatus === 'saving'}
            className="bg-rose-500 hover:bg-rose-600"
          >
            {saveStatus === 'saving' ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : saveStatus === 'success' ? (
              <>
                <Check className="mr-2 h-4 w-4" />
                Saved
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save All
              </>
            )}
          </Button>
        </div>

        {saveStatus === 'error' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3"
          >
            <AlertCircle className="h-5 w-5 text-red-400" />
            <p className="text-red-400">{errorMessage}</p>
          </motion.div>
        )}

        <Tabs defaultValue="wordpress" className="space-y-6">
          <TabsList className="bg-gray-800 border border-gray-700">
            <TabsTrigger value="wordpress" className="data-[state=active]:bg-rose-500/20">
              <Globe className="mr-2 h-4 w-4" />
              WordPress
            </TabsTrigger>
            <TabsTrigger value="vercel" className="data-[state=active]:bg-rose-500/20">
              <Zap className="mr-2 h-4 w-4" />
              Vercel
            </TabsTrigger>
            <TabsTrigger value="autonomous" className="data-[state=active]:bg-rose-500/20">
              <Bot className="mr-2 h-4 w-4" />
              Autonomous
            </TabsTrigger>
            <TabsTrigger value="ui" className="data-[state=active]:bg-rose-500/20">
              <Palette className="mr-2 h-4 w-4" />
              UI Preferences
            </TabsTrigger>
            <TabsTrigger value="system" className="data-[state=active]:bg-rose-500/20">
              <SettingsIcon className="mr-2 h-4 w-4" />
              System
            </TabsTrigger>
          </TabsList>

          {/* WordPress Settings */}
          <TabsContent value="wordpress" className="space-y-6">
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle>WordPress Connection</CardTitle>
                <CardDescription>Configure WordPress REST API credentials</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="wp-url">WordPress URL</Label>
                  <Input
                    id="wp-url"
                    type="url"
                    value={settings.wordpress.url}
                    onChange={(e) => updateSetting('wordpress', 'url', e.target.value)}
                    placeholder="https://skyyrose.co"
                    className="bg-gray-800 border-gray-700"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="wp-key">Consumer Key</Label>
                  <div className="flex gap-2">
                    <Input
                      id="wp-key"
                      type={showSecrets['wp-key'] ? 'text' : 'password'}
                      value={settings.wordpress.consumerKey}
                      onChange={(e) => updateSetting('wordpress', 'consumerKey', e.target.value)}
                      placeholder="ck_xxxxxxxxxxxxx"
                      className="bg-gray-800 border-gray-700 flex-1"
                    />
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => toggleSecret('wp-key')}
                      className="border-gray-700"
                    >
                      {showSecrets['wp-key'] ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="wp-secret">Consumer Secret</Label>
                  <div className="flex gap-2">
                    <Input
                      id="wp-secret"
                      type={showSecrets['wp-secret'] ? 'text' : 'password'}
                      value={settings.wordpress.consumerSecret}
                      onChange={(e) => updateSetting('wordpress', 'consumerSecret', e.target.value)}
                      placeholder="cs_xxxxxxxxxxxxx"
                      className="bg-gray-800 border-gray-700 flex-1"
                    />
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => toggleSecret('wp-secret')}
                      className="border-gray-700"
                    >
                      {showSecrets['wp-secret'] ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                <Separator className="bg-gray-800" />

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Auto-Sync</Label>
                    <p className="text-sm text-gray-400">
                      Automatically sync Round Table results to WordPress
                    </p>
                  </div>
                  <Switch
                    checked={settings.wordpress.autoSync}
                    onCheckedChange={(checked) => updateSetting('wordpress', 'autoSync', checked)}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Vercel Settings */}
          <TabsContent value="vercel" className="space-y-6">
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle>Vercel Integration</CardTitle>
                <CardDescription>Configure Vercel deployment settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="vercel-project">Project ID</Label>
                  <Input
                    id="vercel-project"
                    value={settings.vercel.projectId}
                    onChange={(e) => updateSetting('vercel', 'projectId', e.target.value)}
                    placeholder="prj_xxxxxxxxxxxxx"
                    className="bg-gray-800 border-gray-700"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="vercel-org">Organization ID</Label>
                  <Input
                    id="vercel-org"
                    value={settings.vercel.orgId}
                    onChange={(e) => updateSetting('vercel', 'orgId', e.target.value)}
                    placeholder="team_xxxxxxxxxxxxx"
                    className="bg-gray-800 border-gray-700"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="vercel-token">API Token</Label>
                  <div className="flex gap-2">
                    <Input
                      id="vercel-token"
                      type={showSecrets['vercel-token'] ? 'text' : 'password'}
                      value={settings.vercel.apiToken}
                      onChange={(e) => updateSetting('vercel', 'apiToken', e.target.value)}
                      placeholder="xxxxxxxxxxxxx"
                      className="bg-gray-800 border-gray-700 flex-1"
                    />
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => toggleSecret('vercel-token')}
                      className="border-gray-700"
                    >
                      {showSecrets['vercel-token'] ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Autonomous Settings */}
          <TabsContent value="autonomous" className="space-y-6">
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle>Autonomous Agent Configuration</CardTitle>
                <CardDescription>Control autonomous operations and self-healing behavior</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Enable Autonomous Operations</Label>
                    <p className="text-sm text-gray-400">
                      Allow agents to operate autonomously
                    </p>
                  </div>
                  <Switch
                    checked={settings.autonomous.enabled}
                    onCheckedChange={(checked) => updateSetting('autonomous', 'enabled', checked)}
                  />
                </div>

                <Separator className="bg-gray-800" />

                <div className="space-y-2">
                  <Label htmlFor="circuit-threshold">Circuit Breaker Threshold</Label>
                  <Input
                    id="circuit-threshold"
                    type="number"
                    value={settings.autonomous.circuitBreakerThreshold}
                    onChange={(e) =>
                      updateSetting('autonomous', 'circuitBreakerThreshold', parseInt(e.target.value))
                    }
                    className="bg-gray-800 border-gray-700"
                  />
                  <p className="text-sm text-gray-400">
                    Number of failures before circuit breaker opens
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="retry-attempts">Retry Attempts</Label>
                  <Input
                    id="retry-attempts"
                    type="number"
                    value={settings.autonomous.retryAttempts}
                    onChange={(e) =>
                      updateSetting('autonomous', 'retryAttempts', parseInt(e.target.value))
                    }
                    className="bg-gray-800 border-gray-700"
                  />
                  <p className="text-sm text-gray-400">
                    Maximum number of retry attempts for failed operations
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="retry-delay">Retry Delay (ms)</Label>
                  <Input
                    id="retry-delay"
                    type="number"
                    value={settings.autonomous.retryDelay}
                    onChange={(e) =>
                      updateSetting('autonomous', 'retryDelay', parseInt(e.target.value))
                    }
                    className="bg-gray-800 border-gray-700"
                  />
                  <p className="text-sm text-gray-400">
                    Initial delay before first retry (exponential backoff applies)
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* UI Preferences */}
          <TabsContent value="ui" className="space-y-6">
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle>UI Preferences</CardTitle>
                <CardDescription>Customize the look and feel of DevSkyy</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="theme">Theme</Label>
                  <select
                    id="theme"
                    value={settings.ui.theme}
                    onChange={(e) => updateSetting('ui', 'theme', e.target.value)}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md"
                  >
                    <option value="dark">Dark</option>
                    <option value="light">Light</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="typography">Typography</Label>
                  <select
                    id="typography"
                    value={settings.ui.typography}
                    onChange={(e) => updateSetting('ui', 'typography', e.target.value)}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md"
                  >
                    <option value="playfair">Playfair Display (Luxury)</option>
                    <option value="inter">Inter (Modern)</option>
                    <option value="system">System Default</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="accent">Accent Color</Label>
                  <div className="flex gap-2">
                    <Input
                      id="accent"
                      type="color"
                      value={settings.ui.accentColor}
                      onChange={(e) => updateSetting('ui', 'accentColor', e.target.value)}
                      className="w-20 h-10 bg-gray-800 border-gray-700"
                    />
                    <Input
                      type="text"
                      value={settings.ui.accentColor}
                      onChange={(e) => updateSetting('ui', 'accentColor', e.target.value)}
                      className="bg-gray-800 border-gray-700 flex-1"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* System Settings */}
          <TabsContent value="system" className="space-y-6">
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle>System Configuration</CardTitle>
                <CardDescription>Advanced system settings and performance tuning</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="timeout">API Timeout (ms)</Label>
                  <Input
                    id="timeout"
                    type="number"
                    value={settings.system.apiTimeout}
                    onChange={(e) =>
                      updateSetting('system', 'apiTimeout', parseInt(e.target.value))
                    }
                    className="bg-gray-800 border-gray-700"
                  />
                  <p className="text-sm text-gray-400">
                    Maximum time to wait for API responses
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="concurrent">Max Concurrent Requests</Label>
                  <Input
                    id="concurrent"
                    type="number"
                    value={settings.system.maxConcurrentRequests}
                    onChange={(e) =>
                      updateSetting('system', 'maxConcurrentRequests', parseInt(e.target.value))
                    }
                    className="bg-gray-800 border-gray-700"
                  />
                  <p className="text-sm text-gray-400">
                    Maximum number of simultaneous API requests
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="log-level">Log Level</Label>
                  <select
                    id="log-level"
                    value={settings.system.logLevel}
                    onChange={(e) => updateSetting('system', 'logLevel', e.target.value)}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md"
                  >
                    <option value="debug">Debug</option>
                    <option value="info">Info</option>
                    <option value="warn">Warning</option>
                    <option value="error">Error</option>
                  </select>
                  <p className="text-sm text-gray-400">
                    Minimum severity level for logging
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
}
