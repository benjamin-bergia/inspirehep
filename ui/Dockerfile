FROM node:lts-jessie as build-stage
WORKDIR /usr/src/app
ENV PATH /usr/src/app/node_modules/.bin:$PATH
COPY package.json yarn.lock /usr/src/app/
RUN yarn install
COPY . /usr/src/app
RUN yarn run build


FROM nginx:1.17-alpine as base
EXPOSE 8080
COPY docker/nginx/config/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build-stage /usr/src/app/build /usr/share/nginx/html


FROM alekzonder/puppeteer as test
WORKDIR /app/ui-tests
ENTRYPOINT ["yarn"]
CMD ["test"]
COPY --from=build-stage /usr/src/app /app
RUN yarn install
