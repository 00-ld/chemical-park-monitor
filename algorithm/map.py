"""Factory map visualization for A* grid-based path planning.

Generates a visual representation of the chemical plant layout with
building obstacles, patrol car positions, and status indicators.
Designed for debugging and system testing.

Typical usage:
    python map.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

# ===================== 1. 地图配置（可直接修改适配你的Web系统）=====================
MAP_WIDTH = 80   # 地图宽度（网格数）
MAP_HEIGHT = 50  # 地图高度（网格数）
# 4个小车点位坐标 (y, x) 对应矩阵行列
CAR_POINTS = {
    1: {"pos": (15, 20), "status": "normal", "color": "#00c853"},  # 正常 绿色
    2: {"pos": (30, 60), "status": "normal", "color": "#00c853"},  # 正常 绿色
    3: {"pos": (22, 38), "status": "error",  "color": "#f44336"},  # 异常 红色
    4: {"pos": (35, 18), "status": "normal", "color": "#00c853"}   # 正常 绿色
}

# ===================== 2. 初始化网格地图（A*算法专用矩阵）=====================
grid_map = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=int)  # 0=道路

# ---------------------- 绘制工厂建筑（障碍物=1）复刻你的布局 ----------------------
# 中心大型厂区（异常点3所在建筑）
grid_map[18:28, 30:48] = 1
# 左上厂区（点位1旁车间）
grid_map[10:22, 10:28] = 1
# 右下厂区（点位2旁车间）
grid_map[25:38, 55:75] = 1
# 左下厂区（点位4旁车间）
grid_map[30:45, 8:25] = 1
# 右侧配套厂房
grid_map[8:20, 50:78] = 1
# 顶部厂房
grid_map[5:15, 22:45] = 1
# 底部厂房群
grid_map[40:48, 10:55] = 1

# 标记小车点位（2=关键节点）
for idx, info in CAR_POINTS.items():
    y, x = info["pos"]
    grid_map[y, x] = 2

# ===================== 3. 可视化地图（和你的Web页面风格一致）=====================
plt.figure(figsize=(14, 9), facecolor="#e8f5e9")
# 配色：白色=道路，灰色=建筑，彩色=小车点
cmap = plt.cm.colors.ListedColormap(["#ffffff", "#90a4ae", "#ff5722"])
plt.imshow(grid_map, cmap=cmap, vmin=0, vmax=2)

# 标注4个小车点位+文字
for idx, info in CAR_POINTS.items():
    y, x = info["pos"]
    # 画圆点
    plt.scatter(x, y, s=600, color=info["color"], edgecolors="white", linewidth=3)
    # 标注编号+状态
    plt.text(x, y, f"{idx}\n{info['status']}",
             ha="center", va="center", fontsize=12, fontweight="bold", color="white")

# 地图美化（适配Web系统）
plt.title("化工厂智能车巡检地图 | A*算法网格版", fontsize=16, pad=20, fontweight="bold")
plt.xticks([])  # 隐藏坐标轴（Web无坐标）
plt.yticks([])
plt.tight_layout()

# ===================== 4. 输出关键数据（对接Web系统）=====================
print("=== 地图网格矩阵（A*算法直接使用）===")
print(f"地图尺寸: {MAP_HEIGHT}行 × {MAP_WIDTH}列")
print(f"数值定义: 0=可通行  1=建筑障碍  2=小车点位")
print("\n=== 4个小车点位坐标（y行, x列）===")
for idx, info in CAR_POINTS.items():
    print(f"小车{idx}: {info['pos']} | 状态: {info['status']}")

# 显示地图
plt.show()




