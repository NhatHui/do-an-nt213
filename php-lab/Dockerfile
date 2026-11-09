FROM php:8.2-apache
RUN apt-get update && apt-get install -y --no-install-recommends libpng-dev libjpeg-dev \
    && docker-php-ext-configure gd --with-jpeg \
    && docker-php-ext-install -j"$(nproc)" gd \
    && rm -rf /var/lib/apt/lists/*
COPY apache-ufu.conf /etc/apache2/sites-available/000-default.conf
COPY php.ini /usr/local/etc/php/conf.d/b22.ini
COPY src/ /var/www/html/
COPY storage_outside_webroot/ /var/www/storage_outside_webroot/
RUN mkdir -p /var/www/html/uploads/sub /var/www/storage_outside_webroot \
    && chown -R www-data:www-data /var/www/html/uploads /var/www/storage_outside_webroot \
    && chmod 0755 /var/www/html/uploads \
    && chmod 0750 /var/www/storage_outside_webroot