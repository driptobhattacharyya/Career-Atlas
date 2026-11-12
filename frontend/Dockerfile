# Career-Atlas frontend — TanStack Start (SSR). The production target is a
# Cloudflare Worker (dist/server + wrangler.json), so an SSR runtime is required;
# static nginx hosting can't serve it. For LOCAL clone-and-run we run the Vite
# dev server (full SSR, HMR). VITE_* are read at runtime from the environment
# (set in docker-compose) and point the app at the local stack.
FROM oven/bun:1
WORKDIR /app
COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile
COPY . .
EXPOSE 5173
CMD ["bun", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
