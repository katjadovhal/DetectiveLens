# DetectiveLens App Refactoring - Summary

## Durchgeführte Änderungen

### Backend - API-Endpunkte

#### Neue Endpunkte:
1. **POST /api/v1/onboarding/create-user** - Erstellt einen neuen Benutzer mit Onboarding-Daten
2. **GET /api/v1/users** - Listet alle existierenden Benutzer auf
3. **GET /api/v1/users/{user_id}** - Holt Benutzerdaten
4. **GET /api/v1/challenges/users/{user_id}/daily** - Holt den täglichen Challenge (zufällig ausgewählt)
5. **GET /api/v1/challenges/users/{user_id}/next-practice** - Holt den nächsten Practice Challenge basierend auf Skills
6. **POST /api/v1/challenges/{challenge_id}/start/{user_id}** - Startet einen Challenge

#### Aktualisierte Endpunkte:
- **GET /api/v1/home/{user_id}** - Benötigt nun user_id
- **GET /api/v1/profiles/{user_id}** - Benötigt nun user_id
- **PATCH /api/v1/profiles/{user_id}** - Benötigt nun user_id

### Backend - Datenmodell

#### Benutzer (users):
```json
{
  "id": "user-id",
  "username": "benutzername",
  "email": null,
  "createdAt": "ISO-Timestamp",
  "lastActiveAt": "ISO-Timestamp"
}
```

#### Profil (profiles):
```json
{
  "id": "profile-id",
  "userId": "user-id",
  "avatarId": "avatar-detective-1",
  "displayName": "Benutzername",
  "currentLevel": 1,
  "totalXp": 0,
  "currentLevelXp": 0,
  "dailyStreak": 0,
  "onboardingCompleted": true,
  "colorBlindness": false,
  "lastChallengeId": null,
  "lastChallengeProgress": null,
  "settings": { "notifications": true, "sound": true, "privacy": false }
}
```

#### Skill-Profile (skill_scores):
- Jeder Benutzer hat ein Skill-Profil für jede Skill-Kategorie
- Skill-Score liegt zwischen -1 und 1
- Wird nach jedem abgeschlossenen Challenge aktualisiert

### Challenge-Empfehlungs-Algorithmus

**Für Practice-Mode:**
1. Wenn keine Challenges abgeschlossen: Wähle zufällig
2. Sonst: Berechne Score für jeden verfügbaren Challenge basierend auf:
   - **Weakness Signal (70%)**: Zeigt negative Skills, die trainiert werden sollen
   - **Difficulty Fit (30%)**: Zeigt ob Schwierigkeit zum aktuellen Skill passt

```python
score = 0.7 * weakness_signal + 0.3 * difficulty_fit_signal
```

**Für Daily Challenge:**
- Ein Challenge wird einmal täglich zufällig aus den "isDailyEligible" Challenges gewählt
- Cache verhindert mehrfaches Picking am selben Tag

### Frontend - Neue Seiten

1. **Start Page (/)** - Willkommensmeldung mit zwei Optionen
2. **Onboarding Page (/onboarding)** - Benutzererstellung mit:
   - Name-Eingabe
   - Altersangabe
   - Farbblindheits-Toggle
   - Avatar-Auswahl
   - Spezielle Bestätigung für Nutzer unter 7 Jahren
3. **User Selection (/select-user)** - Auswahl aus existierenden Benutzern
4. **Challenge Staging (/challenge-staging)** - Wahl zwischen Daily/Practice
5. **Updated Challenge Page** - Nimmt userId und mode Parameter

### Daten Bereinigung

✅ **Demo-Benutzer entfernt:**
- Datei `backend/app/services/demo_user.py` gelöscht
- DEMO_USER_ID aus constants entfernt
- store.json geleert

✅ **Felder entfernt:**
- `selfReportedLevel` aus Profilen entfernt
- Age wird nicht persistiert (nur für Validierung verwendet)

### Avatare

Vier verfügbare Avatare:
- `avatar-detective-1` 🕵️‍♂️
- `avatar-detective-2` 🕵️‍♀️
- `avatar-detective-3` 👨‍🔬
- `avatar-detective-4` 👩‍🔬

### Willkommensmeldungen

**Start Page:**
- Titel: "Welcome to DetectiveLens!"
- Beschreibung: "Some pictures lie. Learn to spot the cues and catch them all."

### Nächste Schritte

Das Projekt ist implementiert und einsatzbereit. Um die App zu testen:

```bash
# Terminal 1: Backend starten
cd backend
uvicorn app.main:app --reload

# Terminal 2: Frontend testen (öffne Browser)
http://localhost:8000
```

Die App leitet automatisch auf die Start-Seite weiter.

