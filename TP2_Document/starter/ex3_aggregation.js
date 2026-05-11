/**
 * TP2 - Exercice 3 : Pipelines d'Agrégation
 * Use Case : Statistiques médicales HealthCare DZ
 */

use("medical_db");

// ─── 3.1 : Distribution des diagnostics par wilaya ────────────────────────────
print("=== 3.1 : Top diagnostics par wilaya ===");

const diagParWilaya = db.patients.aggregate([
  { $unwind: "$consultations" },
  {
    $group: {
      _id: {
        wilaya: "$adresse.wilaya",
        diagnostic: "$consultations.diagnostic"
      },
      count: { $sum: 1 }
    }
  },
  { $sort: { count: -1 } },
  { $limit: 20 },
  {
    $project: {
      _id: 0,
      wilaya: "$_id.wilaya",
      diagnostic: "$_id.diagnostic",
      count: 1
    }
  }
]).toArray();

// printjson(diagParWilaya);

// ─── 3.2 : Médicament le plus prescrit par spécialité ─────────────────────────
print("\n=== 3.2 : Top médicaments par spécialité ===");

const medsParSpecialite = db.patients.aggregate([
  { $unwind: "$consultations" },
  { $unwind: "$consultations.medicaments" },
  {
    $group: {
      _id: {
        specialite: "$consultations.medecin.specialite",
        medicament: "$consultations.medicaments.nom"
      },
      count: { $sum: 1 }
    }
  },
  { $sort: { count: -1 } },
  {
    $group: {
      _id: "$_id.specialite",
      top_medicament: { $first: "$_id.medicament" },
      prescriptions: { $first: "$count" }
    }
  },
  { $sort: { prescriptions: -1 } },
  {
    $project: {
      _id: 0,
      specialite: "$_id",
      top_medicament: 1,
      prescriptions: 1
    }
  }
]).toArray();

// ─── 3.3 : Évolution mensuelle des consultations ──────────────────────────────
print("\n=== 3.3 : Consultations par mois (12 derniers mois) ===");

const evolutionMensuelle = db.patients.aggregate([
  { $unwind: "$consultations" },
  { $match: {
    "consultations.date": {
      $gte: new Date(new Date().setFullYear(new Date().getFullYear() - 1))
    }
  }},
  {
    $group: {
      _id: {
        year: { $year: "$consultations.date" },
        month: { $month: "$consultations.date" }
      },
      count: { $sum: 1 }
    }
  },
  { $sort: { "_id.year": 1, "_id.month": 1 } },
  {
    $project: {
      _id: 0,
      month: {
        $concat: [
          { $toString: "$_id.year" },
          "-",
          {
            $cond: [
              { $lt: ["$_id.month", 10] },
              { $concat: ["0", { $toString: "$_id.month" }] },
              { $toString: "$_id.month" }
            ]
          }
        ]
      },
      count: 1
    }
  }
]).toArray();

// ─── 3.4 : Patients à risque multiple ────────────────────────────────────────
print("\n=== 3.4 : Profil patients à risque élevé ===");

const patientsRisque = db.patients.aggregate([
  {
    $match: {
      antecedents: { $all: ["Diabète type 2", "HTA"] },
      $expr: {
        $gt: [
          {
            $dateDiff: {
              startDate: "$dateNaissance",
              endDate: "$$NOW",
              unit: "year"
            }
          },
          60
        ]
      }
    }
  },
  {
    $addFields: {
      age: {
        $dateDiff: {
          startDate: "$dateNaissance",
          endDate: "$$NOW",
          unit: "year"
        }
      },
      nb_consultations: { $size: "$consultations" }
    }
  },
  {
    $group: {
      _id: null,
      nb_patients: { $sum: 1 },
      age_moy: { $avg: "$age" },
      consultations_moy: { $avg: "$nb_consultations" },
      consultations_total: { $sum: "$nb_consultations" }
    }
  },
  {
    $project: {
      _id: 0,
      nb_patients: 1,
      age_moy: 1,
      consultations_moy: 1,
      consultations_total: 1
    }
  }
]).toArray();

// ─── 3.5 : Rapport médecins ───────────────────────────────────────────────────
print("\n=== 3.5 : Top 5 médecins & taux de ré-consultation ===");

const rapportMedecins = db.patients.aggregate([
  { $unwind: "$consultations" },
  {
    $group: {
      _id: {
        medecin: "$consultations.medecin.nom",
        specialite: "$consultations.medecin.specialite"
      },
      consultations_total: { $sum: 1 },
      patients_uniques: { $addToSet: "$cin" }
    }
  },
  {
    $addFields: {
      nb_patients_uniques: { $size: "$patients_uniques" }
    }
  },
  {
    $addFields: {
      taux_reconsultation: {
        $multiply: [
          {
            $divide: [
              { $subtract: ["$consultations_total", "$nb_patients_uniques"] },
              "$nb_patients_uniques"
            ]
          },
          100
        ]
      }
    }
  },
  { $sort: { consultations_total: -1 } },
  { $limit: 5 },
  {
    $project: {
      _id: 0,
      medecin: "$_id.medecin",
      specialite: "$_id.specialite",
      consultations_total: 1,
      nb_patients_uniques: 1,
      taux_reconsultation: 1
    }
  }
]).toArray();

printjson(rapportMedecins);
