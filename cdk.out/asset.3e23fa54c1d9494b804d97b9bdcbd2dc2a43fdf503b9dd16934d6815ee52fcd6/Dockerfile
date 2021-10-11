FROM moodlehq/moodle-php-apache:7.4
RUN mkdir -p /var/www/moodle/data && chown www-data /var/www/moodle/data && \
    mkdir -p /var/www/moodle/cache \
    mkdir -p /var/www/moodle/temp \
    mkdir -p /var/www/moodle/local 
WORKDIR /var/www/html
RUN curl --location https://github.com/moodle/moodle/archive/refs/tags/v3.11.2.tar.gz --output code.tar.gz
RUN tar -x -f code.tar.gz --strip-components=1 && rm -r code.tar.gz
COPY config-dist.php config.php
# RUN git clone https://github.com/catalyst/moodle-local_aws local/aws
# RUN git clone https://github.com/catalyst/moodle-tool_objectfs.git admin/tool/objectfs
EXPOSE 80
EXPOSE 443