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
COPY package.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application for production
RUN npm run build

# -----------------------------------------------------
# Stage 2: Serve the application with nginx
# -----------------------------------------------------
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx configuration (if needed)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

