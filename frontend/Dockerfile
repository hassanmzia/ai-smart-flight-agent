# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
# Use npm ci if lock file exists, otherwise use npm install
RUN if [ -f package-lock.json ]; then npm ci; else npm install && npm install --package-lock-only; fi

# Copy source code
COPY . .

# Set environment variables for build
ARG VITE_API_URL=http://108.48.39.238:3090
ARG VITE_WS_URL=ws://108.48.39.238:3090/ws
ARG VITE_MCP_URL=http://108.48.39.238:3090/mcp

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL
ENV VITE_MCP_URL=$VITE_MCP_URL

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 3090

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3090 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
