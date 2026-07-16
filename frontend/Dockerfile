FROM node:alpine3.24 as development

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

EXPOSE 5173

# Run Vite with --host so it accepts traffic from outside the container
CMD ["npm", "run", "dev", "--", "--host"]

# Production Build
FROM development AS build
RUN npm run build

# Lightweight Production Web Server
FROM nginx:1.25-alpine AS production

# Remove default Nginx static files
RUN rm -rf /usr/share/nginx/html/*

# Copy build artifacts from build into the Nginx server directory
COPY --from=build /app/dist /usr/share/nginx/html

# Expose HTTP port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]