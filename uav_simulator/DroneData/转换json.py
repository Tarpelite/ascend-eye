#!/usr/bin/env python3
"""
flight_data_all.json 数据解析和转换测试脚本

用途：
1. 测试解析现有的 flight_data_all.json 文件
2. 验证数据格式是否符合 run_simulator.py 的需求
3. 转换和清理数据格式
4. 生成标准格式的 JSON 文件
"""

import json
import os
from pathlib import Path

def load_original_data(file_path="uav_simulator/DroneData/flight_data_all.json"):
    """加载原始的 flight_data_all.json 文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ 成功加载文件: {file_path}")
        print(f"📊 包含 {len(data)} 个端口的数据")
        return data
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        return None
    except Exception as e:
        print(f"❌ 加载文件失败: {e}")
        return None

def clean_markdown_json(data_string):
    """清理包含 markdown 标记的 JSON 字符串"""
    if not isinstance(data_string, str):
        return data_string
    
    # 移除 markdown 代码块标记
    clean_data = data_string.strip()
    
    # 移除开头的 ```json
    if clean_data.startswith('```json'):
        clean_data = clean_data[7:]
    elif clean_data.startswith('```'):
        clean_data = clean_data[3:]
    
    # 移除结尾的 ```
    if clean_data.endswith('```'):
        clean_data = clean_data[:-3]
    
    # 清理首尾空白
    clean_data = clean_data.strip()
    
    return clean_data

def parse_flight_data(port, raw_data):
    """解析单个端口的飞行数据"""
    print(f"\n🛩️  解析端口 {port} 的数据...")
    
    try:
        # 清理 markdown 标记
        clean_data = clean_markdown_json(raw_data)
        
        # 显示清理后的数据预览
        print(f"📝 清理后的数据预览 (前100字符):")
        print(f"   {clean_data[:100]}...")
        
        # 解析 JSON
        flight_data = json.loads(clean_data)
        
        # 验证数据格式
        if not isinstance(flight_data, list):
            print(f"❌ 数据格式错误: 期望数组，得到 {type(flight_data)}")
            return None
        
        print(f"✅ 解析成功! 包含 {len(flight_data)} 个数据点")
        
        # 验证数据点格式
        if len(flight_data) > 0:
            first_point = flight_data[0]
            required_fields = ['timestamp', 'latitude', 'longitude', 'altitude', 'vx', 'vy', 'vz', 'roll', 'pitch', 'yaw']
            
            missing_fields = [field for field in required_fields if field not in first_point]
            if missing_fields:
                print(f"⚠️  缺少字段: {missing_fields}")
            else:
                print(f"✅ 数据格式验证通过")
                
            # 显示第一个数据点
            print(f"🎯 第一个数据点:")
            for key, value in first_point.items():
                print(f"   {key}: {value}")
        
        return flight_data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        print(f"📋 问题数据: {clean_data[:200]}...")
        return None
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return None

def validate_data_consistency(parsed_data):
    """验证解析后数据的一致性"""
    print(f"\n🔍 验证数据一致性...")
    
    total_points = 0
    port_summary = {}
    
    for port, data in parsed_data.items():
        if data is not None:
            port_summary[port] = {
                'count': len(data),
                'time_range': (data[0]['timestamp'], data[-1]['timestamp']) if data else (None, None),
                'altitude_range': (min(p['altitude'] for p in data), max(p['altitude'] for p in data)) if data else (None, None)
            }
            total_points += len(data)
        else:
            port_summary[port] = {'count': 0, 'time_range': (None, None), 'altitude_range': (None, None)}
    
    print(f"📊 总数据点: {total_points}")
    print(f"📋 各端口数据概览:")
    
    for port, summary in port_summary.items():
        print(f"   端口 {port}:")
        print(f"     数据点数: {summary['count']}")
        if summary['count'] > 0:
            print(f"     时间范围: {summary['time_range'][0]} ~ {summary['time_range'][1]}")
            print(f"     高度范围: {summary['altitude_range'][0]} ~ {summary['altitude_range'][1]}")
    
    return port_summary

def convert_to_standard_format(parsed_data):
    """转换为标准格式（直接的 JSON 数组，而不是字符串）"""
    print(f"\n🔄 转换为标准格式...")
    
    standard_data = {}
    
    for port, data in parsed_data.items():
        if data is not None:
            # 确保端口号为字符串类型（与原文件格式一致）
            standard_data[str(port)] = data
            print(f"✅ 端口 {port}: 转换完成 ({len(data)} 个数据点)")
        else:
            print(f"❌ 端口 {port}: 跳过（数据为空）")
    
    return standard_data

def save_converted_data(data, output_file="flight_data_standard.json"):
    """保存转换后的标准格式数据"""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 标准格式数据已保存到: {output_file}")
        
        # 显示文件大小
        file_size = os.path.getsize(output_file)
        print(f"📁 文件大小: {file_size} 字节 ({file_size/1024:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")
        return False

def test_simulator_compatibility(data):
    """测试与 run_simulator.py 的兼容性"""
    print(f"\n🧪 测试 run_simulator.py 兼容性...")
    
    # 模拟 run_simulator.py 中的解析逻辑
    def simulate_parsing(port_data):
        """模拟 run_simulator.py 中的数据处理"""
        try:
            if isinstance(port_data, str):
                # 如果是字符串，尝试解析
                clean_data = clean_markdown_json(port_data)
                data_json = json.loads(clean_data)
            else:
                # 如果已经是对象，直接使用
                data_json = port_data
            
            return data_json, True
        except Exception as e:
            return None, False
    
    success_count = 0
    
    for port, port_data in data.items():
        parsed, success = simulate_parsing(port_data)
        
        if success and parsed:
            print(f"✅ 端口 {port}: 兼容性测试通过 ({len(parsed)} 个数据点)")
            success_count += 1
        else:
            print(f"❌ 端口 {port}: 兼容性测试失败")
    
    print(f"📊 兼容性测试结果: {success_count}/{len(data)} 个端口通过")
    
    return success_count == len(data)

def main():
    """主函数"""
    print("🚀 flight_data_all.json 数据解析和转换工具")
    print("=" * 80)
    
    # 步骤1: 加载原始数据
    print("📂 步骤1: 加载原始数据")
    original_data = load_original_data()
    
    if not original_data:
        print("❌ 无法加载原始数据，程序退出")
        return
    
    # 步骤2: 解析各端口数据
    print(f"\n📊 步骤2: 解析各端口数据")
    parsed_data = {}
    
    for port, raw_data in original_data.items():
        parsed_data[port] = parse_flight_data(port, raw_data)
    
    # 步骤3: 验证数据一致性
    print(f"\n🔍 步骤3: 验证数据一致性")
    validate_data_consistency(parsed_data)
    
    # 步骤4: 转换为标准格式
    print(f"\n🔄 步骤4: 转换为标准格式")
    standard_data = convert_to_standard_format(parsed_data)
    
    # 步骤5: 保存标准格式数据
    print(f"\n💾 步骤5: 保存标准格式数据")
    save_success = save_converted_data(standard_data)
    
    # 步骤6: 测试兼容性
    print(f"\n🧪 步骤6: 测试 run_simulator.py 兼容性")
    compatibility = test_simulator_compatibility(original_data)
    
    # 最终总结
    print(f"\n{'='*80}")
    print("📋 转换结果总结:")
    print(f"✅ 原始数据加载: {'成功' if original_data else '失败'}")
    print(f"✅ 数据解析: {'成功' if any(parsed_data.values()) else '失败'}")
    print(f"✅ 格式转换: {'成功' if standard_data else '失败'}")
    print(f"✅ 文件保存: {'成功' if save_success else '失败'}")
    print(f"✅ 兼容性测试: {'通过' if compatibility else '失败'}")
    
    if compatibility:
        print(f"\n🎉 所有测试通过! run_simulator.py 应该可以正常使用数据。")
    else:
        print(f"\n⚠️  存在兼容性问题，建议检查数据格式。")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
