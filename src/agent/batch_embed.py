import os
import json
import argparse
from src.agent.storage import Storage
from src.agent.rag import EmbeddingProvider, build_terms, embed_text
from pathlib import Path

folder = r" "

def read_text_file(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def collect_files(folder):
    files = []
    for root, dirs, filenames in os.walk(folder):
        for fn in filenames:
            if fn.lower().endswith(('.txt', '.md', '.html')):
                files.append(os.path.join(root, fn))
    files.sort()
    return files


def main(folder, db_path, assessment_id_offset=1000000, provider_name=None):
    storage = Storage(db_path)
    storage.init()
    ep = EmbeddingProvider(provider=provider_name)

    files = collect_files(folder)
    if not files:
        print("没有找到可处理的文件：", folder)
        return

    texts = [read_text_file(p) for p in files]


    # Batch embedding first
    print("尝试批量嵌入：provider =", ep.provider)
    embeddings = ep.embed_batch(texts)

    # Fallback to per-doc embed
    if embeddings is None:
        print("批量嵌入失败，切换为逐文档嵌入…")
        embeddings = []
        for t in texts:
            v = ep.embed_text(t)
            embeddings.append(v)

    # Prepare database items
    items = []
    for idx, (path, vec, txt) in enumerate(zip(files, embeddings, texts)):
        aid = assessment_id_offset + idx
        terms = build_terms(txt)
        items.append((aid, json.dumps(terms, ensure_ascii=False), json.dumps(vec, ensure_ascii=False)))

    print(f"正在写入{len(items)}条embeddings到 {db_path} ...")
    storage.save_embeddings_batch(items)

    print("完成！当前embeddings总数 =", storage.count_embeddings())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', type=str, required=True, help="选择要读取的文本文件目录")
    parser.add_argument('--db', type=str, default='rag_storage.db', help="指定存embeddings的SQLite文件")
    parser.add_argument('--offset', type=int, default=1e8, help="生成assessment_id偏移，防止冲突")
    parser.add_argument('--provider', type=str, default=None, help="指定 embedding 模型来源[openai/baai/local]")
    args = parser.parse_args()
    main(args.dir, args.db, args.offset, args.provider)

