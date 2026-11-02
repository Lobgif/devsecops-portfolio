# syntax=docker/dockerfile:1

# syntax=docker/dockerfile:1
FROM node:20-alpine@sha256:fb4cd12c85ee03686f6af5362a0b0d56d50c58a04632e6c0fb8363f609372293

WORKDIR /app
COPY package*.json ./
RUN chown -R 1000:1000 /app
USER 1000
# Le .npmrc est monté temporairement pour npm install
RUN --mount=type=secret,id=npmrc,target=/home/node/.npmrc,required=true,mode=0400\
    npm install --omit=dev

COPY . .
CMD ["node", "server.js"]