"""
TP3 - Exercice 2 : Ingestion de données IoT
Use Case : SmartGrid DZ - 10 000 capteurs, 5 minutes de mesures
"""
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement, BatchType
import uuid
import random
from datetime import datetime, timedelta
import time

# Configuration
CASSANDRA_HOST = 'localhost'
KEYSPACE = 'smartgrid'
NB_CAPTEURS = 10000
MINUTES_HISTORIQUE = 5

WILAYAS = ["Alger", "Oran", "Constantine", "Annaba", "Blida"]
COMMUNES = {
    "Alger": ["Bab Ezzouar", "Hydra", "El Harrach", "Dar El Beida"],
    "Oran": ["Bir El Djir", "Es Senia", "Arzew"],
    "Constantine": ["El Khroub", "Ain Smara", "Hamma Bouziane"],
    "Annaba": ["El Bouni", "El Hadjar", "Seraidi"],
    "Blida": ["Bougara", "Boufarik", "Larbaa"],
}

def connect():
    """Connexion au cluster Cassandra"""
    cluster = Cluster([CASSANDRA_HOST])
    session = cluster.connect(KEYSPACE)
    return session, cluster


def generate_mesure(capteur_id, wilaya, commune, timestamp):
    """Générer une mesure réaliste pour un capteur"""
    tension_base = 220  # Volts (réseau algérien)
    
    return {
        "capteur_id": capteur_id,
        "date_jour": timestamp.date(),
        "timestamp": timestamp,
        "wilaya": wilaya,
        "commune": commune,
        # Variation normale ± 10V
        "tension_v": round(tension_base + random.gauss(0, 5), 2),
        "courant_a": round(random.uniform(0.5, 15.0), 2),
        "puissance_kw": round(random.uniform(0.1, 3.3), 3),
        "frequence_hz": round(50 + random.gauss(0, 0.1), 2),
        "temperature": round(random.uniform(20, 65), 1),
        # 5% de chance d'alerte
        "alerte": random.random() < 0.05,
    }


def insert_single(session, mesure):
    """
    TODO: Insérer une seule mesure dans mesures_par_capteur
    Utiliser une prepared statement
    """
    if not hasattr(insert_single, "_prepared"):
        insert_single._prepared = session.prepare(
            "INSERT INTO mesures_par_capteur (capteur_id, date_jour, timestamp, wilaya, commune, tension_v, courant_a, puissance_kw, frequence_hz, temperature, alerte, code_alerte) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) USING TTL 7776000"
        )

    code_alerte = None
    if mesure["alerte"]:
        if mesure["tension_v"] < 200:
            code_alerte = "LOW_VOLT"
        elif mesure["tension_v"] > 240:
            code_alerte = "HIGH_VOLT"
        elif mesure["temperature"] > 60:
            code_alerte = "OVERHEAT"
        else:
            code_alerte = "GEN"

    session.execute(
        insert_single._prepared,
        (
            mesure["capteur_id"],
            mesure["date_jour"],
            mesure["timestamp"],
            mesure["wilaya"],
            mesure["commune"],
            mesure["tension_v"],
            mesure["courant_a"],
            mesure["puissance_kw"],
            mesure["frequence_hz"],
            mesure["temperature"],
            mesure["alerte"],
            code_alerte,
        ),
    )


def insert_batch(session, mesures: list):
    """
    TODO: Insérer un batch de mesures de manière efficace
    Utiliser UNLOGGED BATCH pour les séries temporelles
    Faire des batches de max 50 items (bonne pratique Cassandra)
    """
    if not hasattr(insert_batch, "_prepared_mesure"):
        insert_batch._prepared_mesure = session.prepare(
            "INSERT INTO mesures_par_capteur (capteur_id, date_jour, timestamp, wilaya, commune, tension_v, courant_a, puissance_kw, frequence_hz, temperature, alerte, code_alerte) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) USING TTL ?"
        )
        insert_batch._prepared_alerte = session.prepare(
            "INSERT INTO alertes_par_wilaya (wilaya, date_jour, timestamp, capteur_id, code_alerte, description, gravite, resolue) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) USING TTL ?"
        )

    max_batch = 50
    for i in range(0, len(mesures), max_batch):
        chunk = mesures[i : i + max_batch]
        batch = BatchStatement(batch_type=BatchType.UNLOGGED)

        for mesure in chunk:
            code_alerte = None
            gravite = 1
            description = None

            if mesure["alerte"]:
                if mesure["tension_v"] < 200:
                    code_alerte = "LOW_VOLT"
                    gravite = 3
                    description = "Tension < 200V"
                elif mesure["tension_v"] > 240:
                    code_alerte = "HIGH_VOLT"
                    gravite = 3
                    description = "Tension > 240V"
                elif mesure["temperature"] > 60:
                    code_alerte = "OVERHEAT"
                    gravite = 2
                    description = "Température > 60°C"
                else:
                    code_alerte = "GEN"
                    gravite = 1
                    description = "Alerte générique"

            batch.add(
                insert_batch._prepared_mesure,
                (
                    mesure["capteur_id"],
                    mesure["date_jour"],
                    mesure["timestamp"],
                    mesure["wilaya"],
                    mesure["commune"],
                    mesure["tension_v"],
                    mesure["courant_a"],
                    mesure["puissance_kw"],
                    mesure["frequence_hz"],
                    mesure["temperature"],
                    mesure["alerte"],
                    code_alerte,
                    7776000,
                ),
            )

            if mesure["alerte"]:
                batch.add(
                    insert_batch._prepared_alerte,
                    (
                        mesure["wilaya"],
                        mesure["date_jour"],
                        mesure["timestamp"],
                        mesure["capteur_id"],
                        code_alerte,
                        description,
                        gravite,
                        False,
                        31536000,
                    ),
                )

        session.execute(batch)


def run_ingestion(session):
    """
    TODO: Générer et insérer NB_CAPTEURS × MINUTES_HISTORIQUE mesures
    1. Générer les capteurs (ID aléatoires + assignation wilaya/commune)
    2. Pour chaque minute des MINUTES_HISTORIQUE dernières minutes
       → Insérer les mesures de tous les capteurs
    3. Mesurer et afficher :
       - Nombre total d'insertions
       - Durée totale
       - Débit (mesures/seconde)
    """
    print(f"Démarrage ingestion : {NB_CAPTEURS} capteurs × {MINUTES_HISTORIQUE} min")
    start = time.time()
    
    capteurs = []
    for i in range(NB_CAPTEURS):
        capteur_id = uuid.uuid4()
        wilaya = WILAYAS[i % len(WILAYAS)]
        commune = COMMUNES[wilaya][i % len(COMMUNES[wilaya])]
        capteurs.append((capteur_id, wilaya, commune))

    now = datetime.utcnow()
    for minute_offset in range(MINUTES_HISTORIQUE):
        ts = now - timedelta(minutes=minute_offset)
        mesures = []
        for capteur_id, wilaya, commune in capteurs:
            m = generate_mesure(capteur_id, wilaya, commune, ts)
            mesures.append(m)
        insert_batch(session, mesures)
    
    elapsed = time.time() - start
    total = NB_CAPTEURS * MINUTES_HISTORIQUE
    print(f"\n✅ {total:,} mesures insérées en {elapsed:.1f}s")
    print(f"   Débit : {total/elapsed:,.0f} mesures/seconde")


if __name__ == "__main__":
    session, cluster = connect()
    run_ingestion(session)
    cluster.shutdown()
