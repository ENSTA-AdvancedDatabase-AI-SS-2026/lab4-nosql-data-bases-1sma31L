/**
 * TP2 - Exercice 2 : Requêtes MongoDB (find/filter/projection)
 */

use("medical_db");

print("=== 2.1 Diabétiques > 50 ans à Alger ===");
printjson(
  db.patients.find(
    {
      "adresse.wilaya": "Alger",
      antecedents: "Diabète type 2",
      $expr: {
        $gt: [
          {
            $dateDiff: {
              startDate: "$dateNaissance",
              endDate: "$$NOW",
              unit: "year"
            }
          },
          50
        ]
      }
    },
    { _id: 0, cin: 1, nom: 1, prenom: 1, "adresse.wilaya": 1 }
  ).toArray()
);

print("\n=== 2.2 Allergie Pénicilline + au moins 3 consultations ===");
printjson(
  db.patients.find(
    {
      allergies: "Pénicilline",
      $expr: { $gte: [{ $size: "$consultations" }, 3] }
    },
    { _id: 0, cin: 1, nom: 1, prenom: 1, allergies: 1, nb_consultations: { $size: "$consultations" } }
  ).toArray()
);

print("\n=== 2.3 Projection : Nom, prénom, et dernière consultation ===");
printjson(
  db.patients.find(
    {},
    {
      _id: 0,
      nom: 1,
      prenom: 1,
      derniere_consultation: { $arrayElemAt: ["$consultations", -1] }
    }
  ).limit(10).toArray()
);

print("\n=== 2.4 Sans antécédents + tension systolique > 140 (dernière consultation) ===");
printjson(
  db.patients.aggregate([
    { $addFields: { derniere: { $arrayElemAt: ["$consultations", -1] } } },
    {
      $match: {
        $expr: {
          $and: [
            { $eq: [{ $size: "$antecedents" }, 0] },
            { $gt: ["$derniere.tension.systolique", 140] }
          ]
        }
      }
    },
    { $project: { _id: 0, cin: 1, nom: 1, prenom: 1, derniere: 1 } }
  ]).toArray()
);

print("\n=== 2.5 Recherche textuelle diagnostics (nécessite index text) ===");
printjson(
  db.patients.find(
    { $text: { $search: "hypertension diabète" } },
    { _id: 0, cin: 1, nom: 1, prenom: 1, score: { $meta: "textScore" } }
  ).sort({ score: { $meta: "textScore" } }).limit(10).toArray()
);
