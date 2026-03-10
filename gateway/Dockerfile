FROM node:20-alpine

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev

COPY src ./src

EXPOSE 8080
CMD ["node", "src/server.js"]

USER app
