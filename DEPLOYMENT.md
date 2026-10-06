# Ghid Bază de Date & Publicare Online — Denta Atelier

Acest document explică arhitectura bazei de date, diferența dintre rularea locală și publicarea online, precum și pașii recomandați pentru a pune aplicația pe internet.

---

## 1. Ce tip de bază de date ai nevoie?

Pentru o aplicație de clinică stomatologică (pacienți, programări în calendar, fișe medicale, devize de tratament, tarife și medici), ai nevoie de o **Bază de date Relațională (SQL)**:

| Mediu | Baza de date recomandată | De ce? |
| :--- | :--- | :--- |
| **Local (pe calculatorul clinicii)** | **SQLite** (`data/denta_atelier.db`) | • **Configurare zero:** vine integrat direct în Python (`sqlite3`), nu trebuie să instalezi servere separate.<br>• **Fișier unic:** toate datele sunt salvate în siguranță în folderul `data/`.<br>• **Rapid și fiabil:** suportă tranzacții ACID și salvare instantanee. |
| **Online (Internet / Cloud)** | **PostgreSQL** | • **Multi-utilizator concurent:** permite mai multor medici și recepționeri să acceseze și să modifice date simultan de pe telefoane, tablete sau computere de acasă.<br>• **Backup automat:** furnizorii cloud oferă copii de siguranță zilnice automate.<br>• **Securitate & Criptare:** conexiuni criptate SSL (TLS) conforme cu cerințele datelor medicale (GDPR / HIPAA). |

---

## 2. Cum funcționează acum (Modul Local)

Aplicația este deja configurată și gata de utilizare:
1. La pornirea serverului (`python3 server.py` sau dublu-click pe `PORNEȘTE.command`), se inițializează automat baza de date SQLite în:
   ```
   data/denta_atelier.db
   ```
2. Datele inițiale demonstrative sunt populate automat dacă baza este nouă.
3. Orice modificare (programare nouă, editare pacient, modificare tarif, fișă medicală) este trimisă asincron prin `POST /api/data` și salvată în fișierul SQLite.
4. În interfață (antet), există un indicator vizual:
   - **`● SQLite conectat`** — datele sunt salvate direct în baza de date locală.
   - Apăsând pe iconița **`⚙`** sau pe etichetă, poți:
     - Descărca oricând o **copie de rezervă JSON** (`Backup`).
     - Reîncărca datele din baza de date.
     - Reseta datele la starea demo.

---

## 3. Unde poți găzdui baza de date gratuit sau ieftin online?

Pentru o bază de date **PostgreSQL** online, ai următoarele opțiuni excelente:

1. **[Supabase](https://supabase.com)** *(Recomandat)*:
   - Oferă o bază de date PostgreSQL completă gratuit (plan Free generos).
   - Panou de control web modern (poți vedea și edita tabelele direct din browser).
   - Îți oferă un link de conexiune de tipul: `postgresql://postgres:[parola]@db.[proiect].supabase.co:5432/postgres`.
2. **[Neon.tech](https://neon.tech)**:
   - PostgreSQL serverless, gratuit, performanță ridicată.
3. **[Railway](https://railway.app)** sau **[Render](https://render.com)**:
   - Poți porni atât serverul web Python cât și baza de date PostgreSQL într-un singur loc, cu un singur click.

---

## 4. Pași pentru a pune aplicația online

### Varianta A: Render sau Railway (Cea mai simplă)

1. Creează un cont gratuit pe [Render.com](https://render.com) sau [Railway.app](https://railway.app).
2. Încarcă proiectul într-un depozit privat pe **GitHub** (fișierul `.gitignore` va proteja fișierul cu pacienți locali `denta_atelier.db`).
3. Conectează GitHub la Render/Railway:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python3 server.py`
4. În panoul Render/Railway, adaugă un serviciu **PostgreSQL** și copiază variabila `DATABASE_URL` în setările aplicației (Environment Variables).
5. Vei primi un domeniu public HTTPS (ex: `https://denta-atelier.onrender.com`) accesibil de pe orice dispozitiv.

### Varianta B: Vercel + Supabase / Neon

1. Proiectul include deja `vercel.json` și serverless functions în folderul `api/` (`api/data.py`, `api/export-pdf.py`, `api/export-visits.py`).
2. În Vercel, setează variabila de mediu `DATABASE_URL` cu linkul către PostgreSQL din Supabase.

### Configurația implementată: site static + Supabase Auth

Această versiune folosește direct API-ul Supabase din browser, cu autentificare pe email și politici RLS. Nu este nevoie de `DATABASE_URL` sau de cheia `service_role`.

1. Rulează, în ordine, migrarea [`001_clinic_state.sql`](supabase/migrations/001_clinic_state.sql), [`002_team_access.sql`](supabase/migrations/002_team_access.sql) și [`003_single_admin_access.sql`](supabase/migrations/003_single_admin_access.sql) în SQL Editor-ul Supabase.
2. În **Authentication → URL Configuration**, adaugă URL-ul final Vercel la **Site URL** și **Redirect URLs**.
3. În **Authentication → Users**, folosește **Add user** pentru a crea administratorul cu emailul și parola dorite. Primul cont devine automat administrator.
4. Publică folderul curent pe Vercel. Fișierele `supabase-config.js` și `supabase-client.js` sunt servite automat împreună cu site-ul.
5. Această configurare este pentru un singur administrator: pagina de autentificare apare înainte de calendar, nu există opțiune de creare cont în site, iar utilizatorii care nu sunt administratori nu pot citi sau modifica datele.

Tabelul `clinic_state` păstrează starea completă a clinicii într-un document JSON comun. Politicile Row Level Security permit accesul numai contului administratorului.

---

## 5. Salvarea și restaurarea copiilor de rezervă (Backups)

- Din aplicație: apasă butonul **⚙** din antet -> **📥 Descarcă Backup JSON**.
- Direct din fișiere: poți copia oricând fișierul `data/denta_atelier.db` pe un stick USB sau în Google Drive/iCloud pentru siguranță maximă.
