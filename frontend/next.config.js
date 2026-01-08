/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use static export for Tauri desktop app
  // Change to "standalone" for Docker/server deployment
  output: process.env.BUILD_MODE === "server" ? "standalone" : "export",

  // Required for static export
  images: {
    unoptimized: true,
  },

  // Disable trailing slashes for cleaner URLs
  trailingSlash: false,

  // Development webpack config
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }
    return config;
  },
};

module.exports = nextConfig;
