FROM fluent/fluentd:v1.14-1

USER root

# Install FluentD ClickHouse plugin
RUN gem install fluent-plugin-clickhouse --no-document

# Copy configuration file
COPY fluent.conf /fluentd/etc/

# Set permissions
RUN chown fluent /fluentd/etc/fluent.conf

USER fluent