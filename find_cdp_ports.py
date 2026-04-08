# -*- coding: utf-8 -*-
import socket
import threading
import time

found = []

def check_port(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex(('127.0.0.1', port))
        if result == 0:
            found.append(port)
            # Check if it's CDP
            try:
                s.send(b'GET /json HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
                resp = s.recv(4096, socket.MSG_PEEK)
                resp_str = resp.decode('utf-8', errors='replace')[:200]
                print(f"  Port {port}: {resp_str[:100]}")
            except:
                pass
        s.close()
    except:
        pass

# Common CDP ports
targets = []
for base in range(9200, 9300):
    targets.append(base)

print("Scanning common CDP ports...")
threads = []
for port in targets:
    t = threading.Thread(target=check_port, args=(port,))
    t.start()
    threads.append(t)
    time.sleep(0.05)

for t in threads:
    t.join()

print(f"\nFound {len(found)} open ports: {sorted(found)}")
