"""Database module for Denta Atelier.
Provides persistent storage using SQLite locally, with support for PostgreSQL / DATABASE_URL for cloud deployments.
"""
import os
import json
import sqlite3
from typing import Dict, Any, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_FILE = os.path.join(DB_DIR, "denta_atelier.db")

DEFAULT_SEED = {
    "clinic": {
        "name": "Denta Atelier Centrală",
        "address": "Strada Exemplu 10, Chișinău",
        "taxId": "1024600033211",
        "phone": "+373 22 456 880",
        "hours": ["08:00", "18:00"],
        "lunch": ["13:00", "14:00"]
    },
    "settings": {
        "step": 30,
        "duration": 60
    },
    "patients": [
        {
            "id": "p1",
            "first": "Mara",
            "last": "Exemplu",
            "phone": "060 000 101",
            "sex": "F",
            "birth": 1992,
            "nid": "2001018123456",
            "owner": "u1",
            "status": "open",
            "shared": False
        },
        {
            "id": "p2",
            "first": "Tudor",
            "last": "Demo",
            "phone": "060 000 102",
            "sex": "M",
            "birth": 1985,
            "nid": "2002022123441",
            "owner": "u1",
            "status": "open",
            "shared": False
        },
        {
            "id": "p3",
            "first": "Sofia",
            "last": "Test",
            "phone": "060 000 103",
            "sex": "F",
            "birth": 1996,
            "nid": "",
            "owner": "u2",
            "status": "locked",
            "shared": True
        }
    ],
    "appointments": [
        {
            "id": "a1",
            "patient": "p1",
            "start": "2026-10-05T09:00",
            "end": "2026-10-05T10:00"
        },
        {
            "id": "a2",
            "patient": "p2",
            "start": "2026-10-06T11:30",
            "end": "2026-10-06T12:15"
        },
        {
            "id": "a3",
            "patient": "p1",
            "start": "2026-10-08T14:00",
            "end": "2026-10-08T15:30"
        }
    ],
    "sections": [
        {"id": "s1", "name": "Terapie"},
        {"id": "s2", "name": "Chirurgie"},
        {"id": "s3", "name": "Ortodonție"}
    ],
    "services": [
        {"id": "x1", "section": "s1", "name": "Consultație inițială", "price": 350},
        {"id": "x2", "section": "s1", "name": "Obturație compozit", "price": 1200},
        {"id": "x3", "section": "s2", "name": "Extracție simplă", "price": 800},
        {"id": "x4", "section": "s3", "name": "Control aparat dentar", "price": 500}
    ],
    "doctors": [
        {
            "id": "u1",
            "first": "Medic",
            "last": "Demo",
            "email": "medic.demo@example.invalid",
            "phone": "060 000 201",
            "role": "Administrator",
            "salary": {"mode": "percent", "percentage": 35, "fixed": 0}
        },
        {
            "id": "u2",
            "first": "Doctor",
            "last": "Test",
            "email": "doctor.test@example.invalid",
            "phone": "060 000 202",
            "role": "Medic",
            "salary": {"mode": "hybrid", "percentage": 25, "fixed": 8000}
        }
    ],
    "records": {
        "p1": {
            "diagnostic": "Caria dentară simplă, 2.6",
            "complaints": "Sensibilitate la rece.",
            "notes": "Control peste 6 luni."
        },
        "p2": {
            "diagnostic": "Gingivită catarală",
            "complaints": "Sângerare gingivală.",
            "notes": "Igienizare profesională recomandată."
        }
    },
    "templates": [
        {
            "name": "Consultație de rutină",
            "fields": "diagnostic,complaints,notes",
            "text": "Examinare clinică efectuată. Recomandări oferite pacientului."
        }
    ],
    "quick": [
        {
            "field": "complaints",
            "text": "Pacientul nu acuză dureri spontane."
        }
    ]
}


def get_db_path() -> str:
    os.makedirs(DB_DIR, exist_ok=True)
    return DB_FILE


def get_connection():
    path = get_db_path()
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initializes tables and seeds initial data if empty."""
    conn = get_connection()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS clinic (
            id TEXT PRIMARY KEY,
            name TEXT,
            address TEXT,
            tax_id TEXT,
            phone TEXT,
            hours_start TEXT,
            hours_end TEXT,
            lunch_start TEXT,
            lunch_end TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            id TEXT PRIMARY KEY,
            step INTEGER,
            duration INTEGER
        );

        CREATE TABLE IF NOT EXISTS doctors (
            id TEXT PRIMARY KEY,
            first TEXT,
            last TEXT,
            email TEXT,
            phone TEXT,
            role TEXT,
            salary_mode TEXT,
            salary_percentage REAL,
            salary_fixed REAL
        );

        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            first TEXT,
            last TEXT,
            phone TEXT,
            sex TEXT,
            birth INTEGER,
            nid TEXT,
            owner TEXT,
            status TEXT,
            shared INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            patient TEXT,
            start_time TEXT,
            end_time TEXT
        );

        CREATE TABLE IF NOT EXISTS sections (
            id TEXT PRIMARY KEY,
            name TEXT
        );

        CREATE TABLE IF NOT EXISTS services (
            id TEXT PRIMARY KEY,
            section TEXT,
            name TEXT,
            price REAL
        );

        CREATE TABLE IF NOT EXISTS records (
            patient_id TEXT PRIMARY KEY,
            diagnostic TEXT,
            complaints TEXT,
            history TEXT,
            exterior TEXT,
            teeth TEXT,
            mucosa TEXT,
            treatment TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            fields TEXT,
            text TEXT
        );

        CREATE TABLE IF NOT EXISTS quick_texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field TEXT,
            text TEXT
        );
        """)

        # Lightweight, forward-compatible configuration for local clinic features
        # such as SMS templates, variable hours and a print logo.
        clinic_columns = {row[1] for row in conn.execute("PRAGMA table_info(clinic)")}
        if "preferences_json" not in clinic_columns:
            conn.execute("ALTER TABLE clinic ADD COLUMN preferences_json TEXT DEFAULT '{}'")

        # Check if database has any clinic record, else seed
        cur = conn.cursor()
        cur.execute("SELECT count(*) as cnt FROM clinic")
        if cur.fetchone()["cnt"] == 0:
            seed_data(conn, DEFAULT_SEED)

    conn.close()


def seed_data(conn: sqlite3.Connection, data: Dict[str, Any]):
    """Populates empty database with initial seed structure."""
    c = data.get("clinic", {})
    conn.execute(
        """INSERT OR REPLACE INTO clinic
           (id, name, address, tax_id, phone, hours_start, hours_end, lunch_start, lunch_end)
           VALUES ('main', ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            c.get("name", ""),
            c.get("address", ""),
            c.get("taxId", ""),
            c.get("phone", ""),
            c.get("hours", ["08:00", "18:00"])[0] if len(c.get("hours", [])) > 0 else "08:00",
            c.get("hours", ["08:00", "18:00"])[1] if len(c.get("hours", [])) > 1 else "18:00",
            c.get("lunch", ["13:00", "14:00"])[0] if len(c.get("lunch", [])) > 0 else "13:00",
            c.get("lunch", ["13:00", "14:00"])[1] if len(c.get("lunch", [])) > 1 else "14:00"
        )
    )

    s = data.get("settings", {})
    conn.execute(
        """INSERT OR REPLACE INTO settings (id, step, duration)
           VALUES ('main', ?, ?)""",
        (s.get("step", 30), s.get("duration", 60))
    )

    for d in data.get("doctors", []):
        sal = d.get("salary", {})
        conn.execute(
            """INSERT OR REPLACE INTO doctors
               (id, first, last, email, phone, role, salary_mode, salary_percentage, salary_fixed)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                d.get("id"),
                d.get("first"),
                d.get("last"),
                d.get("email"),
                d.get("phone"),
                d.get("role"),
                sal.get("mode", "percent"),
                sal.get("percentage", 25),
                sal.get("fixed", 0)
            )
        )

    for p in data.get("patients", []):
        conn.execute(
            """INSERT OR REPLACE INTO patients
               (id, first, last, phone, sex, birth, nid, owner, status, shared)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                p.get("id"),
                p.get("first"),
                p.get("last"),
                p.get("phone"),
                p.get("sex"),
                p.get("birth"),
                p.get("nid", ""),
                p.get("owner", "u1"),
                p.get("status", "open"),
                1 if p.get("shared") else 0
            )
        )

    for a in data.get("appointments", []):
        conn.execute(
            """INSERT OR REPLACE INTO appointments (id, patient, start_time, end_time)
               VALUES (?, ?, ?, ?)""",
            (a.get("id"), a.get("patient"), a.get("start"), a.get("end"))
        )

    for sec in data.get("sections", []):
        conn.execute(
            """INSERT OR REPLACE INTO sections (id, name) VALUES (?, ?)""",
            (sec.get("id"), sec.get("name"))
        )

    for srv in data.get("services", []):
        conn.execute(
            """INSERT OR REPLACE INTO services (id, section, name, price)
               VALUES (?, ?, ?, ?)""",
            (srv.get("id"), srv.get("section"), srv.get("name"), srv.get("price"))
        )

    for pid, r in data.get("records", {}).items():
        conn.execute(
            """INSERT OR REPLACE INTO records
               (patient_id, diagnostic, complaints, history, exterior, teeth, mucosa, treatment, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                pid,
                r.get("diagnostic", ""),
                r.get("complaints", ""),
                r.get("history", ""),
                r.get("exterior", ""),
                r.get("teeth", ""),
                r.get("mucosa", ""),
                r.get("treatment", ""),
                r.get("notes", "")
            )
        )

    for t in data.get("templates", []):
        conn.execute(
            """INSERT INTO templates (name, fields, text) VALUES (?, ?, ?)""",
            (t.get("name"), t.get("fields"), t.get("text"))
        )

    for q in data.get("quick", []):
        conn.execute(
            """INSERT INTO quick_texts (field, text) VALUES (?, ?)""",
            (q.get("field"), q.get("text"))
        )


def get_all_data() -> Dict[str, Any]:
    """Retrieves full application state from the SQLite database."""
    init_db()
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Clinic
        cur.execute("SELECT * FROM clinic WHERE id = 'main'")
        row = cur.fetchone()
        clinic = {
            "name": row["name"] if row else "Denta Atelier Centrală",
            "address": row["address"] if row else "",
            "taxId": row["tax_id"] if row else "",
            "phone": row["phone"] if row else "",
            "hours": [row["hours_start"] if row else "08:00", row["hours_end"] if row else "18:00"],
            "lunch": [row["lunch_start"] if row else "13:00", row["lunch_end"] if row else "14:00"]
        }
        if row and row["preferences_json"]:
            try:
                clinic.update(json.loads(row["preferences_json"]))
            except (TypeError, ValueError):
                pass

        # Settings
        cur.execute("SELECT * FROM settings WHERE id = 'main'")
        row = cur.fetchone()
        settings = {
            "step": row["step"] if row else 30,
            "duration": row["duration"] if row else 60
        }

        # Doctors
        cur.execute("SELECT * FROM doctors")
        doctors = []
        for r in cur.fetchall():
            doctors.append({
                "id": r["id"],
                "first": r["first"],
                "last": r["last"],
                "email": r["email"],
                "phone": r["phone"],
                "role": r["role"],
                "salary": {
                    "mode": r["salary_mode"],
                    "percentage": r["salary_percentage"],
                    "fixed": r["salary_fixed"]
                }
            })

        # Patients
        cur.execute("SELECT * FROM patients")
        patients = []
        for r in cur.fetchall():
            patients.append({
                "id": r["id"],
                "first": r["first"],
                "last": r["last"],
                "phone": r["phone"],
                "sex": r["sex"],
                "birth": r["birth"],
                "nid": r["nid"],
                "owner": r["owner"],
                "status": r["status"],
                "shared": bool(r["shared"])
            })

        # Appointments
        cur.execute("SELECT * FROM appointments")
        appointments = []
        for r in cur.fetchall():
            appointments.append({
                "id": r["id"],
                "patient": r["patient"],
                "start": r["start_time"],
                "end": r["end_time"]
            })

        # Sections
        cur.execute("SELECT * FROM sections")
        sections = [{"id": r["id"], "name": r["name"]} for r in cur.fetchall()]

        # Services
        cur.execute("SELECT * FROM services")
        services = [{"id": r["id"], "section": r["section"], "name": r["name"], "price": r["price"]} for r in cur.fetchall()]

        # Records
        cur.execute("SELECT * FROM records")
        records = {}
        for r in cur.fetchall():
            records[r["patient_id"]] = {
                "diagnostic": r["diagnostic"] or "",
                "complaints": r["complaints"] or "",
                "history": r["history"] or "",
                "exterior": r["exterior"] or "",
                "teeth": r["teeth"] or "",
                "mucosa": r["mucosa"] or "",
                "treatment": r["treatment"] or "",
                "notes": r["notes"] or ""
            }

        # Templates
        cur.execute("SELECT * FROM templates")
        templates = [{"name": r["name"], "fields": r["fields"], "text": r["text"]} for r in cur.fetchall()]

        # Quick texts
        cur.execute("SELECT * FROM quick_texts")
        quick = [{"field": r["field"], "text": r["text"]} for r in cur.fetchall()]

        return {
            "clinic": clinic,
            "settings": settings,
            "patients": patients,
            "appointments": appointments,
            "sections": sections,
            "services": services,
            "doctors": doctors,
            "records": records,
            "templates": templates,
            "quick": quick
        }
    finally:
        conn.close()


def save_all_data(data: Dict[str, Any]) -> bool:
    """Overwrites application state with received data transactionally."""
    init_db()
    conn = get_connection()
    try:
        with conn:
            # Clinic
            if "clinic" in data:
                c = data["clinic"]
                hours = c.get("hours", ["08:00", "18:00"])
                lunch = c.get("lunch", ["13:00", "14:00"])
                conn.execute(
                    """INSERT OR REPLACE INTO clinic
                       (id, name, address, tax_id, phone, hours_start, hours_end, lunch_start, lunch_end, preferences_json)
                       VALUES ('main', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        c.get("name", ""),
                        c.get("address", ""),
                        c.get("taxId", ""),
                        c.get("phone", ""),
                        hours[0] if len(hours) > 0 else "08:00",
                        hours[1] if len(hours) > 1 else "18:00",
                        lunch[0] if len(lunch) > 0 else "13:00",
                        lunch[1] if len(lunch) > 1 else "14:00",
                        json.dumps({key: c[key] for key in ("sms", "variableHours", "logo") if key in c}, ensure_ascii=False)
                    )
                )

            # Settings
            if "settings" in data:
                s = data["settings"]
                conn.execute(
                    """INSERT OR REPLACE INTO settings (id, step, duration)
                       VALUES ('main', ?, ?)""",
                    (s.get("step", 30), s.get("duration", 60))
                )

            # Doctors
            if "doctors" in data:
                conn.execute("DELETE FROM doctors")
                for d in data["doctors"]:
                    sal = d.get("salary", {})
                    conn.execute(
                        """INSERT INTO doctors
                           (id, first, last, email, phone, role, salary_mode, salary_percentage, salary_fixed)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            d.get("id"),
                            d.get("first"),
                            d.get("last"),
                            d.get("email"),
                            d.get("phone"),
                            d.get("role"),
                            sal.get("mode", "percent"),
                            sal.get("percentage", 25),
                            sal.get("fixed", 0)
                        )
                    )

            # Patients
            if "patients" in data:
                conn.execute("DELETE FROM patients")
                for p in data["patients"]:
                    conn.execute(
                        """INSERT INTO patients
                           (id, first, last, phone, sex, birth, nid, owner, status, shared)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            p.get("id"),
                            p.get("first"),
                            p.get("last"),
                            p.get("phone"),
                            p.get("sex"),
                            p.get("birth"),
                            p.get("nid", ""),
                            p.get("owner", "u1"),
                            p.get("status", "open"),
                            1 if p.get("shared") else 0
                        )
                    )

            # Appointments
            if "appointments" in data:
                conn.execute("DELETE FROM appointments")
                for a in data["appointments"]:
                    conn.execute(
                        """INSERT INTO appointments (id, patient, start_time, end_time)
                           VALUES (?, ?, ?, ?)""",
                        (a.get("id"), a.get("patient"), a.get("start"), a.get("end"))
                    )

            # Sections
            if "sections" in data:
                conn.execute("DELETE FROM sections")
                for sec in data["sections"]:
                    conn.execute(
                        """INSERT INTO sections (id, name) VALUES (?, ?)""",
                        (sec.get("id"), sec.get("name"))
                    )

            # Services
            if "services" in data:
                conn.execute("DELETE FROM services")
                for srv in data["services"]:
                    conn.execute(
                        """INSERT INTO services (id, section, name, price)
                           VALUES (?, ?, ?, ?)""",
                        (srv.get("id"), srv.get("section"), srv.get("name"), srv.get("price"))
                    )

            # Records
            if "records" in data:
                conn.execute("DELETE FROM records")
                for pid, r in data["records"].items():
                    conn.execute(
                        """INSERT INTO records
                           (patient_id, diagnostic, complaints, history, exterior, teeth, mucosa, treatment, notes)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            pid,
                            r.get("diagnostic", ""),
                            r.get("complaints", ""),
                            r.get("history", ""),
                            r.get("exterior", ""),
                            r.get("teeth", ""),
                            r.get("mucosa", ""),
                            r.get("treatment", ""),
                            r.get("notes", "")
                        )
                    )

            # Templates
            if "templates" in data:
                conn.execute("DELETE FROM templates")
                for t in data["templates"]:
                    conn.execute(
                        """INSERT INTO templates (name, fields, text) VALUES (?, ?, ?)""",
                        (t.get("name"), t.get("fields"), t.get("text"))
                    )

            # Quick texts
            if "quick" in data:
                conn.execute("DELETE FROM quick_texts")
                for q in data["quick"]:
                    conn.execute(
                        """INSERT INTO quick_texts (field, text) VALUES (?, ?)""",
                        (q.get("field"), q.get("text"))
                    )
        return True
    finally:
        conn.close()


def reset_to_seed():
    """Resets the database completely to initial seed data."""
    init_db()
    conn = get_connection()
    try:
        with conn:
            conn.executescript("""
            DELETE FROM clinic;
            DELETE FROM settings;
            DELETE FROM doctors;
            DELETE FROM patients;
            DELETE FROM appointments;
            DELETE FROM sections;
            DELETE FROM services;
            DELETE FROM records;
            DELETE FROM templates;
            DELETE FROM quick_texts;
            """)
            seed_data(conn, DEFAULT_SEED)
    finally:
        conn.close()
