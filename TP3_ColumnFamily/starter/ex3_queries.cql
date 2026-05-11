-- TP3 - Exercice 3 : Requêtes CQL

USE smartgrid;

-- 3.1 Mesures d'un capteur spécifique sur les dernières 6 heures
-- Remplacer ? par les valeurs réelles
-- SELECT * FROM mesures_par_capteur
-- WHERE capteur_id = ? AND date_jour = ? AND timestamp >= ?;

-- Exemple (à adapter):
-- SELECT * FROM mesures_par_capteur
-- WHERE capteur_id = 11111111-1111-1111-1111-111111111111
--   AND date_jour = '2026-05-11'
--   AND timestamp >= '2026-05-11 08:00:00';

-- 3.2 Dernière mesure d'un capteur (la plus récente de la journée)
-- SELECT * FROM mesures_par_capteur
-- WHERE capteur_id = ? AND date_jour = ?
-- LIMIT 1;

-- 3.3 Capteurs en alerte dans la wilaya "Alger" aujourd'hui
-- SELECT * FROM alertes_par_wilaya
-- WHERE wilaya = 'Alger' AND date_jour = '2026-05-11';

-- Compter les alertes
-- SELECT count(*) FROM alertes_par_wilaya
-- WHERE wilaya = 'Alger' AND date_jour = '2026-05-11';

-- 3.4 Consommation moyenne par heure sur une journée (dashboard)
-- SELECT * FROM agregats_horaires
-- WHERE wilaya = 'Alger'
-- LIMIT 24;

-- 3.5 Détection d'anomalie : tension < 200V ou > 240V (nécessite filtrage côté app)
-- On récupère une fenêtre temporelle restreinte puis on filtre en application.
-- SELECT * FROM mesures_par_capteur
-- WHERE capteur_id = ? AND date_jour = ? AND timestamp >= ?;

-- 3.6 Top 10 capteurs les plus actifs (plus de mesures) cette semaine
-- Cassandra n'est pas adaptée à ce type d'agrégation ad-hoc sans table dédiée.
-- Solution: table matérialisée / table d'agrégats (non fournie dans ce TP).

-- 3.7 ALLOW FILTERING : pourquoi éviter ?
-- Exemple (à éviter):
-- SELECT * FROM mesures_par_capteur WHERE wilaya='Alger' ALLOW FILTERING;
-- Correct: utiliser alertes_par_wilaya pour les alertes par wilaya/date, et mesures_par_capteur pour un capteur donné.
