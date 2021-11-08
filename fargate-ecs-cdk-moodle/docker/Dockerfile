FROM --platform=linux/amd64 moodlehq/moodle-php-apache:7.4
RUN mkdir -p /var/www/moodle/data && chown www-data /var/www/moodle/data && \
    mkdir -p /var/www/moodle/temp && chown www-data /var/www/moodle/temp && \
    mkdir -p /var/www/moodle/cache && chown www-data /var/www/moodle/cache && \
    mkdir -p /var/www/local && chown www-data /var/www/local
RUN curl --location https://github.com/moodle/moodle/archive/refs/tags/v3.11.2.tar.gz --output code.tar.gz
RUN tar -x -f code.tar.gz --strip-components=1 && rm -r code.tar.gz
COPY config-dist.php config.php