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

1. Rulează, în ordine, migrările [`001_clinic_state.sql`](supabase/migrations/001_clinic_state.sql), [`002_team_access.sql`](supabase/migrations/002_team_access.sql), [`003_single_admin_access.sql`](supabase/migrations/003_single_admin_access.sql) și [`004_registration_approval.sql`](supabase/migrations/004_registration_approval.sql) în SQL Editor-ul Supabase. Pentru o instalare existentă, aplică doar migrările care nu sunt încă rulate.
2. În **Authentication → URL Configuration**, adaugă URL-ul final Vercel la **Site URL** și **Redirect URLs**.
3. Activează Email, **Allow new users to sign up** și **Confirm email** în setările Authentication. Configurează SMTP pentru confirmările Supabase în producție. Înregistrează și confirmă adresa `chathot000@gmail.com`; migrarea `004` recunoaște această adresă confirmată ca administrator. Administratorii existenți sunt păstrați. Un vizitator nou nu mai devine administrator doar pentru că s-a înregistrat primul.
4. Publică folderul curent pe Vercel. Fișierele `supabase-config.js` și `supabase-client.js` sunt servite automat împreună cu site-ul.
5. Pagina de autentificare apare înainte de calendar și include **Înregistrare / Register**. Utilizatorii noi confirmă emailul și așteaptă aprobarea administratorului. Numai administratorii pot aproba conturi din **Utilizatori → Vezi și aprobă cererile**.

Tabelul `clinic_state` păstrează starea completă a clinicii într-un document JSON comun. Politicile Row Level Security permit citirea și modificarea numai conturilor aprobate. Inițializarea și ștergerea spațiului de lucru sunt rezervate administratorilor.

### Notificări email pentru cereri de acces

Destinatarul notificărilor este fix: **chathot000@gmail.com**. Emailul include adresa solicitantului și instrucțiunile de aprobare; nu include parole, tokenuri sau date medicale. Înregistrarea și aprobarea funcționează și dacă serviciul email este indisponibil.

1. Folosește serviciul de email existent **Brevo** sau, opțional, [Resend](https://resend.com/docs/api-reference/emails/send-email). Pentru [Brevo](https://developers.brevo.com/docs/send-a-transactional-email), ai nevoie de o cheie API și de un expeditor verificat. Cheia API Brevo este diferită de parola SMTP configurată în Supabase. Acest serviciu trimite notificările către administrator; confirmările de cont sunt gestionate separat de Supabase Auth.
2. În variabilele de mediu **server** ale proiectului Vercel (sau ale serverului Python), adaugă valorile din `.env.example`:
   - `REGISTRATION_EMAIL_PROVIDER`: `brevo` sau `resend`.
   - `BREVO_API_KEY`: cheia privată Brevo pentru providerul `brevo`; pentru `resend`, folosește în schimb `RESEND_API_KEY`.
   - `REGISTRATION_EMAIL_FROM`: expeditorul verificat în providerul ales, de exemplu `Denta Atelier <requests@domeniul-tau.md>`.
   - `ACCESS_REQUEST_WEBHOOK_SECRET`: un secret aleatoriu de minimum 32 de caractere, generat cu `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`.
3. Publică versiunea actualizată a proiectului. Endpointul `POST /api/access-request` este disponibil în Vercel și în serverul Python. Valorile nu se pun în `supabase-config.js` sau în Git. Serverul Python citește variabilele mediului; nu încarcă automat fișiere `.env`.
4. În [Supabase Database Webhooks](https://supabase.com/docs/guides/database/webhooks), creează un webhook pe tabelul **public.clinic_users**, numai pentru evenimentul **INSERT**:
   - Method: **POST**.
   - URL: adresa HTTPS publică a aplicației, urmată de `/api/access-request`.
   - Header `Content-Type`: `application/json`.
   - Header `Authorization`: `Bearer ` urmat de aceeași valoare `ACCESS_REQUEST_WEBHOOK_SECRET`.
   - Timeout: **10000 ms**.
5. Verifică folosind un cont de test cu o adresă pe care o controlezi: înregistrare → confirmare email → autentificare blocată până la aprobare → cerere vizibilă în Utilizatori → notificare primită la chathot000@gmail.com → aprobare → autentificare reușită.

Nu alege `auth.users` pentru webhook: acel tabel conține câmpuri de autentificare care nu sunt necesare notificărilor. Endpointul acceptă numai evenimente pentru `public.clinic_users` și cere secretul serverului. Pentru Resend, reîncercările aceleiași cereri folosesc cheia de idempotency bazată pe ID-ul contului. Pentru Brevo, verifică jurnalul de livrare înainte de retrimitere, deoarece aceasta poate produce o notificare duplicată.

Dacă emailul nu ajunge, verifică istoricul webhookului din schema `net` și jurnalul providerului de email. Codul `401` indică un secret nepotrivit, `503` o configurare lipsă, iar `502` o problemă de trimitere. Remediază configurația și retrimite evenimentul dintr-un mediu de încredere; webhookul nu promite reîncercări automate. Cererea rămâne disponibilă pentru aprobare în aplicație indiferent de livrarea notificării.

---

## 5. Salvarea și restaurarea copiilor de rezervă (Backups)

- Din aplicație: apasă butonul **⚙** din antet -> **📥 Descarcă Backup JSON**.
- Direct din fișiere: poți copia oricând fișierul `data/denta_atelier.db` pe un stick USB sau în Google Drive/iCloud pentru siguranță maximă.
