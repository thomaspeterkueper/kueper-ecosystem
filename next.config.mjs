/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: "/api/status",
          destination: "/api/status-public",
        },
      ],
    };
  },
};

export default nextConfig;
