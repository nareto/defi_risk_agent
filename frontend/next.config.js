/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  async rewrites() {
    return [
      { source: "/run", destination: "http://backend:8000/run" },
      {
        source: "/events/:task_id",
        destination: "http://backend:8000/events/:task_id",
      },
    ];
  },
};

module.exports = nextConfig;
