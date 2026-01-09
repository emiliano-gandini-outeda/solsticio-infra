# Etapa 1: build
FROM node:20-alpine AS build

WORKDIR /app

# Copiar package.json y lock
COPY package.json package-lock.json ./ 

# Instalar dependencias
RUN npm ci

# Copiar todo el código y hacer build
COPY . .
RUN npm run build

# Etapa 2: nginx
FROM nginx:alpine

# Copiar build a nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar entrypoint que genera runtime-config.js
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# Exponer puerto
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
