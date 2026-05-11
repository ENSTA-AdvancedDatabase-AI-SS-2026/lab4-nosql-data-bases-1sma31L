/**
 * TP2 - Exercice 4 : Index et Optimisation
 */

use("medical_db");

// ─── 4.1 : Créer les index appropriés ────────────────────────────────────────

// Index 1 : Recherche fréquente par wilaya + antécédents
// TODO: Créer l'index composé approprié
db.patients.createIndex({ "adresse.wilaya": 1, antecedents: 1 });

// Index 2 : Recherche par date de consultation
// TODO:
db.patients.createIndex({ "consultations.date": -1 });

// Index 3 : Texte sur diagnostics pour recherche full-text
// TODO:
db.patients.createIndex({ "consultations.diagnostic": "text" });

// Index 4 : Analyses par patient (lookup)
// TODO:
db.analyses.createIndex({ patient_id: 1, date: -1 });


// ─── 4.2 : Comparer avec explain() ────────────────────────────────────────────

// Requête de test
const requeteTest = {
  "adresse.wilaya": "Alger",
  antecedents: "Diabète type 2"
};

print("=== AVANT index ===");
const before = db.patients.find(requeteTest).explain("executionStats");
printjson({
  nReturned: before.executionStats.nReturned,
  totalDocsExamined: before.executionStats.totalDocsExamined,
  executionTimeMillis: before.executionStats.executionTimeMillis
});

print("\n=== APRÈS index ===");
// TODO: Après création de l'index, même requête avec explain()
// Comparer : nReturned, totalDocsExamined, executionTimeMillis
const after = db.patients.find(requeteTest).explain("executionStats");
printjson({
  nReturned: after.executionStats.nReturned,
  totalDocsExamined: after.executionStats.totalDocsExamined,
  executionTimeMillis: after.executionStats.executionTimeMillis
});

// ─── 4.4 : Index TTL pour archivage ───────────────────────────────────────────
// TODO: Créer un index TTL sur analyses.date pour expirer après 5 ans
// db.analyses.createIndex(
//   { date: 1 },
//   { expireAfterSeconds: ??? }
// );

db.analyses.createIndex(
  { date: 1 },
  { expireAfterSeconds: 60 * 60 * 24 * 365 * 5 }
);
