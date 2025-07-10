#!/usr/bin/env python
"""
简单的UDP通信测试工具
用于验证UDP端口是否能正常通信
"""

import socket
import sys
import time

def test_sender(host='127.0.0.1', port=5600):
    """测试发送端"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print(f"发送测试数据到 {host}:{port}")
    for i in range(5):
        message = f"Test message {i}".encode()
        sock.sendto(message, (host, port))
        print(f"发送: {message}")
        time.sleep(1)
    
    sock.close()
    print("发送完成")

def test_receiver(port=5600):
    """测试接收端"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port))
    sock.settimeout(5.0)
    
    print(f"监听端口 {port}...")
    
    try:
        for i in range(5):
            try:
                data, addr = sock.recvfrom(1024)
                print(f"收到来自 {addr} 的数据: {data}")
            except socket.timeout:
                print("超时，未收到数据")
    finally:
        sock.close()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'send':
        test_sender()
    else:
        test_receiver()