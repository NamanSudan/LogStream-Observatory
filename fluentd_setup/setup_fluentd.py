# setup_fluentd.py

import os

def create_fluentd_config():
    config_content = '''
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<match application.logs>
  @type clickhouse
  host clickhouse-server
  port 8123
  database logs
  username default
  password ''
  flush_interval 5s
  <buffer>
    @type memory
    chunk_limit_size 8MB
    flush_interval 5s
  </buffer>
</match>
    '''
    os.makedirs('fluentd', exist_ok=True)
    with open('fluentd/fluent.conf', 'w') as file:
        file.write(config_content.strip())
    print("FluentD configuration file 'fluent.conf' created successfully.")

if __name__ == "__main__":
    create_fluentd_config()