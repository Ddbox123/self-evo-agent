import datetime

def print_evolution_time():
    """打印当前系统时间的进化功能"""
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"这是我进化后的新功能！当前时间是：{current_time}")

# 测试调用
if __name__ == "__main__":
    print_evolution_time()
