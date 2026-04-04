---
name: Brand-Analyzer
description: 根据用户问题从品牌知识库(ChromaDB)检索相关信息，支持产品卖点、竞品分析、风格定位等问答。
trigger: 分析品牌|产品定位|竞品是谁|我们的风格是什么|卖点是什么|产品有哪些
---

## Instructions

1. **接收用户问题**
   - 解析用户输入中的产品关键词
   - 如未提供关键词，从问题中推断

2. **向量检索**
   - 使用 sentence-transformers (all-MiniLM-L6-v2) 将问题转为向量
   - 查询 ChromaDB collection `brand_knowledge`，返回最相似的5个文本块

3. **生成回答**
   - 将检索结果作为上下文
   - 调用 MiniMax 文本模型生成回答
   - 回答需基于检索到的知识，不可胡说

4. **输出格式**
   ```
   📚 品牌知识检索结果：
   
   **参考来源：** [文件名]
   
   **回答：** [基于知识库的回答]
   ```

## 数据库路径
- ChromaDB: `C:\Users\Administrator\.openclaw\workspace\video_production\vector_db`
- Collection: `brand_knowledge`

## 检索函数

```python
def retrieve_brand_knowledge(query, top_k=5):
    """从品牌知识库检索相关信息"""
    import chromadb
    from sentence_transformers import SentenceTransformer
    
    client = chromadb.PersistentClient(
        path="C:/Users/Administrator/.openclaw/workspace/video_production/vector_db"
    )
    collection = client.get_or_create_collection("brand_knowledge")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    query_embedding = model.encode(query)
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )
    
    return results
```

## 使用示例

**用户：** "我们的产品主要卖点是什么？"

**输出：**
```
📚 品牌知识检索结果：

**参考来源：** 产品资料.md, 卖点分析.xlsx

**回答：** 
根据品牌知识库，轻上产品的主要卖点包括：
1. 天然健康：0糖0脂0添加
2. 东南亚优质原料：甄选越南椰子
3. 场景多元：运动补水/日常饮用/健身人群
...
```
