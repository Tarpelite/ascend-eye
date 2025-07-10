#!/usr/bin/env python
"""
Ascend-Eye UAV Simulator 一键测试脚本
同时启动模拟器和测试客户端
"""

import subprocess
import time
import sys
import os
import signal

def signal_handler(sig, frame):
    """处理Ctrl+C信号"""
    print('\n[INFO] 正在关闭所有进程...')
    sys.exit(0)

def main():
    print("=" * 50)
    print("Ascend-Eye UAV Simulator 测试工具")
    print("=" * 50)
    print("\n[INFO] 即将启动:")
    print("  1. 测试客户端 (接收端)")
    print("  2. 无人机模拟器 (发送端)")
    print("\n[INFO] 按 Ctrl+C 退出所有程序\n")
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 检查test.mp4是否存在
    test_video = os.path.join(current_dir, 'test_videos', 'test.mp4')
    if not os.path.exists(test_video):
        print(f"[ERROR] 测试视频不存在: {test_video}")
        # print("[INFO] 请先运行 'python scripts/download_test_video.py' 下载测试视频")
        return
    
    try:
        # 启动测试客户端
        print("[INFO] 启动测试客户端...")
        client_script = os.path.join(current_dir, 'test_client.py')
        client_process = subprocess.Popen(
            [sys.executable, client_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 等待客户端启动
        time.sleep(2)
        
        # 启动模拟器
        print("[INFO] 启动无人机模拟器...")
        simulator_script = os.path.join(current_dir, 'run_simulator.py')
        simulator_process = subprocess.Popen(
            [sys.executable, simulator_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        print("\n[INFO] 系统已启动！")
        print("[INFO] 你应该能看到一个显示视频流的窗口")
        print("[INFO] 在视频窗口中按 'q' 键或按 Ctrl+C 退出\n")
        
        # 监控进程输出
        while True:
            # 检查进程是否还在运行
            if client_process.poll() is not None and simulator_process.poll() is not None:
                break
                
            # 读取并显示输出（非阻塞）
            if simulator_process.poll() is None:
                line = simulator_process.stdout.readline()
                if line:
                    print(f"[模拟器] {line.strip()}")
                    
            if client_process.poll() is None:
                line = client_process.stdout.readline()
                if line:
                    print(f"[客户端] {line.strip()}")
                    
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n[INFO] 收到退出信号...")
    finally:
        # 终止所有进程
        print("[INFO] 正在关闭进程...")
        
        if 'client_process' in locals():
            client_process.terminate()
            client_process.wait()
            
        if 'simulator_process' in locals():
            simulator_process.terminate()
            simulator_process.wait()
            
        print("[INFO] 测试完成！")

if __name__ == '__main__':
    main()