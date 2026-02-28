"""
将PNG图片转换为ICO图标文件
"""
from PIL import Image
import sys

def convert_to_ico(input_path, output_path='wifi_icon.ico'):
    """将图片转换为多尺寸ICO文件"""
    try:
        # 打开图片
        img = Image.open(input_path)
        
        # 确保是RGBA模式（支持透明）
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 生成多个尺寸的图标（Windows推荐）
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        # 保存为ICO文件
        img.save(output_path, format='ICO', sizes=icon_sizes)
        
        print(f"✅ 图标转换成功: {output_path}")
        print(f"   支持尺寸: {', '.join([f'{w}x{h}' for w, h in icon_sizes])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else 'wifi_icon.ico'
        convert_to_ico(input_file, output_file)
    else:
        print("使用方法: python convert_icon.py <输入图片> [输出ICO文件名]")
        print("示例: python convert_icon.py wifi.png wifi_icon.ico")
