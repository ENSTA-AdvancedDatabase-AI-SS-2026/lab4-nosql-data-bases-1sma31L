/**
 * TP2 - Exercice 1 : Modélisation MongoDB
 * Use Case : HealthCare DZ - Dossiers Médicaux
 */

// Se connecter à la base médicale
use("medical_db");

db.patients.drop();
db.analyses.drop();

// ─── 1.1 : Créer la collection avec validation ────────────────────────────────
// TODO: Décommenter et compléter le validator $jsonSchema
db.createCollection("patients", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["cin", "nom", "prenom", "dateNaissance", "sexe", "adresse", "consultations"],
      properties: {
        cin: { bsonType: "string", minLength: 12 },
        nom: { bsonType: "string", minLength: 1 },
        prenom: { bsonType: "string", minLength: 1 },
        dateNaissance: { bsonType: "date" },
        sexe: { enum: ["M", "F"] },
        adresse: {
          bsonType: "object",
          required: ["wilaya", "commune"],
          properties: {
            wilaya: { bsonType: "string" },
            commune: { bsonType: "string" }
          }
        },
        groupeSanguin: { bsonType: "string" },
        antecedents: { bsonType: "array", items: { bsonType: "string" } },
        allergies: { bsonType: "array", items: { bsonType: "string" } },
        consultations: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["id", "date", "medecin", "diagnostic"],
            properties: {
              id: { bsonType: "binData" },
              date: { bsonType: "date" },
              medecin: {
                bsonType: "object",
                required: ["nom", "specialite"],
                properties: {
                  nom: { bsonType: "string" },
                  specialite: { bsonType: "string" }
                }
              },
              diagnostic: { bsonType: "string" },
              tension: {
                bsonType: ["object", "null"],
                properties: {
                  systolique: { bsonType: "int" },
                  diastolique: { bsonType: "int" }
                }
              },
              medicaments: {
                bsonType: "array",
                items: {
                  bsonType: "object",
                  required: ["nom", "dosage", "duree"],
                  properties: {
                    nom: { bsonType: "string" },
                    dosage: { bsonType: "string" },
                    duree: { bsonType: "string" }
                  }
                }
              },
              notes: { bsonType: ["string", "null"] }
            }
          }
        }
      }
    }
  }
});

// ─── 1.2 : Insérer des patients avec données algériennes ──────────────────────
// TODO: Insérer au moins 20 patients avec :
// - Prénoms et noms algériens variés
// - Wilayas différentes (Alger, Oran, Constantine, Annaba, Blida...)
// - Pathologies courantes (Diabète, HTA, Asthme, etc.)
// - Au moins 2-5 consultations par patient
// - Dates réalistes sur les 2 dernières années

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

const wilayas = [
  { wilaya: "Alger", communes: ["Bab Ezzouar", "Hydra", "El Harrach", "Dar El Beida"] },
  { wilaya: "Oran", communes: ["Bir El Djir", "Es Senia", "Arzew"] },
  { wilaya: "Constantine", communes: ["El Khroub", "Ain Smara", "Hamma Bouziane"] },
  { wilaya: "Annaba", communes: ["El Bouni", "El Hadjar", "Seraidi"] },
  { wilaya: "Blida", communes: ["Boufarik", "Larbaa", "Bougara"] }
];

const prenoms = ["Ahmed", "Fatima", "Yacine", "Sara", "Mohamed", "Yasmina", "Riad", "Nadia", "Karim", "Imene", "Amine", "Lina", "Oussama", "Meriem", "Walid", "Houda", "Sofiane", "Samira", "Adel", "Ines"];
const noms = ["Bensalem", "Ouali", "Benali", "Khelifi", "Mansouri", "Ait Ali", "Bouazza", "Chibane", "Ziani", "Hamidi", "Boudiaf", "Mokhtari", "Meziane", "Rahmani", "Cherif", "Saidi", "Guerfi", "Bekkouche", "Kaci", "Toumi"];
const groupes = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+"];

const specialites = ["Cardiologie", "Endocrinologie", "Pneumologie", "Médecine interne", "Gastro-entérologie"];
const diagnostics = [
  "Hypertension artérielle",
  "Diabète type 2",
  "Asthme",
  "Grippe",
  "Dyslipidémie"
];
const medicamentsByDiag = {
  "Hypertension artérielle": [{ nom: "Amlodipine", dosage: "5mg", duree: "30 jours" }],
  "Diabète type 2": [{ nom: "Metformine", dosage: "850mg", duree: "60 jours" }],
  "Asthme": [{ nom: "Salbutamol", dosage: "100µg", duree: "30 jours" }],
  "Grippe": [{ nom: "Paracétamol", dosage: "1g", duree: "5 jours" }],
  "Dyslipidémie": [{ nom: "Atorvastatine", dosage: "20mg", duree: "90 jours" }]
};

function makeConsultation(baseDate, diag) {
  const spec = diag === "Hypertension artérielle" ? "Cardiologie" : (diag === "Diabète type 2" ? "Endocrinologie" : (diag === "Asthme" ? "Pneumologie" : "Médecine interne"));
  const tension = diag === "Hypertension artérielle"
    ? { systolique: randInt(140, 170), diastolique: randInt(85, 105) }
    : null;

  return {
    id: UUID(),
    date: baseDate,
    medecin: { nom: "Dr. " + ["Mansouri", "Kaci", "Rahmani", "Saidi", "Meziane"][randInt(0, 4)], specialite: spec },
    diagnostic: diag,
    tension,
    medicaments: medicamentsByDiag[diag] ?? [],
    notes: null
  };
}

function makePatient(i) {
  const w = wilayas[i % wilayas.length];
  const commune = w.communes[i % w.communes.length];
  const prenom = prenoms[i % prenoms.length];
  const nom = noms[i % noms.length];
  const sexe = i % 2 === 0 ? "M" : "F";

  const year = 1960 + (i % 35);
  const month = (i % 12) + 1;
  const day = ((i * 3) % 28) + 1;

  const antecedents = [];
  if (i % 3 === 0) antecedents.push("Diabète type 2");
  if (i % 4 === 0) antecedents.push("HTA");
  if (i % 7 === 0) antecedents.push("Asthme");

  const allergies = i % 5 === 0 ? ["Pénicilline"] : [];

  const consultations = [];
  const nCons = 2 + (i % 4); // 2..5
  for (let k = 0; k < nCons; k++) {
    const diag = diagnostics[(i + k) % diagnostics.length];
    const monthsAgo = 1 + (i + k) % 22;
    const d = new Date();
    d.setMonth(d.getMonth() - monthsAgo);
    d.setDate(((i + k) % 28) + 1);
    consultations.push(makeConsultation(d, diag));
  }

  return {
    cin: String(198000000000 + i * 12345).padEnd(12, "0").slice(0, 12),
    nom,
    prenom,
    dateNaissance: new Date(`${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`),
    sexe,
    adresse: { wilaya: w.wilaya, commune },
    groupeSanguin: groupes[i % groupes.length],
    antecedents,
    allergies,
    consultations
  };
}

const patients = Array.from({ length: 20 }, (_, i) => makePatient(i + 1));
const insertedPatients = db.patients.insertMany(patients);

// ─── 1.3 : Collection analyses (référencée) ───────────────────────────────────
// TODO: Créer des analyses pour les patients insérés
// Types : "Glycémie", "NFS", "Lipidogramme", "Créatinine", "ECG"

db.createCollection("analyses");

const analyseTypes = ["Glycémie", "NFS", "Lipidogramme", "Créatinine", "ECG"];
const analyses = [];

const patientIds = Object.values(insertedPatients.insertedIds);
for (let i = 0; i < patientIds.length; i++) {
  const pid = patientIds[i];
  const nAnalyses = 2 + (i % 3); // 2..4
  for (let k = 0; k < nAnalyses; k++) {
    const type = analyseTypes[(i + k) % analyseTypes.length];
    const d = new Date();
    d.setMonth(d.getMonth() - (2 + (i + k) % 18));
    const resultats =
      type === "Glycémie" ? { valeur_g_l: Number((0.8 + Math.random() * 0.9).toFixed(2)) } :
      type === "NFS" ? { hb_g_dl: Number((11.0 + Math.random() * 5.0).toFixed(1)) } :
      type === "Lipidogramme" ? { ldl_mg_dl: randInt(70, 190), hdl_mg_dl: randInt(30, 70) } :
      type === "Créatinine" ? { creat_mg_dl: Number((0.6 + Math.random() * 1.6).toFixed(2)) } :
      { rythme: ["Normal", "Tachycardie", "Bradycardie"][randInt(0, 2)] };

    analyses.push({
      patient_id: pid,
      date: d,
      type,
      resultats,
      laboratoire: "Labo Central Alger",
      valide: true
    });
  }
}

db.analyses.insertMany(analyses);

print("✅ Modélisation terminée. Patients insérés:", db.patients.countDocuments());
print("✅ Analyses insérées:", db.analyses.countDocuments());
