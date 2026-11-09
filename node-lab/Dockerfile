FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY server.js ./
COPY views ./views
COPY public ./public
COPY storage_outside_webroot ./storage_outside_webroot
RUN mkdir -p public/uploads storage_outside_webroot && adduser -D appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 3000
CMD ["node", "server.js"]