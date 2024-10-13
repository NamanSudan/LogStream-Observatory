import time
import random
import socket
import json

def generate_logs():
    # Create a TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 9001))   # Match the address in vector.yaml

    log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    sources = ['auth', 'payment', 'search', 'profile']

    try:
        while True:
            log_level = random.choice(log_levels)
            source_module = random.choice(sources)
            message = f"Sample log message from {source_module} at level {log_level}"
            event_time = time.strftime('%Y-%m-%d %H:%M:%S')
            log_entry = {
                'timestamp': event_time,
                'level': log_level,
                'message': message,
                'source': source_module
            }

            log_json = json.dumps(log_entry)
            print(f"Sending log: {log_json}")  # Add this line
            # Send the JSON log over the socket
            sock.sendall((log_json + '\n').encode('utf-8'))
            time.sleep(1)
    except (KeyboardInterrupt, BrokenPipeError, ConnectionResetError) as e:
        print(f"Log generation stopped due to error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    generate_logs()
