// TP4 - Exercice 1 : Création du graphe UniConnect DZ
// Effacer la base pour partir propre
MATCH (n) DETACH DELETE n;

// ─── 1.1 : Contraintes d'unicité ─────────────────────────────────────────────
CREATE CONSTRAINT etudiant_id IF NOT EXISTS FOR (e:Etudiant) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT cours_code IF NOT EXISTS FOR (c:Cours) REQUIRE c.code IS UNIQUE;
CREATE CONSTRAINT competence_nom IF NOT EXISTS FOR (c:Competence) REQUIRE c.nom IS UNIQUE;

// ─── 1.2 : Créer les compétences ──────────────────────────────────────────────
UNWIND [
  {nom: "Python", categorie: "Programmation"},
  {nom: "Java", categorie: "Programmation"},
  {nom: "SQL", categorie: "Bases de Données"},
  {nom: "NoSQL", categorie: "Bases de Données"},
  {nom: "Machine Learning", categorie: "IA"},
  {nom: "Deep Learning", categorie: "IA"},
  {nom: "React", categorie: "Web"},
  {nom: "Docker", categorie: "DevOps"},
  {nom: "Linux", categorie: "Systèmes"},
  {nom: "Réseaux", categorie: "Infrastructure"}
] AS comp
MERGE (:Competence {nom: comp.nom, categorie: comp.categorie});

// ─── 1.3 : Créer les cours ────────────────────────────────────────────────────
UNWIND [
  {code: "INFO401", intitule: "Bases de Données Avancées", credits: 6, dept: "Informatique"},
  {code: "INFO402", intitule: "Intelligence Artificielle", credits: 6, dept: "Informatique"},
  {code: "INFO403", intitule: "Développement Web", credits: 4, dept: "Informatique"},
  {code: "INFO404", intitule: "Systèmes Distribués", credits: 5, dept: "Informatique"},
  {code: "INFO405", intitule: "Cloud Computing", credits: 4, dept: "Informatique"}
] AS cours
MERGE (:Cours {code: cours.code, intitule: cours.intitule, 
               credits: cours.credits, departement: cours.dept});

// ─── 1.4 : Créer les étudiants ────────────────────────────────────────────────
// TODO: Créer 50 étudiants avec données algériennes réalistes
// Utiliser UNWIND avec une liste de maps
// Universités : USTHB, UMBB, USTO, UMC, UBMA
// Filieres : Informatique, Mathématiques, Electronique, Telecoms, GL

LOAD CSV WITH HEADERS FROM 'file:///students.csv' AS row
MERGE (e:Etudiant {id: row.id})
SET e.prenom = row.prenom,
    e.nom = row.nom,
    e.universite = row.universite,
    e.filiere = row.filiere,
    e.annee = toInteger(row.annee),
    e.ville = row.ville;

UNWIND range(11,50) AS i
WITH i,
     ["USTHB","UMBB","USTO","UMC","UBMA"][i % 5] AS universite,
     ["Informatique","Mathematiques","Electronique","Telecoms","GL"][i % 5] AS filiere,
     ["Alger","Boumerdes","Oran","Constantine","Annaba"][i % 5] AS ville,
     ["Mohamed","Sara","Yacine","Lina","Karim","Imene","Walid","Meriem","Adel","Nadia"][i % 10] AS prenom,
     ["Benali","Khelifi","Meziane","Rahmani","Saidi","Cherif","Hamidi","Toumi","Bekkouche","Kaci"][i % 10] AS nom
MERGE (e:Etudiant {id: "E" + toString(i).lpad(3,'0')})
SET e.prenom = prenom,
    e.nom = nom,
    e.universite = universite,
    e.filiere = filiere,
    e.annee = (i % 4) + 1,
    e.ville = ville;

// ─── 1.4bis : Clubs et entreprises ───────────────────────────────────────────
UNWIND [
  {nom: "Club IA", universite: "USTHB", domaine: "IA"},
  {nom: "Club Robotics", universite: "UMBB", domaine: "Robotique"},
  {nom: "Club Web", universite: "USTO", domaine: "Web"},
  {nom: "Club Cyber", universite: "UMC", domaine: "Sécurité"},
  {nom: "Club Data", universite: "UBMA", domaine: "Data"}
] AS club
MERGE (:Club {nom: club.nom, universite: club.universite, domaine: club.domaine});

UNWIND [
  {nom: "Sonatrach", secteur: "Énergie", ville: "Alger"},
  {nom: "Djezzy", secteur: "Télécoms", ville: "Alger"},
  {nom: "Ooredoo", secteur: "Télécoms", ville: "Oran"},
  {nom: "Cevital", secteur: "Agroalimentaire", ville: "Bejaia"},
  {nom: "Cosider", secteur: "BTP", ville: "Alger"}
] AS ent
MERGE (:Entreprise {nom: ent.nom, secteur: ent.secteur, ville: ent.ville});

// ─── 1.5 : Créer les relations ────────────────────────────────────────────────
// TODO: Relations CONNAIT entre étudiants
// Assurer que le graphe est connexe (pas d'étudiants isolés)

// Chaîne de connexité (assure graphe connexe)
MATCH (e:Etudiant)
WITH e ORDER BY e.id
WITH collect(e) AS es
UNWIND range(0, size(es)-2) AS idx
WITH es[idx] AS a, es[idx+1] AS b
MERGE (a)-[:CONNAIT {depuis: 2023, contexte: "cours"}]->(b)
MERGE (b)-[:CONNAIT {depuis: 2023, contexte: "cours"}]->(a);

// Connexions supplémentaires
MATCH (e:Etudiant)
WITH collect(e) AS es
UNWIND range(1, 120) AS _
WITH es[toInteger(rand() * size(es))] AS a, es[toInteger(rand() * size(es))] AS b
WHERE a.id <> b.id
MERGE (a)-[:CONNAIT {depuis: 2024, contexte: "club"}]->(b);

// Relations SUIT (étudiant → cours) avec notes
MATCH (e:Etudiant), (c:Cours)
WITH e, collect(c) AS cs
UNWIND cs[0..3] AS c1
WITH e, c1
MERGE (e)-[:SUIT {semestre: "S" + toString((e.annee % 2) + 1), note: toFloat(10 + rand() * 10)}]->(c1);

// Relations MAITRISE (étudiant → compétence) avec niveaux
MATCH (e:Etudiant), (k:Competence)
WITH e, collect(k) AS ks
UNWIND ks[0..4] AS k1
WITH e, k1
MERGE (e)-[:MAITRISE {niveau: toInteger(1 + rand() * 4)}]->(k1);

// MEMBRE_DE (un club par étudiant)
MATCH (e:Etudiant), (cl:Club)
WITH e, collect(cl) AS cls
WITH e, cls[toInteger(rand()*size(cls))] AS chosen
MERGE (e)-[:MEMBRE_DE {role: "membre"}]->(chosen);

// Stages (quelques étudiants)
MATCH (e:Etudiant)
WITH e ORDER BY rand() LIMIT 15
MATCH (ent:Entreprise)
WITH e, collect(ent) AS ents
WITH e, ents[toInteger(rand()*size(ents))] AS chosen
MERGE (e)-[:A_STAGE_CHEZ {annee: 2025, duree_mois: toInteger(1 + rand()*5)}]->(chosen);

// Cours -> compétences requises
MATCH (c:Cours), (k:Competence)
WITH c, collect(k) AS ks
UNWIND ks[0..2] AS k1
WITH c, k1
MERGE (c)-[:REQUIERT]->(k1);

// Vérification
MATCH (n) RETURN labels(n)[0] AS type, count(n) AS total ORDER BY total DESC;
MATCH ()-[r]->() RETURN type(r) AS relation, count(r) AS total ORDER BY total DESC;
