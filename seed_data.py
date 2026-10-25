"""30 sample patients, inserted only when the table is empty."""
from patient import Patient

# (id, name, age, gender, department, diagnosis, doctor, admission_date)
SEED_ROWS = [
    (1003, "Aarav Sharma", 45, "Male", "Cardiology", "Hypertension", "Dr. R. Mehta", "2026-10-21"),
    (1005, "Priya Nair", 29, "Female", "ENT", "Sinusitis", "Dr. S. Iyer", "2026-10-23"),
    (1007, "Rohan Verma", 8, "Male", "Pediatrics", "Viral Fever", "Dr. A. Kapoor", "2026-10-21"),
    (1010, "Sneha Reddy", 34, "Female", "General Medicine", "Typhoid", "Dr. K. Rao", "2026-10-22"),
    (1014, "Vikram Singh", 61, "Male", "Cardiology", "Angina", "Dr. R. Mehta", "2026-10-24"),
    (1019, "Ananya Das", 52, "Female", "Neurology", "Migraine", "Dr. P. Bose", "2026-10-22"),
    (1023, "Karthik Subramanian", 38, "Male", "Orthopedics", "Fractured Wrist", "Dr. M. Pillai", "2026-10-25"),
    (1028, "Meera Joshi", 5, "Female", "Pediatrics", "Bronchitis", "Dr. A. Kapoor", "2026-10-23"),
    (1031, "Rajesh Gupta", 67, "Male", "Cardiology", "Heart Failure", "Dr. N. Shah", "2026-10-21"),
    (1036, "Divya Menon", 41, "Female", "ENT", "Tonsillitis", "Dr. S. Iyer", "2026-10-24"),
    (1038, "Arjun Patel", 55, "Male", "Neurology", "Stroke", "Dr. P. Bose", "2026-10-25"),
    (1041, "Lakshmi Pillai", 72, "Female", "Orthopedics", "Hip Fracture", "Dr. M. Pillai", "2026-10-22"),
    (1045, "Imran Khan", 33, "Male", "General Medicine", "Dengue", "Dr. K. Rao", "2026-10-23"),
    (1049, "Pooja Kulkarni", 26, "Female", "ENT", "Ear Infection", "Dr. S. Iyer", "2026-10-21"),
    (1052, "Suresh Babu", 58, "Male", "Cardiology", "Arrhythmia", "Dr. N. Shah", "2026-10-25"),
    (1057, "Neha Agarwal", 11, "Female", "Pediatrics", "Asthma", "Dr. A. Kapoor", "2026-10-24"),
    (1061, "Harish Chandra", 49, "Male", "Orthopedics", "Knee Ligament Tear", "Dr. M. Pillai", "2026-10-23"),
    (1064, "Fatima Sheikh", 36, "Female", "Neurology", "Epilepsy", "Dr. P. Bose", "2026-10-21"),
    (1068, "Gopal Krishnan", 63, "Male", "General Medicine", "Diabetes Mellitus", "Dr. K. Rao", "2026-10-25"),
    (1070, "Ishita Banerjee", 31, "Female", "General Medicine", "Malaria", "Dr. K. Rao", "2026-10-22"),
    (1073, "Manoj Tiwari", 47, "Male", "Cardiology", "Chest Pain", "Dr. R. Mehta", "2026-10-23"),
    (1077, "Sunita Yadav", 54, "Female", "Orthopedics", "Osteoarthritis", "Dr. M. Pillai", "2026-10-24"),
    (1080, "Aditya Rao", 3, "Male", "Pediatrics", "Gastroenteritis", "Dr. A. Kapoor", "2026-10-22"),
    (1084, "Kavita Mishra", 44, "Female", "ENT", "Vertigo", "Dr. S. Iyer", "2026-10-25"),
    (1088, "Deepak Chauhan", 59, "Male", "Neurology", "Parkinson's Disease", "Dr. P. Bose", "2026-10-24"),
    (1091, "Rekha Naidu", 66, "Female", "Cardiology", "Hypertension", "Dr. N. Shah", "2026-10-22"),
    (1094, "Sanjay Desai", 40, "Male", "General Medicine", "Pneumonia", "Dr. K. Rao", "2026-10-21"),
    (1096, "Tanvi Bhatt", 22, "Female", "Orthopedics", "Ankle Sprain", "Dr. M. Pillai", "2026-10-23"),
    (1098, "Mohan Lal", 70, "Male", "General Medicine", "COPD", "Dr. K. Rao", "2026-10-24"),
    (1100, "Shreya Ghosh", 9, "Female", "ENT", "Tonsillitis", "Dr. S. Iyer", "2026-10-25"),
]


def seed_if_empty(database):
    """Insert the sample rows when the table has no records."""
    if database.count() == 0:
        for row in SEED_ROWS:
            database.insert(Patient(*row))
