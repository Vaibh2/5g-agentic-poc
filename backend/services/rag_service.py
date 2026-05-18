"""
RAG Service — Pure-Python TF-IDF similarity search.
No C++ build tools required. Works on Windows, Mac, Linux out of the box.
"""

import json
import math
import re
from pathlib import Path
from collections import Counter

INCIDENTS_FILE = Path(__file__).parent.parent / "data" / "incidents.json"

SEED_INCIDENTS = [
    {
        "id": "inc_001",
        "title": "MTU Misconfiguration - Packet Fragmentation",
        "description": "Routing update changed MTU from 1500 to 9000 without enabling jumbo frame support end-to-end. Caused massive packet fragmentation across SECTOR-3 towers.",
        "symptoms": "Latency spike 900ms, packet loss 22%, CPU 91%",
        "root_cause": "MTU mismatch between core and edge nodes caused fragmentation",
        "resolution": "Reverted MTU to 1500, service restored in 38 seconds",
        "config_change": "network/mtu_settings.tf",
        "impact_duration_minutes": 4,
    },
    {
        "id": "inc_002",
        "title": "BGP Route Flapping - SECTOR-7",
        "description": "BGP failover timeout set too aggressively caused continuous route flapping between primary and backup paths.",
        "symptoms": "Intermittent latency spikes 300-600ms, packet loss 8%",
        "root_cause": "BGP timer misconfiguration in sector_7 routing policy",
        "resolution": "Adjusted failover_timeout from 10s to 30s, stabilized routes",
        "config_change": "network/bgp.tf",
        "impact_duration_minutes": 12,
    },
    {
        "id": "inc_003",
        "title": "CPU Throttle - QoS Policy Overload",
        "description": "New QoS policy introduced excessive deep packet inspection on all traffic, overwhelming CPU on tower controllers.",
        "symptoms": "CPU 96%, throughput dropped 70%, error rate 18%",
        "root_cause": "QoS policy applied DPI universally instead of only priority traffic",
        "resolution": "Rolled back QoS config, scoped DPI to VoNR traffic only",
        "config_change": "network/qos_policy.tf",
        "impact_duration_minutes": 7,
    },
    {
        "id": "inc_004",
        "title": "Null Route Injection - Maintenance Window",
        "description": "Maintenance script accidentally injected null routes into the routing table during off-peak window.",
        "symptoms": "Complete packet loss on 12 towers, latency 9999ms (timeout)",
        "root_cause": "Maintenance script regex matched too broadly, deleted valid routes",
        "resolution": "Emergency rollback via backup config snapshot",
        "config_change": "scripts/maintenance_cleanup.sh",
        "impact_duration_minutes": 18,
    },
]


def _ensure_seed():
    if not INCIDENTS_FILE.exists():
        INCIDENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        INCIDENTS_FILE.write_text(json.dumps(SEED_INCIDENTS, indent=2))


_ensure_seed()


def _tokenize(text: str) -> list:
    return re.findall(r"[a-z0-9]+", text.lower())


def _tf(tokens: list) -> dict:
    counts = Counter(tokens)
    total = len(tokens) or 1
    return {w: c / total for w, c in counts.items()}


def _idf(corpus: list) -> dict:
    n = len(corpus)
    doc_freq = {}
    for doc in corpus:
        for word in set(doc):
            doc_freq[word] = doc_freq.get(word, 0) + 1
    return {w: math.log((n + 1) / (df + 1)) + 1 for w, df in doc_freq.items()}


def _cosine(a: dict, b: dict) -> float:
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[w] * b[w] for w in common)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    return dot / (mag_a * mag_b + 1e-9)


def _build_tfidf(text: str, idf: dict) -> dict:
    tokens = _tokenize(text)
    tf = _tf(tokens)
    return {w: tf[w] * idf.get(w, 1.0) for w in tf}


class RAGService:

    @staticmethod
    def retrieve_similar_incidents(query: str, top_k: int = 3) -> list:
        incidents = json.loads(INCIDENTS_FILE.read_text())
        corpus_texts = [
            f"{inc['title']} {inc['description']} {inc['symptoms']} {inc['root_cause']}"
            for inc in incidents
        ]
        corpus_tokens = [_tokenize(t) for t in corpus_texts]
        idf = _idf(corpus_tokens + [_tokenize(query)])

        query_vec = _build_tfidf(query, idf)
        scored = []
        for inc, text in zip(incidents, corpus_texts):
            doc_vec = _build_tfidf(text, idf)
            score = _cosine(query_vec, doc_vec)
            if score > 0:
                scored.append({**inc, "similarity_score": round(score, 3)})

        return sorted(scored, key=lambda x: x["similarity_score"], reverse=True)[:top_k]

    @staticmethod
    def get_all_incidents() -> list:
        return json.loads(INCIDENTS_FILE.read_text())
