
"""Patient record definition."""
from dataclasses import dataclass


@dataclass
class Patient:
    """One patient record. admission_date is stored as 'YYYY-MM-DD'."""
    patient_id: int
    name: str
    age: int
    gender: str
    department: str
    diagnosis: str
    doctor: str
    admission_date: str

    def as_row(self):
        """Return the fields as a tuple (handy for Treeview rows)."""
        return (self.patient_id, self.name, self.age, self.gender,
                self.department, self.diagnosis, self.doctor,
                self.admission_date)
