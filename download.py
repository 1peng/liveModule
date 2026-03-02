from modelscope import snapshot_download
# 下载 Qwen2-0.5B-Instruct 到本地 ./models/Qwen2-0.5B-Instruct 目录
model_dir = snapshot_download('BAAI/bge-small-zh-v1.5', cache_dir='./models')
print(f"模型已下载到: {model_dir}")