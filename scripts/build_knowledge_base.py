#!/usr/bin/env python3
"""
构建品牌知识库
- 扫描 knowledge_base/ 下的资料
- 切分文本块
- 生成嵌入向量
- 存入 ChromaDB
"""
import os
import json
import hashlib
from pathlib import Path

def scan_knowledge_base(base_dir):
    """扫描资料目录，返回所有文件路径"""
    files = []
    for ext in ['*.txt', '*.md', '*.pdf', '*.xlsx', '*.mp4', '*.csv']:
        files.extend(Path(base_dir).rglob(ext))
    return [str(f) for f in files]

def extract_text_from_file(filepath):
    """从各类文件中提取文本"""
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext in ['.txt', '.md']:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    elif ext == '.csv':
        import pandas as pd
        df = pd.read_csv(filepath)
        texts = []
        for _, row in df.iterrows():
            texts.append(' | '.join([str(v) for v in row.values if pd.notna(v)]))
        return '\n'.join(texts)
    
    elif ext == '.xlsx':
        import pandas as pd
        df = pd.read_excel(filepath)
        texts = []
        for _, row in df.iterrows():
            texts.append(' | '.join([str(v) for v in row.values if pd.notna(v)]))
        return '\n'.join(texts)
    
    elif ext == '.pdf':
        # 简单PDF解析（需要 pip install PyPDF2）
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(filepath)
            texts = []
            for page in reader.pages:
                texts.append(page.extract_text())
            return '\n'.join(texts)
        except:
            return f"[PDF文件无法解析: {filepath}]"
    
    elif ext == '.mp4':
        # 视频文件只记录元数据
        return f"[视频文件: {os.path.basename(filepath)}]"
    
    return ""

def chunk_text(text, chunk_size=200, overlap=50):
    """将长文本切分成块"""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    
    return chunks

def main():
    BASE_DIR = r"C:\Users\Administrator\.openclaw\workspace\video_production"
    KB_DIR = os.path.join(BASE_DIR, "knowledge_base")
    DB_DIR = os.path.join(BASE_DIR, "vector_db")
    
    print("=" * 60)
    print("构建品牌知识库")
    print("=" * 60)
    
    # 初始化 ChromaDB
    import chromadb
    from sentence_transformers import SentenceTransformer
    
    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_or_create_collection("brand_knowledge")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 扫描文件
    print(f"\n📂 扫描目录: {KB_DIR}")
    files = scan_knowledge_base(KB_DIR)
    print(f"找到 {len(files)} 个文件")
    
    if not files:
        print("⚠️ 没有找到任何资料文件")
        print("请将产品资料(PDF/Excel/视频)放入 knowledge_base/ 目录")
        return
    
    # 处理每个文件
    all_chunks = []
    
    for i, filepath in enumerate(files, 1):
        filename = os.path.basename(filepath)
        print(f"\n[{i}/{len(files)}] 处理: {filename}")
        
        text = extract_text_from_file(filepath)
        
        if not text:
            print(f"  ⚠️ 未能提取文本")
            continue
        
        # 切分文本块
        chunks = chunk_text(text)
        print(f"  切分为 {len(chunks)} 个文本块")
        
        for chunk in chunks:
            all_chunks.append({
                "text": chunk,
                "source": filename,
                "chunk_id": len(all_chunks)
            })
    
    if not all_chunks:
        print("\n⚠️ 没有找到可处理的文本内容")
        return
    
    print(f"\n📊 总共 {len(all_chunks)} 个文本块")
    print("⏳ 正在生成嵌入向量...")
    
    # 批量生成嵌入
    batch_size = 32
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        texts = [c["text"] for c in batch]
        
        embeddings = model.encode(texts)
        ids = [hashlib.md5(c["text"].encode()).hexdigest() for c in batch]
        
        collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            metadatas=[{"source": c["source"]} for c in batch],
            documents=texts
        )
        
        print(f"  已处理 {min(i+batch_size, len(all_chunks))}/{len(all_chunks)}")
    
    print(f"\n✅ 知识库构建完成！")
    print(f"   数据库路径: {DB_DIR}")
    print(f"   Collection: brand_knowledge")
    print(f"   总文本块: {len(all_chunks)}")

if __name__ == "__main__":
    main()
