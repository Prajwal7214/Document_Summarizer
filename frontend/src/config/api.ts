// Backend API base URL — reads from .env (VITE_API_URL), falls back to localhost
export const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
