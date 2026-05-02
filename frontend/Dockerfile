# ── Stage 1: Build ────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first (layer caching)
COPY package.json package-lock.json ./
RUN npm ci --prefer-offline

# Copy source and build
COPY . .
RUN npm run build


# ── Stage 2: Production ──────────────────────────────────────────────────
FROM node:20-alpine AS production

WORKDIR /app

# Copy package files and install production-only deps
COPY package.json package-lock.json ./
RUN npm ci --prefer-offline --production

# Copy built Next.js output from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.js ./

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --spider -q http://localhost:3000 || exit 1

CMD ["npm", "start"]
