from sentence_transformers import SentenceTransformer
import numpy as np
import os
import torch
import gradio as gr
import faiss

# ======================
# 配置
# ======================
VECTOR_DB_PATH = "faiss_rag_db"
EMBED_MODEL = "./models/BAAI/bge-small-zh-v1.5"
LLM_MODEL = "./models/Qwen/Qwen2-0.5B-Instruct"
KNOWLEDGE_FOLDER = "data"

# ======================
# 向量模型
# ======================
embed_model = SentenceTransformer(EMBED_MODEL)

def text2vec(text: str) -> np.ndarray:
    return embed_model.encode(text)

# ======================
# 文件读取：txt md pdf docx xlsx
# ======================
def read_text_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

def read_pdf(path):
    try:
        import PyPDF2
        text = ""
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t
        return text
    except:
        return ""

def read_docx(path):
    try:
        from docx import Document
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs])
    except:
        return ""

def read_excel(path):
    try:
        import pandas as pd
        df = pd.read_excel(path, dtype=str).fillna("")
        return df.to_string(index=False)
    except:
        return ""

def load_file(path):
    ext = path.lower().split(".")[-1]
    if ext in ["txt", "md"]:
        return read_text_file(path)
    elif ext == "pdf":
        return read_pdf(path)
    elif ext == "docx":
        return read_docx(path)
    elif ext in ["xls", "xlsx"]:
        return read_excel(path)
    return ""

# ======================
# 加载文件夹所有文档
# ======================
def load_all_docs(folder=KNOWLEDGE_FOLDER):
    if not os.path.exists(folder):
        os.mkdir(folder)
    docs = []
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            txt = load_file(path)
            if txt and len(txt.strip()) > 10:
                docs.append({"file": name, "content": txt})
    return docs

# ======================
# 文本切分
# ======================
def split_text(text, max_len=350):
    chunks = []
    while len(text) > max_len:
        chunks.append(text[:max_len])
        text = text[max_len:]
    if text:
        chunks.append(text)
    return chunks

# ======================
# 向量库
# ======================
class FAISSVectorDB:
    def __init__(self, path):
        self.path = path
        self.index = None
        self.metadata = []
    
    def add(self, vector, metadata):
        if self.index is None:
            dimension = vector.shape[0]
            self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array([vector]))
        self.metadata.append(metadata)
    
    def build(self):
        pass
    
    def save(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if self.index is not None:
            faiss.write_index(self.index, os.path.join(self.path, "index.faiss"))
        import pickle
        with open(os.path.join(self.path, "metadata.pkl"), "wb") as f:
            pickle.dump(self.metadata, f)
    
    def load(self):
        import pickle
        try:
            self.index = faiss.read_index(os.path.join(self.path, "index.faiss"))
        except:
            self.index = None
        with open(os.path.join(self.path, "metadata.pkl"), "rb") as f:
            self.metadata = pickle.load(f)
    
    def search(self, query_vector, top_k=2):
        if self.index is None or len(self.metadata) == 0:
            return []
        distances, indices = self.index.search(np.array([query_vector]), top_k)
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                result = type('obj', (object,), {'metadata': self.metadata[idx], 'distance': distances[0][i]})
                results.append(result)
        return results

def get_vector_db(docs):
    if os.path.exists(VECTOR_DB_PATH):
        db = FAISSVectorDB(VECTOR_DB_PATH)
        db.load()
        return db

    db = FAISSVectorDB(VECTOR_DB_PATH)
    for doc in docs:
        for chunk in split_text(doc["content"]):
            vec = text2vec(chunk)
            db.add(vec, metadata={"file": doc["file"], "text": chunk})
    db.build()
    db.save()
    return db

# ======================
# 本地大模型
# ======================
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
llm_model = AutoModelForCausalLM.from_pretrained(
    LLM_MODEL,
    torch_dtype=torch.float32,
    device_map="cuda"
)

def generate_answer(context, question):
    prompt = f"""
请根据下面的资料回答问题，不要编造。
资料：
{context}

问题：{question}
回答：
""".strip()

    # Use a simpler tokenization approach
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids
    input_ids = input_ids.to(llm_model.device)

    out = llm_model.generate(
        input_ids,
        max_new_tokens=300,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id
    )
    return tokenizer.decode(out[0][len(input_ids[0]):], skip_special_tokens=True).strip()

# ======================
# RAG 问答（供界面调用）
# ======================
def rag_chat(question):
    if not question.strip():
        return "请输入问题", ""
    
    if not docs:
        return "请先在 data 文件夹中添加文档", ""
    
    q_vec = text2vec(question)
    results = db.search(q_vec, top_k=2)
    context = "\n".join([r.metadata["text"] for r in results])
    answer = generate_answer(context, question)

    source = "\n".join([f"- {r.metadata['file']}" for r in results])
    return answer, f"参考来源：\n{source}"

# ======================
# 初始化全局库
# ======================
print("正在加载文档...")
docs = load_all_docs()
if not docs:
    print(f"请把文件放入 {KNOWLEDGE_FOLDER} 文件夹！")
else:
    print(f"加载文档数：{len(docs)}")

print("加载向量库...")
db = get_vector_db(docs)
print("系统准备完成！启动界面...")

# ======================
# Gradio 可视化界面
# ======================
with gr.Blocks(title="本地RAG知识库") as demo:
    gr.Markdown("# 🏆 本地私人知识库问答助手（Zvec+RAG）")
    gr.Markdown("支持：txt / md / pdf / docx / xlsx，全程本地运行")
    
    question = gr.Textbox(label="输入你的问题", placeholder="比如：Zvec是什么？RAG怎么用？")
    btn = gr.Button("开始回答", variant="primary")
    
    answer = gr.Textbox(label="🤖 回答", lines=5)
    source = gr.Textbox(label="📄 参考来源", lines=3)
    
    btn.click(rag_chat, inputs=question, outputs=[answer, source])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)