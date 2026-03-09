import os
import sys

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import snapshot_download

MODELS = {
    "BAAI/bge-small-zh-v1.5": "checkpoints/BAAI/bge-small-zh-v1.5",
    # "Qwen/Qwen2.5-1.5B-Instruct": "checkpoints/Qwen/Qwen2.5-1.5B-Instruct",
}


def download_model(model_id: str, local_dir: str):
    print(f"\n{'=' * 50}")
    print(f"下载模型: {model_id}")
    print(f"目标目录: {local_dir}")
    print("=" * 50)

    if os.path.exists(local_dir) and os.listdir(local_dir):
        print(f"✅ 模型已存在，跳过下载: {local_dir}")
        return local_dir

    os.makedirs(os.path.dirname(local_dir), exist_ok=True)

    try:
        model_path = snapshot_download(
            repo_id=model_id,
            local_dir=local_dir,
        )
        print(f"\n✅ 下载完成: {model_path}")
        return model_path
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        raise


def main():
    print("\n" + "=" * 50)
    print("RAG 模型下载工具")
    print(f"镜像源: {os.environ.get('HF_ENDPOINT', 'default')}")
    print("=" * 50)

    os.makedirs("checkpoints", exist_ok=True)

    success_count = 0
    fail_count = 0

    for model_id, local_dir in MODELS.items():
        try:
            download_model(model_id, local_dir)
            success_count += 1
        except Exception as e:
            print(f"跳过模型 {model_id}: {e}")
            fail_count += 1

    print("\n" + "=" * 50)
    print("下载完成")
    print(f"成功: {success_count}, 失败: {fail_count}")
    print("=" * 50)


if __name__ == "__main__":
    main()
