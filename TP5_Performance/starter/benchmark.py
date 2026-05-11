"""
TP5 - Benchmark Comparatif NoSQL
Mesurer les performances de Redis, MongoDB, Cassandra, Neo4j
"""
import time
import statistics
import json
from typing import Callable, List, Tuple
import redis
from pymongo import MongoClient
from pymongo import InsertOne
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement, BatchType
import uuid
from neo4j import GraphDatabase

# ─── Utilitaires de mesure ────────────────────────────────────────────────────

def measure_latency(fn: Callable, iterations: int = 1000) -> dict:
    """
    Exécuter fn iterations fois et retourner les statistiques
    """
    latencies = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        latencies.append((time.perf_counter() - start) * 1000)  # en ms
    
    latencies.sort()
    return {
        "mean_ms": statistics.mean(latencies),
        "p50_ms": latencies[int(0.50 * len(latencies))],
        "p95_ms": latencies[int(0.95 * len(latencies))],
        "p99_ms": latencies[int(0.99 * len(latencies))],
        "max_ms": max(latencies),
        "throughput_rps": 1000 / statistics.mean(latencies)
    }


def print_results(name: str, results: dict):
    print(f"\n{'='*50}")
    print(f" {name}")
    print(f"{'='*50}")
    for k, v in results.items():
        print(f"  {k:20s}: {v:.2f}")


# ─── Ex1 : Benchmark Écriture ─────────────────────────────────────────────────

def benchmark_write_redis(n: int = 100_000):
    """TODO: Insérer n enregistrements dans Redis et mesurer le débit"""
    r = redis.Redis(host='localhost', port=6379)
    # TODO: Implémenter avec pipeline pour maximiser le débit
    r.flushdb()
    start = time.perf_counter()
    pipe = r.pipeline(transaction=False)
    for i in range(n):
        pipe.set(f"k:{i}", json.dumps({"i": i, "v": i * 2}))
        if i % 1000 == 0 and i > 0:
            pipe.execute()
    pipe.execute()
    elapsed = time.perf_counter() - start
    print(f"Redis write: {n:,} ops in {elapsed:.2f}s → {n/elapsed:,.0f} ops/s")


def benchmark_write_mongodb(n: int = 100_000):
    """TODO: Insérer n documents dans MongoDB et mesurer le débit"""
    client = MongoClient("mongodb://admin:admin123@localhost:27017/")
    db = client["benchmark"]
    # TODO: Implémenter avec bulk_write pour maximiser le débit
    col = db["items"]
    col.drop()
    start = time.perf_counter()
    batch_size = 2000
    for i in range(0, n, batch_size):
        docs = [{"_id": i + j, "i": i + j, "v": (i + j) * 2, "ts": time.time()} for j in range(min(batch_size, n - i))]
        col.insert_many(docs, ordered=False)
    elapsed = time.perf_counter() - start
    print(f"MongoDB write: {n:,} docs in {elapsed:.2f}s → {n/elapsed:,.0f} docs/s")


def benchmark_write_cassandra(n: int = 100_000):
    """TODO: Insérer n rows dans Cassandra et mesurer le débit"""
    # TODO: Utiliser des UNLOGGED BATCH
    cluster = Cluster(["localhost"])
    session = cluster.connect()
    session.execute("CREATE KEYSPACE IF NOT EXISTS benchmark WITH replication = {'class':'SimpleStrategy','replication_factor':1}")
    session.set_keyspace("benchmark")
    session.execute("CREATE TABLE IF NOT EXISTS kv (k text PRIMARY KEY, v text)")

    prepared = session.prepare("INSERT INTO kv (k, v) VALUES (?, ?)")
    start = time.perf_counter()
    batch_size = 50
    for i in range(0, n, batch_size):
        batch = BatchStatement(batch_type=BatchType.UNLOGGED)
        for j in range(min(batch_size, n - i)):
            key = f"k:{i + j}"
            val = json.dumps({"i": i + j, "v": (i + j) * 2})
            batch.add(prepared, (key, val))
        session.execute(batch)
    elapsed = time.perf_counter() - start
    print(f"Cassandra write: {n:,} rows in {elapsed:.2f}s → {n/elapsed:,.0f} rows/s")
    cluster.shutdown()


# ─── Ex2 : Benchmark Lecture ─────────────────────────────────────────────────

def benchmark_read_redis():
    """TODO: Point lookup, range (ZRANGE), complex (pipeline multi-get)"""
    r = redis.Redis(host='localhost', port=6379)

    def point_lookup():
        r.get("k:1")

    results = measure_latency(point_lookup, iterations=1000)
    print_results("Redis read - GET", results)

    # Range via sorted set
    zkey = "z:bench"
    if r.zcard(zkey) < 10000:
        pipe = r.pipeline(transaction=False)
        for i in range(10000):
            pipe.zadd(zkey, {str(i): i})
        pipe.execute()

    def range_query():
        r.zrange(zkey, 100, 200)

    results = measure_latency(range_query, iterations=1000)
    print_results("Redis read - ZRANGE", results)

    def complex_pipeline():
        pipe = r.pipeline(transaction=False)
        for i in range(50):
            pipe.get(f"k:{i}")
        pipe.execute()

    results = measure_latency(complex_pipeline, iterations=300)
    print_results("Redis read - pipeline 50 GET", results)


def benchmark_read_mongodb():
    """TODO: find_one, find avec range, aggregate pipeline"""
    client = MongoClient("mongodb://admin:admin123@localhost:27017/")
    db = client["benchmark"]
    col = db["items"]

    if col.estimated_document_count() == 0:
        col.insert_many([{"_id": i, "i": i, "v": i * 2, "ts": time.time()} for i in range(10000)], ordered=False)
    col.create_index({"i": 1})

    def find_one():
        col.find_one({"_id": 1})

    results = measure_latency(find_one, iterations=1000)
    print_results("MongoDB read - find_one", results)

    def range_find():
        list(col.find({"i": {"$gte": 1000, "$lte": 1100}}, {"_id": 0, "i": 1}).limit(50))

    results = measure_latency(range_find, iterations=300)
    print_results("MongoDB read - range find", results)

    def agg():
        list(col.aggregate([
            {"$match": {"i": {"$gte": 0}}},
            {"$group": {"_id": None, "avg": {"$avg": "$v"}, "max": {"$max": "$v"}}}
        ]))

    results = measure_latency(agg, iterations=200)
    print_results("MongoDB read - aggregate", results)


# ─── Ex3 : Charge concurrente ─────────────────────────────────────────────────

def benchmark_concurrent(db_fn: Callable, n_clients: int = 50, requests_per_client: int = 200):
    """
    TODO: Lancer n_clients threads simultanés
    Chaque thread effectue requests_per_client requêtes
    Mesurer les latences globales et la dégradation vs single client
    """
    import threading
    latencies = []
    lock = threading.Lock()

    def worker():
        local = []
        for _ in range(requests_per_client):
            start = time.perf_counter()
            db_fn()
            local.append((time.perf_counter() - start) * 1000)
        with lock:
            latencies.extend(local)

    threads = [threading.Thread(target=worker) for _ in range(n_clients)]
    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - start

    latencies.sort()
    return {
        "total_requests": len(latencies),
        "elapsed_s": elapsed,
        "mean_ms": statistics.mean(latencies) if latencies else 0.0,
        "p50_ms": latencies[int(0.50 * len(latencies))] if latencies else 0.0,
        "p95_ms": latencies[int(0.95 * len(latencies))] if latencies else 0.0,
        "p99_ms": latencies[int(0.99 * len(latencies))] if latencies else 0.0,
        "throughput_rps": (len(latencies) / elapsed) if elapsed > 0 else 0.0,
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Benchmark NoSQL - Comparatif des 4 technologies")
    print("="*60)
    
    N = 10_000  # Réduire pour les tests, 100_000 pour la production
    
    print(f"\n📝 Benchmark Écriture ({N:,} enregistrements)")
    benchmark_write_redis(N)
    benchmark_write_mongodb(N)
    benchmark_write_cassandra(N)
    
    print(f"\n📖 Benchmark Lecture (1,000 requêtes)")
    benchmark_read_redis()
    benchmark_read_mongodb()
    
    print(f"\n⚡ Test Charge Concurrente (50 clients)")
    # benchmark_concurrent(...)
    
    print("\n✅ Benchmark terminé ! Consultez RAPPORT.md pour l'analyse.")
