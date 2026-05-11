-- TP3 - Exercice 4 : Compaction et Maintenance

USE smartgrid;

-- 4.1/4.2 : Choix TWCS pour la table de mesures (séries temporelles)
ALTER TABLE mesures_par_capteur
WITH compaction = {
  'class': 'TimeWindowCompactionStrategy',
  'compaction_window_unit': 'DAYS',
  'compaction_window_size': '1'
};

-- Alertes: volume plus faible, accès par jour -> STCS ok par défaut (ou TWCS aussi)
ALTER TABLE alertes_par_wilaya
WITH compaction = {
  'class': 'SizeTieredCompactionStrategy'
};

-- Agrégats horaires: écriture régulière, lecture récente -> STCS ok
ALTER TABLE agregats_horaires
WITH compaction = {
  'class': 'SizeTieredCompactionStrategy'
};

-- 4.3 : Vérifier les TTL
-- Exemple: TTL restant d'une ligne (nécessite une clé complète)
-- SELECT ttl(puissance_kw) FROM mesures_par_capteur
-- WHERE capteur_id = ? AND date_jour = ? AND timestamp = ?;

-- 4.4 : Analyser une partition "hot"
-- Indicateurs: latence élevée sur une seule partition, taille de partition anormale.
-- Correction: ajouter un bucket (jour/heure) dans la partition key, ou sharder avec un "bucket" supplémentaire.
