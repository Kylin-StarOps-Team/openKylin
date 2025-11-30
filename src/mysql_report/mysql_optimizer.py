import subprocess
import configparser
import json
import pymysql
import os
from detection_counter import get_next_detection_number, get_detection_files

def collect_system_config():
    
    """收集系统级配置"""
    config = {
        "file_handles": int(subprocess.getoutput("ulimit -n")),
        "swappiness": int(subprocess.getoutput("cat /proc/sys/vm/swappiness")),
        "io_scheduler": subprocess.getoutput("cat /sys/block/sda/queue/scheduler | awk -F'[' '{print $2}' | awk -F']' '{print $1}'")
    }
    print("done config")
    return config

def collect_mysql_config():
    """收集MySQL配置（自定义解析my.cnf及include文件，避免configparser报错）"""
    import glob
    config_data = {}
    section = None
    
    def parse_file(file_path):
        nonlocal section
        if not os.path.exists(file_path):
            return
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('!includedir'):
                    dir_path = line.split(' ', 1)[1]
                    for subfile in sorted(glob.glob(os.path.join(dir_path, '*.cnf'))):
                        parse_file(subfile)
                elif line.startswith('!include'):
                    subfile = line.split(' ', 1)[1]
                    parse_file(subfile)
                elif line.startswith('[') and line.endswith(']'):
                    section = line.strip('[]')
                    if section not in config_data:
                        config_data[section] = {}
                elif '=' in line and section:
                    key, value = line.split('=', 1)
                    config_data[section][key.strip()] = value.strip()
                # 其他行忽略

    parse_file('/etc/mysql/my.cnf')

    conn = pymysql.connect(host='127.0.0.1', user='root',password='@Buaa123456')
    with conn.cursor() as cursor:
        cursor.execute("SHOW VARIABLES")
        variables = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.execute("SHOW GLOBAL STATUS")
        status = {row[0]: row[1] for row in cursor.fetchall()}
    print("done mysql config")
    return {
        "config_file": config_data,
        "runtime_variables": variables,
        "global_status": status
    }

def run_percona_analysis(detection_number):
    """运行Percona分析工具"""
    files = get_detection_files(detection_number)
    
    print("start percona analysis")
    subprocess.run(f"pt-mysql-summary --host=127.0.0.1 --port=3306 --user=root --password='@Buaa123456' > {files['summary']}", shell=True)
    print("done pt-mysql-summary")
    subprocess.run(f"pt-variable-advisor --host=127.0.0.1 --port=3306 --user=root --password='@Buaa123456' > {files['advisor']}", shell=True)
    print("done pt-variable-advisor")
    # subprocess.run("pt-config-diff /etc/mysql/my.cnf /opt/mysql-best-practice.cnf > config_diff.txt", shell=True)
    # print("done percona analysis")
    return {
        "summary": open(files['summary']).read(),
        "advisor": open(files['advisor']).read(),
        "summary_file": files['summary'],
        "advisor_file": files['advisor']
        # "config_diff": open("config_diff.txt").read()
    }

if __name__ == "__main__":
    # 获取检测编号
    detection_number = get_next_detection_number()
    files = get_detection_files(detection_number)
    
    print(f"开始第 {detection_number} 次MySQL配置检测...")
    
    data = {
        "detection_number": detection_number,
        "system": collect_system_config(),
        "mysql": collect_mysql_config(),
        "analysis": run_percona_analysis(detection_number)
    }
    
    with open(files['optimization_report'], "w") as f:
        json.dump(data, f, indent=2)
    print(f"配置优化报告已生成: {files['optimization_report']}")
    
    # 保存检测信息到文件，供后续脚本使用
    with open("current_detection.json", "w") as f:
        json.dump({"detection_number": detection_number, "files": files}, f, indent=2) 