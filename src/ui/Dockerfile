# =====================================================
# Multi-Stage Dockerfile for React UI (Vite + TypeScript)
# =====================================================

# -----------------------------------------------------
# Stage 1: Build the React application
# -----------------------------------------------------
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments for API URL configuration
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}

# Build the application for production
RUN npm run build

# -----------------------------------------------------
# Stage 2: Serve the application with nginx
# -----------------------------------------------------
FROM nginx:alpine

# Copy built assets from builder stage (Vite outputs to 'build' as configured)
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx configuration for SPA routing and API proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

