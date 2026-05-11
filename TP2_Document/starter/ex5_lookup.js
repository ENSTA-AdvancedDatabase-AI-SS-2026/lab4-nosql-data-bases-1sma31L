/**
 * TP2 - Exercice 5 : $lookup et données référencées (analyses)
 */

use("medical_db");

print("=== 5.1 Dossier complet d'un patient (patients + analyses) ===");
const one = db.patients.findOne({}, { _id: 1 });

if (one) {
  const dossier = db.patients.aggregate([
    { $match: { _id: one._id } },
    {
      $lookup: {
        from: "analyses",
        localField: "_id",
        foreignField: "patient_id",
        as: "analyses"
      }
    }
  ]).toArray();
  printjson(dossier[0]);
}

print("\n=== 5.2 Patients dont glycémie > 1.26 g/L ===");
printjson(
  db.analyses.aggregate([
    { $match: { type: "Glycémie", "resultats.valeur_g_l": { $gt: 1.26 } } },
    {
      $group: {
        _id: "$patient_id",
        max_glycemie: { $max: "$resultats.valeur_g_l" },
        nb: { $sum: 1 }
      }
    },
    {
      $lookup: {
        from: "patients",
        localField: "_id",
        foreignField: "_id",
        as: "patient"
      }
    },
    { $unwind: "$patient" },
    {
      $project: {
        _id: 0,
        cin: "$patient.cin",
        nom: "$patient.nom",
        prenom: "$patient.prenom",
        wilaya: "$patient.adresse.wilaya",
        max_glycemie: 1,
        nb: 1
      }
    },
    { $sort: { max_glycemie: -1 } }
  ]).toArray()
);

print("\n=== 5.3 Taux d'analyses anormales par wilaya ===");
printjson(
  db.analyses.aggregate([
    {
      $addFields: {
        anormale: {
          $or: [
            { $and: [{ $eq: ["$type", "Glycémie"] }, { $gt: ["$resultats.valeur_g_l", 1.26] }] },
            { $and: [{ $eq: ["$type", "Lipidogramme"] }, { $gt: ["$resultats.ldl_mg_dl", 160] }] },
            { $and: [{ $eq: ["$type", "Créatinine"] }, { $gt: ["$resultats.creat_mg_dl", 1.3] }] }
          ]
        }
      }
    },
    {
      $lookup: {
        from: "patients",
        localField: "patient_id",
        foreignField: "_id",
        as: "patient"
      }
    },
    { $unwind: "$patient" },
    {
      $group: {
        _id: "$patient.adresse.wilaya",
        total: { $sum: 1 },
        anormales: { $sum: { $cond: ["$anormale", 1, 0] } }
      }
    },
    {
      $project: {
        _id: 0,
        wilaya: "$_id",
        total: 1,
        anormales: 1,
        taux_anormal: { $multiply: [{ $divide: ["$anormales", "$total"] }, 100] }
      }
    },
    { $sort: { taux_anormal: -1 } }
  ]).toArray()
);
