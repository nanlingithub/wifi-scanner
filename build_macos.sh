#!/bin/bash
# WiFi专业工具 macOS 打包脚本
# 版本: 1.7.2

echo "=================================="
echo "WiFi专业工具 macOS 打包脚本"
echo "版本: 1.7.2"
echo "=================================="
echo ""

# 检查 Python 版本
echo "检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "当前 Python 版本: $python_version"

# 检查必要的依赖
echo ""
echo "检查依赖包..."

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "升级 pip..."
pip install --upgrade pip

# 安装依赖
echo ""
echo "安装依赖包..."
pip install -r requirements.txt

# 安装 PyInstaller
echo ""
echo "安装 PyInstaller..."
pip install pyinstaller

# 清理旧的构建文件
echo ""
echo "清理旧的构建文件..."
rm -rf build dist *.spec

# 创建图标文件（如果不存在）
if [ ! -f "wifi_icon.icns" ]; then
    echo ""
    echo "警告: 未找到 wifi_icon.icns 图标文件"
    echo "将尝试从 wifi_icon.ico 或 wifi_icon.png 转换"
    
    # 尝试从 PNG 创建 ICNS
    if [ -f "wifi_icon.png" ]; then
        echo "从 PNG 创建 ICNS..."
        mkdir -p wifi_icon.iconset
        sips -z 16 16     wifi_icon.png --out wifi_icon.iconset/icon_16x16.png
        sips -z 32 32     wifi_icon.png --out wifi_icon.iconset/icon_16x16@2x.png
        sips -z 32 32     wifi_icon.png --out wifi_icon.iconset/icon_32x32.png
        sips -z 64 64     wifi_icon.png --out wifi_icon.iconset/icon_32x32@2x.png
        sips -z 128 128   wifi_icon.png --out wifi_icon.iconset/icon_128x128.png
        sips -z 256 256   wifi_icon.png --out wifi_icon.iconset/icon_128x128@2x.png
        sips -z 256 256   wifi_icon.png --out wifi_icon.iconset/icon_256x256.png
        sips -z 512 512   wifi_icon.png --out wifi_icon.iconset/icon_256x256@2x.png
        sips -z 512 512   wifi_icon.png --out wifi_icon.iconset/icon_512x512.png
        sips -z 1024 1024 wifi_icon.png --out wifi_icon.iconset/icon_512x512@2x.png
        iconutil -c icns wifi_icon.iconset
        rm -rf wifi_icon.iconset
        echo "ICNS 图标创建成功"
    fi
fi

# 执行打包
echo ""
echo "开始打包..."
pyinstaller build_macos.spec

# 检查打包结果
if [ -d "dist/WiFi专业工具.app" ]; then
    echo ""
    echo "=================================="
    echo "✅ 打包成功！"
    echo "=================================="
    echo ""
    echo "应用位置: dist/WiFi专业工具.app"
    echo "应用大小: $(du -sh dist/WiFi专业工具.app | awk '{print $1}')"
    echo ""
    echo "安装说明:"
    echo "1. 将 WiFi专业工具.app 拖动到应用程序文件夹"
    echo "2. 首次运行需要右键点击，选择'打开'"
    echo "3. 授予必要的权限（位置服务）"
    echo ""
    echo "注意事项:"
    echo "- macOS 10.13 (High Sierra) 或更高版本"
    echo "- 需要授予位置权限才能扫描WiFi"
    echo "- 某些功能可能需要管理员权限"
    echo ""
    
    # 创建 DMG 镜像（可选）
    echo "是否创建 DMG 安装镜像？ (y/n)"
    read -r create_dmg
    if [ "$create_dmg" = "y" ] || [ "$create_dmg" = "Y" ]; then
        echo ""
        echo "创建 DMG 镜像..."
        hdiutil create -volname "WiFi专业工具" -srcfolder "dist/WiFi专业工具.app" -ov -format UDZO "dist/WiFi专业工具_v1.7.2.dmg"
        echo "✅ DMG 镜像创建成功: dist/WiFi专业工具_v1.7.2.dmg"
    fi
else
    echo ""
    echo "=================================="
    echo "❌ 打包失败！"
    echo "=================================="
    echo ""
    echo "请检查上方的错误信息"
    echo "常见问题:"
    echo "1. 检查是否安装了所有依赖包"
    echo "2. 检查 Python 版本（推荐 3.8+）"
    echo "3. 检查是否有足够的磁盘空间"
    exit 1
fi

# 退出虚拟环境
deactivate

echo ""
echo "=================================="
echo "打包流程完成"
echo "=================================="
