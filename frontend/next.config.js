/** @type {import('next').NextConfig} */

// Import the bundle analyzer plugin
const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

const nextConfig = {
  // Enable React's Strict Mode for better development practices and to identify potential problems.
  reactStrictMode: true,

  // Configuration for Next.js Image Optimization
  images: {
    // Defines a list of allowed remote domains for optimized images.
    // This is crucial for security and performance when using external image sources.
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.example.com", // Placeholder: Add specific hostnames for APIs like BetterDoctor, Practo, etc.
        port: "",
        pathname: "/**",
      },
      // Example for BetterDoctor (if they use a specific CDN)
      // {
      //   protocol: 'https',
      //   hostname: 'asset.betterdoctor.com',
      // },
      // Example for Practo
      // {
      //   protocol: 'https',
      //   hostname: 's3-ap-southeast-1.amazonaws.com',
      //   pathname: '/practo-images/**',
      // }
    ],
  },
  
  // Experimental features can be enabled here.
  // For example, to enable the Turbopack bundler for faster local development:
  // experimental: {
  //   turbo: true,
  // },

  // Ensures that the output directory is correctly configured for standalone deployment.
  output: "standalone",
};

// Wrap the Next.js configuration with the bundle analyzer to enable it conditionally.
// To use it, run: `ANALYZE=true npm run build`
module.exports = withBundleAnalyzer(nextConfig);
