FROM node:22-slim
WORKDIR /app
ENV NODE_ENV=production DATA_DIR=/data TRUST_PROXY=true
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY src ./src
COPY public ./public
# Runs as root so it can always write to the host's mounted disk at /data.
RUN mkdir -p /data
EXPOSE 3000
CMD ["node", "--disable-warning=ExperimentalWarning", "src/server.js"]
