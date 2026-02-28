#!/bin/bash
# 从 PNG 图片创建 macOS ICNS 图标文件

if [ -z "$1" ]; then
    echo "用法: ./create_icns_icon.sh <input.png>"
    echo "示例: ./create_icns_icon.sh wifi_icon.png"
    exit 1
fi

INPUT_PNG="$1"
OUTPUT_ICNS="${INPUT_PNG%.png}.icns"

if [ ! -f "$INPUT_PNG" ]; then
    echo "❌ 错误: 文件不存在: $INPUT_PNG"
    exit 1
fi

echo "📝 从 $INPUT_PNG 创建 ICNS 图标..."
echo ""

# 创建临时目录
ICONSET="${INPUT_PNG%.png}.iconset"
mkdir -p "$ICONSET"

# 生成各种尺寸的图标
echo "生成图标尺寸..."
sips -z 16 16     "$INPUT_PNG" --out "$ICONSET/icon_16x16.png" > /dev/null 2>&1
sips -z 32 32     "$INPUT_PNG" --out "$ICONSET/icon_16x16@2x.png" > /dev/null 2>&1
sips -z 32 32     "$INPUT_PNG" --out "$ICONSET/icon_32x32.png" > /dev/null 2>&1
sips -z 64 64     "$INPUT_PNG" --out "$ICONSET/icon_32x32@2x.png" > /dev/null 2>&1
sips -z 128 128   "$INPUT_PNG" --out "$ICONSET/icon_128x128.png" > /dev/null 2>&1
sips -z 256 256   "$INPUT_PNG" --out "$ICONSET/icon_128x128@2x.png" > /dev/null 2>&1
sips -z 256 256   "$INPUT_PNG" --out "$ICONSET/icon_256x256.png" > /dev/null 2>&1
sips -z 512 512   "$INPUT_PNG" --out "$ICONSET/icon_256x256@2x.png" > /dev/null 2>&1
sips -z 512 512   "$INPUT_PNG" --out "$ICONSET/icon_512x512.png" > /dev/null 2>&1
sips -z 1024 1024 "$INPUT_PNG" --out "$ICONSET/icon_512x512@2x.png" > /dev/null 2>&1

echo "✅ 图标文件已生成"

# 转换为 ICNS
echo "转换为 ICNS 格式..."
iconutil -c icns "$ICONSET" -o "$OUTPUT_ICNS"

# 清理临时文件
rm -rf "$ICONSET"

echo ""
echo "✅ ICNS 图标创建成功: $OUTPUT_ICNS"
echo ""
echo "文件信息:"
ls -lh "$OUTPUT_ICNS"
