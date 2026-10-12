# Blåsvarta Spår – GitHub Pages med matchdata

Det här paketet är en startintegration som publicerar `data/matches.json` via GitHub Actions och läser den från `index.html`. Matchkort visar endast spelarinsatser som leverantören faktiskt returnerar; saknade värden ska inte uppskattas.

## 1. Välj dataleverantör och skapa API-nyckel

Paketet använder API-Football v3 som första integration eftersom dess API dokumenterar matchresultat och spelarsiffror per match, inklusive betyg där de finns. API:et har en gratisnivå med begränsningar; kontrollera aktuell täckning för Cypern, Finland, Island, MLS, Belgien och Thailand samt pris/kvot innan du förlitar dig på det. Se:
- https://www.api-football.com/pricing/
- https://www.api-football.com/documentation-v3
- https://www.api-football.com/news/post/fifa-world-cup-2026-guide-to-using-data-with-api-sports

**Jag kan inte skapa en API-nyckel åt dig eller verifiera din kontotäckning här.** Skapa en nyckel hos leverantören om du vill använda denna integration.

## 2. Lägg in nyckeln i GitHub – inte i HTML

I GitHub-repot:
1. Öppna **Settings → Secrets and variables → Actions**.
2. Välj **New repository secret**.
3. Namn: `API_FOOTBALL_KEY`.
4. Värde: din API-Football-nyckel.
5. Spara.

Lägg aldrig nyckeln i `index.html`, `players.json` eller annan publik fil.

## 3. Ladda upp filerna till samma repo

Kopiera följande från paketet till roten i ditt GitHub Pages-repo och committa:
- `index.html` (ersätt befintlig)
- `players.json`
- `scripts/fetch_matches.py`
- `.github/workflows/update-matches.yml`
- `data/matches.json`

Gå sedan till **Actions → Uppdatera matchdata → Run workflow**. När körningen är klar publiceras JSON-filen i repot. Workflowen försöker sedan uppdatera den var sjätte timme.

## 4. Kontrollera spelarlistan

`players.json` har laguppgifter hämtade från din befintliga HTML-fil. De kan vara inaktuella. Verifiera aktuellt lag för varje spelare och uppdatera `team` innan första körningen. Teamnamn kan variera mellan dataleverantörer.

Viktigt: skriptet försöker matcha exakt spelarnamn bland matchens spelare. Om namn eller lag inte matchar kommer ingen spelarrad att visas; detta är avsiktligt för att undvika falska resultat. Leverantörens täckning kan variera per liga och match. Granska varningarna i Actions-loggen.

## 5. Begränsningar och kontroll

- GitHub Actions behöver vara aktiverat för repot och ha rätt att pusha till branchen.
- För GitHub Pages från `main`/`docs`, anpassa `data/matches.json`-sökvägen om publiceringsroten skiljer sig.
- `FOOTBALL_SEASON` står som `2026` i workflowen. För säsonger som startar under 2025 men spelas 2026 (t.ex. vissa europeiska ligor) kan rätt säsongsparameter vara `2025`; täckning måste verifieras och kan kräva ligaspecifik säsongslogik.
- Spelarstatistik, särskilt rating, kan saknas i vissa ligor. Saknade fält visas som `–`.
- `touches`/passningsdetaljer är inte identiska mellan leverantörer. Den här integrationen visar bara de fält som faktiskt finns i svaret.
- Gratis API-kvoter kan snabbt ta slut eftersom varje match behöver spelardata. Om du har många matcher, använd cache och kontrollera förbrukningen.
- Den här koden är en första integration och behöver testas i ditt GitHub-repo med din API-nyckel och ligatäckning. Den kan inte visa live-data förrän workflowen körs framgångsrikt.

## Felsökning

- `Missing API_FOOTBALL_KEY`: skapa repository secret med exakt det namnet.
- `401/403`: nyckel felaktig eller åtkomst/plan otillräcklig.
- Inga matcher: verifiera laguppgifter, säsong, datumfönster och API-täckning.
- `git push` nekas: kontrollera repository Actions permissions och branch protection.
