// Backend API base URL — reads from .env (VITE_API_URL), defaults to relative path for Nginx proxy
export const API_URL = import.meta.env.VITE_API_URL !== undefined ? import.meta.env.VITE_API_URL : '';
