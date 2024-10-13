import os

def create_dockerfile():
    dockerfile_content = '''
FROM fluent/fluentd:v1.14-1

USER root

# Install FluentD ClickHouse plugin
RUN gem install fluent-plugin-clickhouse --no-document

# Copy configuration file
COPY fluent.conf /fluentd/etc/

# Set permissions
RUN chown fluent /fluentd/etc/fluent.conf

USER fluent
    '''
    os.makedirs('fluentd', exist_ok=True)
    with open('fluentd/Dockerfile', 'w') as f:
        f.write(dockerfile_content.strip())
    print("FluentD Dockerfile created successfully.")

if __name__ == "__main__":
    create_dockerfile()