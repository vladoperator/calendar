# Denta Atelier

Aplicație demonstrativă locală pentru o clinică stomatologică. Datele demo se salvează în browser și rămân disponibile după reîncărcare. Este o implementare originală, cu identitate proprie, fără cod, sigle sau active ale produsului analizat.

## Pornire

În acest director, porniți serverul local cu runtime-ul inclus în desktop:

```sh
/Users/sergiu/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 server.py
```

Apoi deschideți `http://localhost:8080`. Alternativ, pe macOS puteți porni aplicația direct cu fișierul `PORNEȘTE.command`.

Serverul include export real XLSX pentru jurnalul vizitelor și PDF pentru documente. Pentru o previzualizare strict statică se poate folosi și `python3 -m http.server 8080`, însă exporturile vor folosi varianta de rezervă din browser.

Pentru revenire la datele demo, ștergeți stocarea locală a site-ului din browser.

## Fluxuri incluse

- Calendar săptămânal cu program de lucru, ore nefuncționale hașurate, navigare, mini-calendar, programări create, editate și șterse, plus golirea săptămânii.
- Pacienți cu căutare, adăugare, editare, telefon mascat și exportul jurnalului de vizite.
- Tarife organizate pe secțiuni, servicii și deviz cu total dinamic și document PDF descărcabil.
- Cartea medicală cu fișă configurabilă, texte rapide, șabloane, export PDF și flux de deblocare prin semnare pentru dosare partajate.
- Administrare cu date de clinică, program și pauză, echipă medicală, parole temporare demonstrative, reguli de salarii, șabloane și preferințe de profil.

## Date demonstrative

Calendarul este pregătit pentru săptămâna 5–11 octombrie 2026. Toate persoanele, telefoanele, adresele și adresele de email sunt date fictive de demonstrație. Fișa Sofiei Test este intenționat blocată: deschideți-o din Cartea medicală și urmați „Adaugă semnătura” pentru a testa întregul flux al documentelor.

## Vercel

Proiectul poate fi importat direct în Vercel ca proiect static, cu presetul `Other`. Nu este necesară comandă de build sau director de ieșire. Funcțiile de calendar, pacienți, tarife, devize și fișe rulează în browser și datele demo sunt persistate local în browserul fiecărui utilizator.
