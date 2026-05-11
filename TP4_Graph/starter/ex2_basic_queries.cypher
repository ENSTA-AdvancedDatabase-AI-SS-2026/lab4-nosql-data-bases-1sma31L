// TP4 - Exercice 2 : Requêtes de Base Cypher

// 2.1 Trouver tous les amis d'Ahmed (1 saut)
MATCH (a:Etudiant {prenom: "Ahmed"})-[:CONNAIT]-(ami:Etudiant)
RETURN ami.prenom, ami.nom, ami.universite
ORDER BY ami.universite, ami.prenom;

// 2.2 Amis d'amis d'Ahmed qui ne sont pas déjà ses amis
MATCH (a:Etudiant {prenom: "Ahmed"})-[:CONNAIT]-(ami:Etudiant)-[:CONNAIT]-(suggestion:Etudiant)
WHERE suggestion <> a AND NOT (a)-[:CONNAIT]-(suggestion)
RETURN DISTINCT suggestion.prenom, suggestion.nom, suggestion.universite
LIMIT 15;

// 2.3 Étudiants qui suivent le même cours que Fatima mais ne la connaissent pas
MATCH (f:Etudiant {prenom: "Fatima"})-[:SUIT]->(c:Cours)<-[:SUIT]-(e:Etudiant)
WHERE e <> f AND NOT (f)-[:CONNAIT]-(e)
RETURN DISTINCT e.prenom, e.nom, c.code, c.intitule
ORDER BY c.code
LIMIT 20;

// 2.4 Clubs les plus populaires (par nombre de membres)
MATCH (e:Etudiant)-[:MEMBRE_DE]->(cl:Club)
RETURN cl.nom AS club, cl.universite AS universite, count(e) AS membres
ORDER BY membres DESC
LIMIT 10;

// 2.5 Profil complet d'un étudiant : amis, cours, compétences, clubs
MATCH (e:Etudiant {prenom: "Ahmed"})
OPTIONAL MATCH (e)-[:CONNAIT]-(a:Etudiant)
OPTIONAL MATCH (e)-[s:SUIT]->(c:Cours)
OPTIONAL MATCH (e)-[m:MAITRISE]->(k:Competence)
OPTIONAL MATCH (e)-[:MEMBRE_DE]->(cl:Club)
RETURN e.prenom AS prenom,
       e.nom AS nom,
       collect(DISTINCT a.prenom + " " + a.nom) AS amis,
       collect(DISTINCT c.code + " (" + toString(s.note) + ")") AS cours,
       collect(DISTINCT k.nom + " (niveau " + toString(m.niveau) + ")") AS competences,
       collect(DISTINCT cl.nom) AS clubs;
