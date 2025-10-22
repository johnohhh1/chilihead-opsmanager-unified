/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: 'http://localhost:8002/:path*',
      },
    ]
  },
  // Increase timeout for AI model requests (Ollama can be slow)
  experimental: {
    proxyTimeout: 300000, // 5 minutes
  },
  // Increase server-side timeout
  serverRuntimeConfig: {
    timeout: 300000,
  },
}

module.exports = nextConfig
