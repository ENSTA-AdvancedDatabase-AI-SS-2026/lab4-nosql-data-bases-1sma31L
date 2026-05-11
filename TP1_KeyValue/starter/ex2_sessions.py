"""
TP1 - Exercice 2 : Sessions utilisateur avec TTL
Use Case : ShopFast - Gestion des sessions utilisateur
"""
import redis
import json
import time
from datetime import datetime, timedelta

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

SESSION_TTL = 1800  # 30 minutes en secondes


def create_session(r, user_id: str, data: dict) -> str:
    """
    Créer une nouvelle session utilisateur avec TTL de 30 minutes
    Clé : "session:{user_id}"
    Valeur : JSON des données de session
    """
    session_key = f"session:{user_id}"
    r.setex(session_key, SESSION_TTL, json.dumps(data))
    return session_key


def get_session(r, user_id: str) -> dict:
    """
    Récupérer les données d'une session
    Retourner None si la session n'existe pas ou a expiré
    """
    session_key = f"session:{user_id}"
    data = r.get(session_key)
    return json.loads(data) if data else None


def refresh_session(r, user_id: str):
    """
    Renouveler le TTL d'une session (sliding expiration)
    Si la session existe, réinitialiser le TTL à 30 minutes
    """
    session_key = f"session:{user_id}"
    r.expire(session_key, SESSION_TTL)


def delete_session(r, user_id: str):
    """
    Supprimer explicitement une session (déconnexion)
    """
    r.delete(f"session:{user_id}")


def get_session_ttl(r, user_id: str) -> int:
    """
    Retourner le temps restant avant expiration (en secondes)
    -1 si pas de TTL, -2 si la clé n'existe pas
    """
    return r.ttl(f"session:{user_id}")


if __name__ == "__main__":
    r.flushdb()

    print("=== Test Sessions ===")

    # Créer une session
    user_id = "user:123"
    create_session(r, user_id, {"username": "Ahmed", "cart_items": 3, "role": "customer"})
    print(f"Session créée : {get_session(r, user_id)}")
    print(f"TTL restant : {get_session_ttl(r, user_id)}s")

    # Simuler une activité (refresh)
    time.sleep(1)
    refresh_session(r, user_id)
    print(f"Après refresh TTL : {get_session_ttl(r, user_id)}s")

    # Récupérer à nouveau
    print(f"Session récupérée : {get_session(r, user_id)}")

    # Déconnexion
    delete_session(r, user_id)
    print(f"Après suppression : {get_session(r, user_id)}")
