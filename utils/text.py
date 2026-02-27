# 文本处理工具函数

def format_message(message, **kwargs):
    """格式化消息，替换占位符"""
    for key, value in kwargs.items():
        message = message.replace(f'{{{key}}}', str(value))
    return message

def get_random_message(messages):
    """从消息列表中随机选择一条"""
    import random
    if not messages:
        return ""
    return random.choice(messages)

def get_next_message(messages, index):
    """按顺序获取下一条消息"""
    if not messages:
        return "", 0
    next_index = (index + 1) % len(messages)
    return messages[next_index], next_index
