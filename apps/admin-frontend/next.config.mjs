/** @type {import('next').NextConfig} */
// Same dev detection as server.js (`NODE_ENV !== 'production'`).
const isDev = process.env.NODE_ENV !== 'production';

const nextConfig = {
  images: {
    unoptimized: true
  },
  // The Admin Observatory had no /api proxy at all, so any relative /api call
  // resolved against :3001 instead of the FastAPI gateway on :8000.
  ...(isDev ? {
    async rewrites() {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ];
    },
  } : {}),
};

export default nextConfig;
