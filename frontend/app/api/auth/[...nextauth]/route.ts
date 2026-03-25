/**
 * NextAuth.js v4 API Route Handler
 *
 * Handles all /api/auth/* requests (signIn, signOut, session, csrf, etc.)
 */

import NextAuth from 'next-auth';
import { authOptions } from '@/lib/auth';

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
