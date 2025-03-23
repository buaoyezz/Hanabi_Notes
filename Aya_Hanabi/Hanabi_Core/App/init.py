# App包初始化
from .optimizer import AppOptimizer

# 创建应用优化器实例
app_Optimizer = AppOptimizer()

# 启动加速
try:
    app_Optimizer.accelerate_startup()
    print("应用加速初始化完成")
except Exception as e:
    print(f"应用加速初始化失败: {e}")
