# Denta Atelier — Sistem de Gestiune Clinică Stomatologică

Aplicație completă pentru gestiunea unei clinici stomatologice: calendar de programări, evidență pacienți, carte medicală cu semnătură electronică, catalog de tarife și devize de tratament, administrare clinică, salarii medici și exporturi profesionale (PDF și Excel XLSX).

---

## 🚀 Pornire Rapidă Locală

1. **Pe macOS:**
   - Faceți dublu-click pe fișierul `PORNEȘTE.command`.
   - Sau rulați în terminal:
     ```sh
     python3 server.py
     ```
2. Deschideți în browser adresa:
   ```
   http://localhost:8080
   ```

Aplicația este conectată automat la baza de date locală **SQLite** localizată în `data/denta_atelier.db`.

---

## 🗄️ Baza de Date & Persistență

- **Local:** Folosește **SQLite** (`data/denta_atelier.db`). Orice pacient adăugat, programare salvată sau fișă completată se scrie direct în baza de date pe disc și este disponibilă tuturor dispozitivelor din rețeaua internă.
- **Offline Fallback:** Dacă serverul este oprit, aplicația folosește automat memoria locală `localStorage` fără să blocheze utilizatorul.
- **Status în Antet:** Indicatorul din dreapta sus afișează `● SQLite conectat`. Apăsați pe el sau pe `⚙` pentru opțiuni de backup JSON, reîncărcare sau resetare.
- **Pentru punerea online:** Consultați ghidul dedicat din [`DEPLOYMENT.md`](file:///Users/sergiu/Desktop/Denta-Atelier-Perfectionata/DEPLOYMENT.md). Se recomandă o bază de date **PostgreSQL** (cum ar fi Supabase, Neon sau Railway).

---

## 🩺 Funcționalități Incluse

- **Calendar săptămânal:** Program de lucru, ore nefuncționale hașurate, navigare facilă, mini-calendar, creare/editare/ștergere programări.
- **Registru Pacienți:** Căutare rapidă după nume sau telefon, adăugare și editare fișă pacient, IDNP, mascare telefon, export jurnal vizite.
- **Tarife & Planuri de tratament:** Catalog structurat pe secțiuni clinice (Terapie, Chirurgie, Ortodonție etc.), generator deviz cu total dinamic și export PDF.
- **Cartea Medicală:** Anamneză, acuze, examen exterior, status dentar, mucoasă, șabloane clinice, texte rapide, export PDF și flux de deblocare prin semnătură electronică desenată direct pe ecran.
- **Administrare Clinică:** Date de identificare (IDNO, adresă, telefon), orar de funcționare și pauză de masă, echipă medicală, calcul automat de salarii (procentual, fix sau hibrid), parole temporare.

---

## 🌐 Publicare Online

Pentru detalii complete despre găzduirea gratuită sau cloud (Render, Railway, Fly.io, Vercel + Supabase), citiți [`DEPLOYMENT.md`](file:///Users/sergiu/Desktop/Denta-Atelier-Perfectionata/DEPLOYMENT.md).

---

## ☁️ Activare Supabase (necesar o singură dată)

Aplicația este configurată pentru proiectul Supabase primit. Pentru a activa salvarea reală în cloud:

1. În Supabase, deschide **SQL Editor** → **New query**.
2. Rulează, în ordine, migrările pentru date și acces `001`–`004` din `supabase/migrations/`. Pentru notificări email, configurează Vault și aplică și `005_access_request_notifications.sql`, conform ghidului de publicare. La o instalare existentă, aplică doar migrările care lipsesc.
3. În setările **Authentication**, activează providerul Email și **Allow new users to sign up**. Păstrează **Confirm email** activ și configurează URL-ul de redirect al site-ului. Configurează și SMTP pentru mesajele de confirmare Supabase în producție.
4. Înregistrează și confirmă contul `chathot000@gmail.com`. Migrarea `004` îi acordă rolul de administrator numai după confirmarea adresei. Administratorii existenți își păstrează accesul.
5. Pe ecranul de pornire, apasă **Înregistrare / Register**. Conturile noi rămân în așteptare până la aprobarea din **Utilizatori → Vezi și aprobă cererile**. Confirmarea emailului nu aprobă accesul la datele clinicii.
6. Pentru notificări automate la **chathot000@gmail.com**, configurează serviciul email și webhookul descrise în [DEPLOYMENT.md](DEPLOYMENT.md#notificări-email-pentru-cereri-de-acces). Fără acea configurare, cererile sunt vizibile în aplicație, dar notificările email nu se trimit.

Cheia din `supabase-config.js` este o cheie **publishable** destinată browserului; nu adăuga niciodată cheia `service_role` în proiect sau în Vercel.
