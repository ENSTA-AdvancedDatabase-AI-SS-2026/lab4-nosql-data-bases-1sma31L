// TP4 - Exercice 4 : Requêtes avancées

// 4.1 Trouver un tuteur
// Étudiant en Master (annee >= 4) qui maîtrise Python et a eu > 14/20 en Bases de Données Avancées
MATCH (t:Etudiant)-[m:MAITRISE]->(:Competence {nom: "Python"})
MATCH (t)-[s:SUIT]->(c:Cours {code: "INFO401"})
WHERE t.annee >= 4 AND s.note > 14
RETURN t.prenom, t.nom, t.universite, t.filiere, m.niveau AS niveau_python, s.note AS note_bdd
ORDER BY s.note DESC, m.niveau DESC
LIMIT 10;

// 4.2 Réseau alumni dans une entreprise
// Qui de mon réseau (jusqu'à 3 sauts) travaille chez Sonatrach ?
MATCH (moi:Etudiant {prenom: "Ahmed"})
MATCH (moi)-[:CONNAIT*1..3]-(x:Etudiant)-[:A_STAGE_CHEZ]->(e:Entreprise {nom: "Sonatrach"})
RETURN DISTINCT x.prenom, x.nom, x.universite, e.nom AS entreprise
LIMIT 20;

// 4.3 Détection de "ponts" simples : étudiants connectant 2 universités différentes
MATCH (a:Etudiant)-[:CONNAIT]-(b:Etudiant)
WHERE a.universite <> b.universite
RETURN a.prenom + " " + a.nom AS etudiant,
       a.universite AS u1,
       b.universite AS u2
LIMIT 20;

// 4.4 Croissance du réseau : nouvelles connexions par année (selon propriété 'depuis')
MATCH ()-[r:CONNAIT]->()
RETURN r.depuis AS annee, count(*) AS nb_connexions
ORDER BY annee;

// 4.5 Similarité Jaccard (cours en commun) : étudiants les plus similaires à Ahmed
MATCH (a:Etudiant {prenom: "Ahmed"})-[:SUIT]->(c:Cours)
WITH a, collect(DISTINCT c.code) AS coursA
MATCH (b:Etudiant)-[:SUIT]->(c2:Cours)
WHERE b <> a
WITH a, coursA, b, collect(DISTINCT c2.code) AS coursB
WITH b,
     size([x IN coursA WHERE x IN coursB]) AS inter,
     size(apoc.coll.toSet(coursA + coursB)) AS uni
RETURN b.prenom + " " + b.nom AS etudiant,
       (toFloat(inter) / toFloat(uni)) AS jaccard
ORDER BY jaccard DESC
LIMIT 10;
