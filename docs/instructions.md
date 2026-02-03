# MISSION: Project "OpenMercura" (The Zero-Cost Clone)

## 1. OBJECTIVE
You are tasked with finalizing a clone of the startup "Mercura" (YC W25).
**CRITICAL CONSTRAINT:** You must mimic functionality using ONLY free tools, open-source libraries, and the existing DeepSeek/OpenRouter connection.
- **FORBIDDEN:** Paid APIs, subscription SaaS, voice bots, individual model fine-tuning.
- **PERMITTED:** "Free tier" APIs, Web Scraping (legal/public only), CSV/Excel for data interchange, standard OAuth (Google/GitHub).

## 2. ARCHITECTURAL CLEANUP (High Priority)
*Before writing new features, you must stabilize the base.*

### A. Resolve Frontend Schizophrenia
**Context:** The repo currently has both `frontend/` (Vite/React) and `my-app/` (Next.js).
**Action:**
1. ANALYZE both directories to see which has more active code.
2. CONSOLIDATE into a single `frontend/` directory.
   - *Recommendation:* Keep `my-app` (Next.js) if Server Side Rendering is needed for SEO/Speed, otherwise stick to Vite for simplicity.
   - **MIGRATE** any unique components from the deleted folder to the survivor.
3. DELETE the redundant folder.
4. UPDATE `package.json` and `docker-compose.yml` to reflect the single frontend source.

### B. Standardize The "Dual Architecture"
Ensure the **Web App** and **Chrome Extension** are distinct but share logic where possible.
1. **Shared Logic:** Create a `shared/` or `packages/` folder for types and utility functions used by both the extension and the web app.
2. **Build Process:** Ensure `npm run build` generates both the Web App build and the Chrome Extension `dist` folder without conflict.

---

## 3. FEATURE IMPLEMENTATION (The "Mercura" Mimic)

You must implement the following core workflows using **Free Workarounds**:

### Feature 1: Intelligent Data Capture (The "Free" CRM)
*Mercura Feature:* Auto-updates CRM from unstructured data.
*Our Free Implementation:*
- **Input:** Allow users to paste raw text or upload CSVs.
- **Process:** Use the current `gemini_service.py` (or switch to `deepseek_service.py` using our free API) to parse text into structured JSON.
- **Storage:** Save to local database (Postgres/SQLite).

### Feature 2: Competitor Analysis
*Mercura Feature:* Real-time competitor tracking.
*Our Free Implementation:*
- **Logic:** Create a scraper/search utility (using free search APIs or direct requests) to fetch public meta-tags and headers from a list of competitor URLs.
- **Output:** Generate a comparison table in the UI (Pricing, Features, Keywords).
- **Constraint:** If a site blocks scraping, handle gracefully with "Data Unavailable" rather than crashing.

### Feature 3: Smart Search & Retrieval
*Mercura Feature:* "Chat with your data."
*Our Free Implementation:*
- Implement a basic RAG (Retrieval-Augmented Generation) system using:
  - Vector DB: **ChromaDB** or **FAISS** (Local/Open Source).
  - Embeddings: Use a lightweight, free huggingface model (run locally).
  - **NO** paid vector cloud services (Pinecone, etc.).

---

## 4. THE AUTONOMOUS LOOP (Strict Protocol)

You will execute the following loop for each feature.

**STATE 1: ANALYZE & PLAN**
- Read current files.
- Identify missing logic based on the "Mercura" mimicry requirements.
- Create a test case that fails (TDD).

**STATE 2: CODE (Junior Dev Mode - DeepSeek-V3)**
- Write the code to pass the test.
- **CONSTRAINT:** Do not delete existing documentation (`PROJECT_SUMMARY.md`, etc.). Update them if architecture changes.

**STATE 3: VERIFY (The Gatekeeper)**
- Run `npm test` or `pytest`.
- **IF PASS:** Move to next feature.
- **IF FAIL:** Read error.
  - If syntax error: Fix immediately.
  - If logic error: **ESCALATE** to "Senior Architect" (DeepSeek-R1) to re-plan the module.

**STATE 4: EXIT STRATEGY (Anti-Loop)**
- **Max Retries:** You have 3 attempts to fix a specific bug.
- **The "Unsolvable" Condition:** If a feature requires a paid tool and you cannot find a 100% free valid workaround after 3 attempts:
  1. **STOP** trying to build it.
  2. **COMMENT OUT** the failing code.
  3. **LOG** it in `UNIMPLEMENTED_FEATURES.md` with the reason: "Requires paid resources."
  4. Move to the next task.

---

## 5. SUCCESS CRITERIA (Definition of Done)
1. Only **ONE** frontend directory exists.
2. `npm run build` completes successfully for both Web App and Extension.
3. `pytest` passes for all backend services.
4. The system starts up locally via `docker-compose up` without crashing.
5. A notification is printed to the console: "Project OpenMercura Ready."

6. THE "RALPH WIGGUM" PROTOCOL (Recursive Persistence)
Core Directive: You are a "Ralph Loop." You do not stop when you think you are done. You stop only when the machine confirms you are done.

The Loop: CODE -> TEST -> FAIL -> FIX -> REPEAT

The Exit: You may ONLY mark a task as "COMPLETE" when:

npm test passes 100%.

The browser console shows ZERO red errors.

npm run build generates a production build without warnings.

7. DESIGN SYSTEM: "Industrial B2B" (Anti-Generic)
Constraint: Do NOT build a "Vibe Coded" website. No purple gradients. No rounded glassmorphism.

Aesthetic Rules (Mimic Mercura YC W25):

Palette: High-contrast Industrial.

Primary: Deep Navy / Charcoal (Trust, Engineering).

Accent: Safety Orange or Electric Blue (Action, Alerts).

Background: Stark White or Light Gray (Not dark mode by default).

Typography: Inter, Roboto, or similar "System" fonts. Tight spacing. High legibility.

Reference: Before styling, browse dribbble.com/tags/b2b_dashboard or saasinterface.com to find a "logistics" or "ERP" reference. Copy that layout structure.

Banned: "AI Sparkles", excessive gradients, "Glass" effects, default Bootstrap look.

**START NOW.**