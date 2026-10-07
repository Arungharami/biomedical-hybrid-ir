"""Offline educational TF-IDF example. This is not an NFCorpus experiment."""
from biomedical_ir.tfidf import TfidfRetriever

def main():
    corpus = {
        "nutrition": "Dietary fiber and whole grains support nutrition.",
        "cardiology": "Cardiac imaging helps assess heart function.",
        "microbiology": "Bacterial cultures identify microorganisms.",
    }
    query = "dietary fiber"
    ranking = TfidfRetriever().fit(corpus).rank(query, top_k=3)
    print("Educational example using three hand-written documents; no benchmark metrics.")
    print(f"Query: {query}")
    for doc_id, score in ranking:
        print(f"{doc_id}: {score:.6f}")

if __name__ == "__main__":
    main()
