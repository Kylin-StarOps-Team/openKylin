#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试检测编号功能
"""

import os
import sys
import shutil
from detection_counter import get_next_detection_number, get_current_detection_number, get_detection_files

def test_detection_counter():
    """测试检测计数器功能"""
    print("🧪 测试检测计数器功能...")
    
    # 备份现有的计数器文件
    counter_file = "detection_counter.json"
    backup_file = "detection_counter.json.backup"
    if os.path.exists(counter_file):
        shutil.copy(counter_file, backup_file)
        os.remove(counter_file)
    
    try:
        # 测试首次检测
        print("📝 测试首次检测...")
        next_num = get_next_detection_number()
        print(f"   首次检测编号: {next_num}")
        assert next_num == 1, f"期望编号为1，实际为{next_num}"
        
        # 测试获取当前编号
        current_num = get_current_detection_number()
        print(f"   当前检测编号: {current_num}")
        assert current_num == 1, f"期望当前编号为1，实际为{current_num}"
        
        # 测试第二次检测
        print("📝 测试第二次检测...")
        next_num = get_next_detection_number()
        print(f"   第二次检测编号: {next_num}")
        assert next_num == 2, f"期望编号为2，实际为{next_num}"
        
        # 测试文件名生成
        print("📝 测试文件名生成...")
        files = get_detection_files(2)
        expected_files = {
            'optimization_report': 'mysql_optimization_report_2.json',
            'suggestions': 'mysql_suggestions_2.json',
            'html_report': 'mysql_optimization_report_2.html',
            'summary': 'mysql_summary_2.txt',
            'advisor': 'variable_advisor_2.txt'
        }
        
        for key, expected in expected_files.items():
            actual = files.get(key)
            print(f"   {key}: {actual}")
            assert actual == expected, f"期望{key}为{expected}，实际为{actual}"
        
        print("✅ 检测计数器功能测试通过！")
        return True
        
    finally:
        # 恢复备份文件
        if os.path.exists(counter_file):
            os.remove(counter_file)
        if os.path.exists(backup_file):
            shutil.move(backup_file, counter_file)

def test_file_separation():
    """测试文件分离功能"""
    print("\n🧪 测试文件分离功能...")
    
    # 模拟多次检测
    for i in range(1, 4):
        files = get_detection_files(i)
        print(f"📝 第{i}次检测文件:")
        for key, filename in files.items():
            print(f"   {key}: {filename}")
        
        # 验证文件名包含检测编号
        assert str(i) in files['optimization_report'], f"优化报告文件名应包含编号{i}"
        assert str(i) in files['suggestions'], f"建议文件名应包含编号{i}"
        assert str(i) in files['html_report'], f"HTML报告文件名应包含编号{i}"
        assert str(i) in files['summary'], f"摘要文件名应包含编号{i}"
        assert str(i) in files['advisor'], f"建议文件名应包含编号{i}"
    
    print("✅ 文件分离功能测试通过！")
    return True

def main():
    """主测试函数"""
    print("🚀 开始测试MySQL检测编号功能\n")
    
    test_results = []
    
    # 测试检测计数器
    test_results.append(test_detection_counter())
    
    # 测试文件分离
    test_results.append(test_file_separation())
    
    # 总结测试结果
    print(f"\n📊 测试结果总结:")
    print(f"✅ 通过测试: {sum(test_results)}/{len(test_results)}")
    
    if all(test_results):
        print("🎉 所有测试通过！MySQL检测编号功能正常工作")
        print("\n💡 功能说明:")
        print("• 每次运行mysql_optimizer.py会自动分配新的检测编号")
        print("• 所有生成的文件都会带有检测编号后缀")
        print("• 文件不会被覆盖，历史检测结果都会保留")
        print("• 同一次检测的所有文件编号保持一致")
    else:
        print("❌ 部分测试失败，请检查实现")
    
    return all(test_results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)