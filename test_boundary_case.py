
import sys
sys.path.append('/app/PythonRoboticsfork')

from PathPlanning.AStar import a_star as m

m.show_animation = False

# 设置障碍物
ox, oy = [], []
for i in range(0, 20):
    ox.append(i)
    oy.append(10.0)  # 一条水平线障碍物

# 测试1: 终点落在障碍物上
print("测试1: 终点落在障碍物上")
try:
    a_star = m.AStarPlanner(ox, oy, 2.0, 1.0)
    rx, ry = a_star.planning(0.0, 0.0, 10.0, 10.0)  # 终点在障碍物上
    print(f"路径长度: {len(rx)}")
    print(f"路径: {list(zip(rx, ry))}")
except Exception as e:
    print(f"错误: {e}")

print("\n" + "="*50 + "\n")

# 测试2: 起点落在障碍物上
print("测试2: 起点落在障碍物上")
try:
    a_star = m.AStarPlanner(ox, oy, 2.0, 1.0)
    rx, ry = a_star.planning(10.0, 10.0, 0.0, 0.0)  # 起点在障碍物上
    print(f"路径长度: {len(rx)}")
    print(f"路径: {list(zip(rx, ry))}")
except Exception as e:
    print(f"错误: {e}")
