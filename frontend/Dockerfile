# TOXMAP Frontend — Development
# Node 22 Alpine + Vite dev server
# Production build (Cloudflare Pages) configured in Phase 7.

FROM node:22-alpine

WORKDIR /app

# Install dependencies
COPY package.json ./
RUN npm install

# Copy source files (volume mount in docker-compose.yml overlays src/ for hot-reload)
COPY . .

# Vite dev server on all interfaces so it's accessible from the host
EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
