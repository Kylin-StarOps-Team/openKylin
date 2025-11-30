#!/bin/bash

# StarOps AI系统监控助手启动脚本
# 
# 使用方法:
#   ./start.sh          # 生产模式启动
#   ./start.sh dev      # 开发模式启动

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 启动StarOps AI系统监控助手..."
echo "📁 当前目录: $SCRIPT_DIR"

# 设置DISPLAY环境变量和X11权限
if [ -z "$DISPLAY" ]; then
    echo "⚠️  DISPLAY环境变量未设置，正在配置..."
    export DISPLAY=:0
    echo "✅ DISPLAY已设置为: $DISPLAY"
fi

# 为root用户设置X11权限
if [ "$EUID" -eq 0 ]; then
    echo "🔧 配置root用户的X11权限..."
    export XAUTHORITY=/run/lightdm/root/:0
    if command -v xhost >/dev/null 2>&1; then
        xhost +local:root >/dev/null 2>&1 && echo "✅ X11权限设置成功" || echo "⚠️  X11权限设置可能失败"
    fi
fi

# 检查是否使用root用户运行
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  警告: 检测到root用户，建议使用普通用户运行以避免权限问题"
    echo "💡 解决方案: su - normaluser 然后重新运行此脚本"
fi

# 设置必要的环境变量
export DISPLAY="${DISPLAY:-:0}"
export ELECTRON_DISABLE_SECURITY_WARNINGS=true
export ELECTRON_ENABLE_LOGGING=true

# 检查X11显示
if [ -z "$DISPLAY" ]; then
    echo "❌ 错误: 未设置DISPLAY环境变量"
    echo "💡 请设置: export DISPLAY=:0"
    exit 1
fi

# 测试X11连接
if ! timeout 5 xset q &>/dev/null; then
    echo "⚠️  警告: X11显示服务可能不可用"
    echo "💡 如果是远程连接，请确保启用了X11转发: ssh -X username@hostname"
fi

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到Node.js，请先安装Node.js"
    exit 1
fi

# 检查npm是否安装
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到npm，请先安装npm"
    exit 1
fi

# 检查依赖是否安装
if [ ! -d "node_modules" ]; then
    echo "📦 正在安装依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 错误: 依赖安装失败"
        exit 1
    fi
fi

# 检查Python是否可用
if ! command -v python3 &> /dev/null; then
    echo "⚠️  警告: 未找到python3，AI功能可能无法正常工作"
fi

# 检查核心文件是否存在
required_files=("main.js" "index.html" "floating-ball.html" "styles.css" "renderer.js")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 错误: 缺少核心文件 $file"
        exit 1
    fi
done

# 检查文件权限
echo "🔍 检查文件权限..."
if [ ! -r "node_modules/electron/dist/libGLESv2.so" ]; then
    echo "⚠️  警告: GPU库文件权限可能有问题，将使用软件渲染"
fi

echo "✅ 环境检查通过"

# 显示启动信息
echo "🌟 启动参数:"
echo "   - 禁用GPU硬件加速 (--disable-gpu)"
echo "   - 禁用沙箱 (--no-sandbox)"  
echo "   - 禁用setuid沙箱 (--disable-setuid-sandbox)"
echo "   - 禁用共享内存 (--disable-dev-shm-usage)"

# 根据参数选择启动模式
if [ "$1" = "dev" ]; then
    echo "🔧 以开发模式启动..."
    npm run dev
else
    echo "🎯 以生产模式启动..."
    npm start
fi
