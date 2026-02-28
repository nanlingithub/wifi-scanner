"""
生成专业的WiFi分析工具图标 - 美化增强版
"""
from PIL import Image, ImageDraw
import math

def generate_wifi_icon(size=256):
    """生成WiFi分析工具图标 - 增强版"""
    # 创建透明背景
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 配色方案 - 鲜艳蓝色系
    colors = {
        'primary': (30, 144, 255),      # 道奇蓝
        'secondary': (65, 105, 225),    # 皇家蓝
        'accent': (0, 191, 255),        # 深天蓝
        'light': (135, 206, 250),       # 天蓝色
        'dark': (25, 25, 112),          # 午夜蓝
    }
    
    # 绘制渐变背景圆
    center_x, center_y = size // 2, size // 2
    radius = size // 2 - 5
    
    # 多层背景营造深度感
    for i in range(8, 0, -1):
        alpha = int(255 * (i / 8) * 0.3)
        r = 5 + (size - 10) * (i / 8)
        offset = (size - r) / 2
        draw.ellipse(
            [offset, offset, offset + r, offset + r],
            fill=(240, 248, 255, alpha)
        )
    
    # 外圈装饰 - 加粗
    draw.ellipse(
        [5, 5, size-5, size-5],
        outline=colors['light'],
        width=6
    )
    
    # WiFi信号波纹 - 加粗并增加层次
    wifi_center_x = center_x
    wifi_center_y = int(center_y * 1.25)
    
    # 绘制WiFi波纹阴影（增强立体感）
    for i, (arc_radius, offset) in enumerate([
        (radius * 0.75, 3),
        (radius * 0.55, 2),
        (radius * 0.35, 1),
    ]):
        bbox_shadow = [
            wifi_center_x - arc_radius + offset,
            wifi_center_y - arc_radius + offset,
            wifi_center_x + arc_radius + offset,
            wifi_center_y + arc_radius + offset
        ]
        draw.arc(
            bbox_shadow,
            start=200,
            end=340,
            fill=(0, 0, 0, 40),
            width=18 + i * 2
        )
    
    # 绘制WiFi波纹主体（从外到内，加粗）
    for i, (arc_radius, color_key, width) in enumerate([
        (radius * 0.75, 'light', 20),
        (radius * 0.55, 'accent', 22),
        (radius * 0.35, 'primary', 24),
    ]):
        bbox = [
            wifi_center_x - arc_radius,
            wifi_center_y - arc_radius,
            wifi_center_x + arc_radius,
            wifi_center_y + arc_radius
        ]
        draw.arc(
            bbox,
            start=200,
            end=340,
            fill=colors[color_key],
            width=width
        )
    
    # 绘制WiFi中心点（加大并添加光晕）
    dot_radius = size // 15
    
    # 光晕效果
    for r in range(dot_radius + 10, dot_radius, -2):
        alpha = int(100 * ((r - dot_radius) / 10))
        draw.ellipse(
            [wifi_center_x - r, wifi_center_y - r, wifi_center_x + r, wifi_center_y + r],
            fill=(*colors['primary'], alpha)
        )
    
    # 中心点主体
    draw.ellipse(
        [wifi_center_x - dot_radius, wifi_center_y - dot_radius,
         wifi_center_x + dot_radius, wifi_center_y + dot_radius],
        fill=colors['primary']
    )
    
    # 高光效果
    highlight_radius = dot_radius // 2
    draw.ellipse(
        [wifi_center_x - dot_radius // 2, wifi_center_y - dot_radius // 2,
         wifi_center_x - dot_radius // 2 + highlight_radius,
         wifi_center_y - dot_radius // 2 + highlight_radius],
        fill=(255, 255, 255, 100)
    )
    
    # 绘制分析元素 - 波形图（右下角，增强版）
    waveform_x = int(size * 0.62)
    waveform_y = int(size * 0.68)
    waveform_width = int(size * 0.3)
    waveform_height = int(size * 0.2)
    
    # 波形图阴影
    draw.rectangle(
        [waveform_x + 2, waveform_y + 2,
         waveform_x + waveform_width + 2, waveform_y + waveform_height + 2],
        fill=(0, 0, 0, 30)
    )
    
    # 波形图背景
    draw.rectangle(
        [waveform_x, waveform_y, waveform_x + waveform_width, waveform_y + waveform_height],
        fill=(255, 255, 255, 220),
        outline=colors['primary'],
        width=4
    )
    
    # 绘制波形线
    points = []
    steps = 10
    wave_heights = [0.3, 0.6, 0.4, 0.8, 0.5, 0.9, 0.6, 0.7, 0.4, 0.5, 0.3]
    
    for i in range(steps + 1):
        x = waveform_x + (i * waveform_width // steps)
        y = waveform_y + waveform_height - int(waveform_height * wave_heights[i] * 0.8)
        points.append((x, y))
    
    # 波形填充区域
    fill_points = [(waveform_x, waveform_y + waveform_height)] + points + \
                  [(waveform_x + waveform_width, waveform_y + waveform_height)]
    draw.polygon(fill_points, fill=(*colors['accent'], 60))
    
    # 波形线（加粗）
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=colors['accent'], width=4)
    
    # 数据点（加大）
    for point in points:
        draw.ellipse(
            [point[0] - 4, point[1] - 4, point[0] + 4, point[1] + 4],
            fill=colors['primary'],
            outline=(255, 255, 255),
            width=2
        )
    
    # 绘制雷达扫描效果（左上角，增强版）
    radar_x = int(size * 0.15)
    radar_y = int(size * 0.15)
    radar_size = int(size * 0.2)
    
    # 雷达背景圆
    draw.ellipse(
        [radar_x, radar_y, radar_x + radar_size, radar_y + radar_size],
        fill=(255, 255, 255, 200)
    )
    
    # 雷达同心圆（加粗）
    radar_center_x = radar_x + radar_size // 2
    radar_center_y = radar_y + radar_size // 2
    
    for r_ratio in [1.0, 0.66, 0.33]:
        r = int(radar_size * r_ratio / 2)
        draw.ellipse(
            [radar_center_x - r, radar_center_y - r,
             radar_center_x + r, radar_center_y + r],
            outline=colors['accent'],
            width=3
        )
    
    # 雷达扫描扇形（增强）
    angle = 45
    for offset_angle in [0, 10, 20]:
        end_x = radar_center_x + int((radar_size // 2) * math.cos(math.radians(angle + offset_angle)))
        end_y = radar_center_y + int((radar_size // 2) * math.sin(math.radians(angle + offset_angle)))
        alpha = int(150 * (1 - offset_angle / 20))
        draw.line(
            [radar_center_x, radar_center_y, end_x, end_y],
            fill=(*colors['primary'], alpha),
            width=4
        )
    
    # 雷达中心点
    draw.ellipse(
        [radar_center_x - 4, radar_center_y - 4,
         radar_center_x + 4, radar_center_y + 4],
        fill=colors['primary']
    )
    
    return img

def main():
    """生成图标主函数"""
    print("🎨 正在生成专业WiFi分析工具图标（美化增强版）...")
    
    # 生成256x256的PNG图标
    icon = generate_wifi_icon(256)
    
    # 保存PNG文件
    png_path = 'wifi_icon.png'
    icon.save(png_path, 'PNG')
    print(f"✅ PNG图标已生成: {png_path}")
    
    # 生成多尺寸ICO文件
    print("\n🔄 正在生成ICO文件...")
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    # 保存为ICO文件
    ico_path = 'wifi_icon.ico'
    icon.save(ico_path, format='ICO', sizes=icon_sizes)
    print(f"✅ ICO图标已生成: {ico_path}")
    print(f"   支持尺寸: {', '.join([f'{w}x{h}' for w, h in icon_sizes])}")
    
    print("\n🎉 图标生成完成！")
    print(f"\n📊 美化特点:")
    print(f"   • 鲜艳蓝色配色 (道奇蓝 #1E90FF + 皇家蓝)")
    print(f"   • 加粗WiFi信号波纹 (20-24px)")
    print(f"   • 立体阴影效果")
    print(f"   • 增强波形分析图 (渐变填充)")
    print(f"   • 雷达扫描同心圆")
    print(f"   • 光晕与高光效果")
    print(f"   • 数据点白色描边")
    print(f"\n📁 生成文件:")
    print(f"   • wifi_icon.png (256x256)")
    print(f"   • wifi_icon.ico (多尺寸)")

if __name__ == '__main__':
    main()
