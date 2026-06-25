import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

const SETTINGS_FILE = path.join(process.cwd(), 'data', 'settings.json');

async function getSettings() {
    try {
        const data = await fs.readFile(SETTINGS_FILE, 'utf-8');
        return JSON.parse(data);
    } catch (error) {
        // Default settings if file doesn't exist
        return {
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
        };
    }
}

async function isAuthenticated() {
    const session = await getServerSession(authOptions);
    return Boolean(session?.user?.email);
}

export async function GET(request: NextRequest) {
    if (!(await isAuthenticated())) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const settings = await getSettings();
    return NextResponse.json(settings);
}

export async function POST(req: NextRequest) {
    if (!(await isAuthenticated())) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        const settings = await req.json();
        
        // Ensure data directory exists
        await fs.mkdir(path.dirname(SETTINGS_FILE), { recursive: true });
        
        // Write to file
        await fs.writeFile(SETTINGS_FILE, JSON.stringify(settings, null, 2));
        
        return NextResponse.json(settings);
    } catch (error) {
        console.error('Failed to save settings:', error);
        return NextResponse.json(
            { error: 'Failed to save settings' },
            { status: 500 }
        );
    }
}
