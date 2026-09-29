/** @type {import('next').NextConfig} */
// Must match the dev detection in server-https.js and package.json, which use
// `NODE_ENV !== 'production'`. This previously tested
// `NODE_ENV === 'development'`, which is false whenever the variable is unset --
// so the custom server ran in dev mode while Next still applied
// `output: 'export'` and skipped the /api proxy, breaking every relative /api
// call and every deep link.
const isDev = process.env.NODE_ENV !== 'production';

const nextConfig = {
  // Static export only for a real production build.
  ...(isDev ? {} : {
    output: 'export',
    trailingSlash: true,
  }),
  images: {
    unoptimized: true
  },
  // Proxy /api/* calls to the FastAPI backend on port 8000.
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
