# 🏀 March Madness Bracket Tracker

A self-contained, single-file bracket scoring calculator for friend groups.
Firebase-backed for live sync across all browsers so everyone sees the leaderboard update in real time.

## Features

- **Multiple brackets per person** (up to 3) with editable names
- **Fibonacci scoring**: R64=1, R32=2, S16=3, E8=5, FF=8, CHAMP=13
- **+2 upset bonus** when winning seed beats a team seeded 3+ lower (seed diff ≥ 3, e.g. 11 over 6 ✅, 9 over 8 ❌)
- **Right winner wins** — picks score based on the winning team advancing, regardless of who they actually beat
- **Live leaderboard** ranked by best bracket per participant, expandable to show all brackets
- **Admin results panel** — one source of truth for game results, shared across all brackets
- **Live sync via Firebase** — all browsers connected to the same database update instantly
- **Offline fallback** — works on localStorage if Firebase is not configured, and queues writes when offline
- **Export / Import JSON** — back up state and restore from a snapshot
- **🤖 ESPN bracket importer** — paste your ESPN bracket text and let GPT auto-fill all 63 picks (requires an OpenAI API key)

---

## Firebase Setup

Without Firebase the app still works, but data is stored in the browser only, so other people opening the URL see an empty app. Follow these steps once to enable shared, real-time state.

### Step 1 — Create a Firebase project

1. Go to [console.firebase.google.com](https://console.firebase.google.com)
2. Click **Add project**, give it a name (e.g. `march-madness-tracker`), disable Google Analytics (not needed), click **Create project**

### Step 2 — Create a Realtime Database

1. In the left sidebar click **Build → Realtime Database**
2. Click **Create Database**
3. Choose a region (any is fine), click **Next**
4. Select **Start in test mode** → click **Enable**

   > Test mode allows read/write from anyone for 30 days. See [Locking down rules](#locking-down-database-rules) below when you're done setting up.

### Step 3 — Get your config

1. Click the gear icon ⚙️ next to *Project Overview* → **Project settings**
2. Scroll down to **Your apps** → click the **</>** (Web) icon
3. Register the app with any nickname, skip Firebase Hosting
4. Copy the `firebaseConfig` object shown — it looks like:

```js
const firebaseConfig = {
  apiKey:            "AIzaSy...",
  authDomain:        "your-project.firebaseapp.com",
  databaseURL:       "https://your-project-default-rtdb.firebaseio.com",
  projectId:         "your-project",
  storageBucket:     "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId:             "1:123456789:web:abc123"
};
```

### Step 4 — Paste the config into index.html

Open `index.html` and find the `FIREBASE_CONFIG` block near the top of the `<script>` section (~line 230):

```js
const FIREBASE_CONFIG = {
  apiKey:            "PASTE_YOUR_API_KEY",
  authDomain:        "PASTE_YOUR_PROJECT_ID.firebaseapp.com",
  databaseURL:       "https://PASTE_YOUR_PROJECT_ID-default-rtdb.firebaseio.com",
  ...
};
```

Replace each `PASTE_YOUR_...` value with the real values from your Firebase config. Commit and push — GitHub Pages will redeploy automatically.

### Step 5 — Verify

Open the URL in two different browsers. Add a participant in one — it should appear instantly in the other. The header should show a green **Live** dot.

---

## Locking down database rules

Test mode expires after 30 days. Before it does, update your rules so only your group can write. The simplest option — allow reads and writes from anywhere (fine for a private friend group since the database URL isn't publicised):

```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

To set rules: Firebase Console → Realtime Database → **Rules** tab → paste and **Publish**.

---

## Usage

### Participants tab
- Add each participant by name
- Each participant starts with one bracket; click **+ Bracket** to add up to 3
- Rename brackets with ✏️ (e.g. "Safe Picks", "Chaos Bracket")

### Picks tab
- Select a participant and bracket from the dropdowns
- Use the round tabs (R64 → CHAMP) to navigate
- R64 slots are labeled with the standard matchup (e.g. "1 vs 16") as a hint
- R32–E8 slots are unlabeled since matchups depend on prior results
- FF and CHAMP use Region + Seed selectors
- Click **💾 Save Picks** (also auto-saves when switching rounds)
- ✓ indicators appear next to picks that have already scored

#### 🤖 Importing picks from ESPN

1. Go to your ESPN bracket page and open the bracket you want to import
2. Select all text on the page (**Ctrl+A** / **Cmd+A**) and copy it
3. In the Picks tab, select the participant and bracket you want to fill
4. Click **🤖 Import ESPN**
5. Enter your **OpenAI API key** (stored in your browser only, never leaves your device except to OpenAI)
6. Paste the copied bracket text into the textarea
7. Click **Parse Bracket** — GPT will extract all 63 picks and show a count per round
8. Review the results, then click **Apply to Bracket**

> **Cost:** A single parse call uses about 2,000–4,000 tokens. With `gpt-4o-mini` this is a fraction of a cent. `gpt-4o` is ~10× more expensive but rarely needed for this task.
>
> **Missing picks:** If GPT can't determine some picks (usually the CHAMP pick), the remaining slots stay empty. Fill them in manually using the round tabs.
>
> **API key safety:** The key is stored in `localStorage` under `mm_oai_key` and is only sent directly to `api.openai.com`. It is not stored in Firebase or shared with anyone.

### Results tab (admin)
- One person enters game results: Round, Winner Region + Seed, Loser Region + Seed
- Upset bonus is calculated automatically
- Scores and the leaderboard update on every connected browser instantly

### Export / Import
- **Export** downloads a JSON snapshot of all data
- **Import** restores from a snapshot (replaces current data — confirm prompt shown)

---

## Customizing scoring

All scoring constants are at the top of the `<script>` block in `index.html`:

```js
const ROUND_POINTS    = { R64: 1, R32: 2, S16: 3, E8: 5, FF: 8, CHAMP: 13 };
const UPSET_BONUS     = 2;
const UPSET_THRESHOLD = 3;   // strictly: winnerSeed − loserSeed must exceed this
```

Change any value and the leaderboard recalculates immediately on next load.
