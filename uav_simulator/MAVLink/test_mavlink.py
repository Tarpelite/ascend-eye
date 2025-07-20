#!/usr/bin/env python
"""
简单的 MAVLink UDP 通信测试工具
用于验证 MAVLink 消息通过 UDP 端口是否能正常收发
"""

import sys
import time
from pymavlink import mavutil

def test_sender(host='127.0.0.1', port=14550):
    """MAVLink 发送端"""
    print(f"发送 MAVLink 心跳消息到 udp://{host}:{port}")
    master = mavutil.mavlink_connection(f'udpout:{host}:{port}')

    for i in range(5):
        # 发送心跳消息，参数按需修改
        master.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_GENERIC,
            mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            0, 0, 0
        )
        print(f"发送第 {i+1} 个心跳消息")
        time.sleep(1)

    master.close()
    print("发送完成")

def test_receiver(port=14550):
    """MAVLink 接收端"""
    print(f"监听 udp://0.0.0.0:{port}，等待 MAVLink 消息...")
    listener = mavutil.mavlink_connection(f'udpin:0.0.0.0:{port}')
    
    try:
        for i in range(5):
            msg = listener.recv_match(blocking=True, timeout=5)
            if msg:
                print(f"收到消息: {msg.get_type()}，内容: {msg}")
            else:
                print("等待超时，未收到消息")
    except KeyboardInterrupt:
        print("用户中断")
    finally:
        listener.close()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'send':
        test_sender()
    else:
        test_receiver()
