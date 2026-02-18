/**
 * Centralized configuration object to manage environment variables.
 * This provides type safety and a single source of truth across the application.
 */

interface Config {
    apiUrl: string;
    isDevelopment: boolean;
    isProduction: boolean;
    appName: string;
    appVersion: string;
}

const config: Config = {
    apiUrl: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
    isDevelopment: import.meta.env.MODE === 'development',
    isProduction: import.meta.env.MODE === 'production',
    appName: import.meta.env.VITE_APP_NAME || 'NLP Database Chatbot',
    appVersion: '1.0.0',
};

export default config;
