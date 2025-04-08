# backend/infer.py
def run_inference():
    """
    模拟推理过程，返回高亮的推理路径
    实际可调用 AnyBURL 或其它模型接口
    """
    # 假设推理返回节点ID列表
    inferred_paths = [
        {"highlight": [1, 2, 3]},   # 一个推理路径的节点ID
        {"highlight": [4, 5]}       # 另一个推理路径
    ]
    return inferred_paths

# 直接调试
if __name__ == '__main__':
    paths = run_inference()
    print(paths)
