"""
TP1 - Exercice 5 : Pipeline & Transactions
Use Case : ShopFast - Insertion bulk et commandes atomiques
"""
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)


def bulk_insert_products(r, products: list):
    """
    Insérer plusieurs produits en utilisant un pipeline
    products : liste de dicts avec id, name, price, stock, category
    """
    pipe = r.pipeline()
    for p in products:
        product_id = p["id"]
        mapping = {k: str(v) for k, v in p.items() if k != "id"}
        pipe.hset(f"product:{product_id}", mapping=mapping)
    return pipe.execute()


def atomic_purchase(r, user_id: str, product_id: int, quantity: int = 1):
    """
    Transaction atomique MULTI/EXEC :
    1. Vérifier le stock du produit
    2. Décrémenter le stock
    3. Ajouter au panier de l'utilisateur
    4. Enregistrer la vente dans le leaderboard
    Si une étape échoue, tout est annulé
    """
    product_key = f"product:{product_id}"
    cart_key = f"cart:{user_id}"
    leaderboard_key = "leaderboard:sales"

    with r.pipeline() as pipe:
        try:
            pipe.watch(product_key)
            stock = int(pipe.hget(product_key, "stock") or 0)

            if stock < quantity:
                pipe.unwatch()
                return {"success": False, "error": "Stock insuffisant"}

            pipe.multi()
            pipe.hincrby(product_key, "stock", -quantity)
            pipe.hincrby(cart_key, str(product_id), quantity)
            pipe.zincrby(leaderboard_key, quantity, str(product_id))
            results = pipe.execute()
            return {"success": True, "results": results}
        except redis.WatchError:
            return {"success": False, "error": "Conflit de concurrence, réessayez"}


if __name__ == "__main__":
    r.flushdb()

    print("=== Test Pipeline Bulk Insert ===")
    products = [
        {"id": 1, "name": "Samsung A54", "price": "65000", "stock": "15", "category": "phones"},
        {"id": 2, "name": "Laptop HP", "price": "120000", "stock": "8", "category": "laptops"},
        {"id": 3, "name": "Casque JBL", "price": "12000", "stock": "50", "category": "audio"},
        {"id": 4, "name": "Clavier Mécanique", "price": "8000", "stock": "30", "category": "accessories"},
    ]
    bulk_insert_products(r, products)
    print(f"Produits insérés : {r.hgetall('product:1')}")

    print("\n=== Test Transaction Atomique ===")
    result = atomic_purchase(r, "user:42", 1, 2)
    print(f"Résultat achat : {result}")
    print(f"Stock restant produit #1 : {r.hget('product:1', 'stock')}")
    print(f"Panier user:42 : {r.hgetall('cart:user:42')}")
    print(f"Leaderboard : {r.zrevrange('leaderboard:sales', 0, -1, withscores=True)}")

    # Test stock insuffisant
    result2 = atomic_purchase(r, "user:42", 2, 10)
    print(f"\nAchat avec stock insuffisant : {result2}")
