export const API_URL = (() => {
    const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    try {
        new URL(url);
        return url;
    } catch {
        console.error('Invalid API_URL configuration');
        return 'http://localhost:8000';
    }
})();
