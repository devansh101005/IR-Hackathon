# Demo Video Script (target 7:45; allowed 5–8 minutes)

| Speaker | Time | Length | Covers |
|---|---|---|---|
| **Devansh Pandey** | 0:00–3:30 | 3:30 | the problem, the engine live (terminal), the code, the web demo and the gate |
| **Anamika Pal** | 3:30–5:35 | 2:05 | the human query set: how we made it, annotator agreement, results on real typing |
| **Abhinav Bachchas** | 5:35–7:35 | 2:00 | evaluation against the baseline, the gate's trade-off, the ablation, the limitations (one live) |
| **Devansh Pandey** | 7:35–7:45 | 0:10 | close |

**PDF rules this video covers:** no slides · the system running live · intermediate output (postings, df/idf, scores) · evaluation against a baseline · one limitation shown live · every member explains their own part.

Each segment lists **Do** (exact click, command or scroll), **Screen shows** (what appears, checked on Devansh's laptop) and **Say** (suggested words; say them in your own way, don't read them word for word). Every number in "Say" is on screen at that moment.

**Timing tip:** practise each part once with a phone stopwatch. The two terminal commands take about 10 seconds to load; keep talking, or cut the wait when editing. If the total goes over 8:00, shorten segment C (the code) first.

---

## Before recording (15 minutes)

1. Laptop **plugged in**, OMEN Gaming Hub → **Performance** mode, Windows notifications **off**, phones on silent, close other apps.
2. Open **two** PowerShell terminals in `E:\IR_Midsem_Hackathon` (VS Code → Terminal → New Terminal, then the split button). In **both** run:
   ```powershell
   $env:PYTHONPATH="src"; $env:PYTHONUTF8="1"; $env:PYTHONIOENCODING="utf-8"
   ```
   Terminal font size ≥ 18 (Ctrl + mouse wheel).
3. **Terminal 1 (server):** `.\.venv\Scripts\python.exe app\server.py` → wait for `Uvicorn running on http://127.0.0.1:8000`. Leave it running.
4. Chrome → `http://127.0.0.1:8000` → **Ctrl + F5** once → zoom **110%** → **light mode** (top-right button says "Dark").
5. **Warm-up:** click every example chip once and switch through S3, G1 and B2. In Terminal 2, run both commands from segment B once. On camera everything should then answer instantly.
6. VS Code tabs open: `src/lipisetu/text/dhvani.py`, `src/lipisetu/retrieval/bm25.py` and `queries/human/sheet_teammate_a.tsv` (for Anamika).
7. Recorder: **Clipchamp → Record & create → Screen** (or Snipping Tool with the mic turned on). Choose **Entire screen** and the **microphone**, and make a 15-second test recording first to check the voice is there.
8. **Refresh the page (F5) right before you press record.** The sound-key card starts on *mausam → M S M* and changes every 4 seconds.

---

# DEVANSH (0:00–3:30)

## A · 0:00–0:35 · The problem
**Do:** start at the top of the page. Point at the four word boxes, then at the key.

**Screen shows:** "One question. Every script." · card *The core idea · Dhvani key*: **mausam · mosam · मौसम · mousam → M S M**.

**Say:**
> "Hi, I'm Devansh, and this is LipiSetu, our project for Track T5. Most Indians type Hindi in Roman letters, and everyone spells it differently: mausam, mosam, mousam. But most Hindi text online is in Devanagari, and a normal search engine matches exact words. So *kal ka mausam* finds nothing about कल का मौसम. We call this the **Script Gap**. Our fix is a sound key, the Dhvani key: all four spellings here, in two scripts, become M S M, and we index that key as its own zone."

## B1 · 0:35–1:10 · Baseline vs LipiSetu (terminal)
**Do:** Terminal 2:
```powershell
.\.venv\Scripts\python.exe -m lipisetu.cli compare "bharat ka samvidhan kab lagu hua" --systems B1,B2,S3
```
**Screen shows:**
```
B1   वित्त मन्त्रालय | भरत व्यास | ...
B2   भरत मिलाप | भरत चक्रवर्ती | अयोध्याकाण्ड
S3   भारतीय संविधान का इतिहास | भारत का संविधान | भारत का संविधान
```
**Say (start while it loads):**
> "This is the real engine on 110,855 Hindi Wikipedia passages from MIRACL. The question is 'when did the constitution come into force', typed in Roman. Normal BM25, B1, can't match Roman words. The obvious fix, B2, transliterates first, and turns *bharat* into भरत, the Ramayana name. Our system, S3, finds the constitution."

## B2 · 1:10–2:15 · Every step with real index values (terminal)
**Do:**
```powershell
.\.venv\Scripts\python.exe -m lipisetu.cli search "kal ka mausam kaisa rahega" --system S3 --explain
```
Scroll the output slowly from the top, stopping at each block.

**Screen shows:** tokens with keys **KL, MSM, RHG** (*ka*, *kaisa* = stop words) → word zone **df=0** for all three → Dhvani zone **KL 12957 / MSM 712 / RHG 293**, idf **2.15 / 5.05 / 5.93** → pooled df → real postings (`MSM df=712 59#49 tf=1 [15] ...`) → #1 **भारतीय मौसम विज्ञान विभाग**, `proximity=0.33 (window 4)`, `7.0 ms`.

**Say:**
> "Here's every step. Stop words are removed, and each word gets its sound key. In the normal word zone, all three words have df zero: these spellings never appear. But in the Dhvani zone they match: MSM is in 712 passages. idf is log N over df, so the rare key RHG counts more than the common KL. These are real postings: passage, term frequency, positions. We add BM25 from each zone with weights tuned on the train split, plus a proximity boost: here the words are within a 4-word window. The top result is the Meteorological Department, in 7 milliseconds."

## C · 2:15–2:40 · The code
**Do:** VS Code → `dhvani.py`, scroll the rules at the top. Then `bm25.py` → select `pooled_df_table`.

**Say:**
> "The key is written from scratch. Each rule exists because Roman spelling can't show the difference: *kh* equals *k*, retroflex equals dental, w equals v, and vowels are dropped. And this is pooled df: each spelling alone looks rare, so we give it the df of its whole sound class. It's Pirkola's idea from cross-language IR, applied to spellings."

## D · 2:40–3:30 · Web demo and the gate
**Do 1:** Chrome → click the example chip **भारत का संविधान कब लागू हुआ** (system **S3**).
**Screen shows:** strip *"Same question, typed in Roman"*: **LipiSetu: 6 of the top 10 are the same · RBO 0.57** vs **Transliterate + BM25: 0 · RBO 0.00**.
**Say:** "The page asks the same question in Roman and compares the two top-10 lists: 6 of 10 match for us, none for the baseline."

**Do 2:** click **LipiSetu cascade G1** → type `congress party ka leader kaun hai` → **Search** → in the right panel scroll to **03 Pooled df**, then **05 Gate**.
**Screen shows:** **congress: own df 5 → pooled df 1,152** · Gate **"Yes. Probability 0.65 is above the threshold 0.47…"**
**Say:** "Pooled df, live: *congress* in Roman is in 5 passages, its sound class in 1,152. G1 is our cascade: a small gate, trained on the train split, decides if the slow neural stage is worth running. Here: yes, 0.65 against 0.47."

**Do 3:** type `kal ka mausam` → **Search** → right panel **05 Gate**.
**Screen shows:** **"No. Probability 0.30 is below the threshold 0.47…"**
**Say:**
> "For *kal ka mausam* the fast answer is already confident, so no neural call. Now Anamika will show how real people type."

---

# ANAMIKA (3:30–5:35)

## F1 · 3:30–4:05 · How we built the human query set
**Do:** VS Code → tab `queries/human/sheet_teammate_a.tsv` (my own sheet). Point at row 1, then row 21, then row 26.

**Screen shows:**
- row 1: `मध्य प्रदेश कितने भागों में विभाजित है?` → `madhya pradesh kitne bhago me vibhajit hai`
- row 21: `भारतीय समय कौन जारी करता है?` → roman `bharatiya samay kaun jari karta hai`, code-mixed `india ka time kon jari krta h`, English `who issues indian standard time?`
- row 26: code-mixed `sachin tendulkar ne january 2011 me test cricket ka 51 century kis country ke against banaya tha`

**Say:**
> "Hi, I'm Anamika. The Roman test questions so far were generated by a program, and real people don't type like a program. So Devansh, Abhinav and I each took the same 60 test questions and typed every one in Roman on our own, the way we'd type on WhatsApp, with no transliteration tool and without looking at each other's sheets. This is my sheet. Each of us also wrote code-mixed and English versions of 20 questions. For example, row 21 I typed as *india ka time kon jari krta h*, which is exactly how people really search."

## F2 · 4:05–4:45 · How differently three people spell
**Do:** Chrome → top menu **Human queries**. Point at the four tiles one by one.

**Screen shows:** **60** questions typed by each of us · **78%** of words spelled the same by all three (so 22% differently) · **91%** of words with the same Dhvani key · LipiSetu on our Roman typing **0.44–0.45** (baseline B2 0.11–0.14).

**Say:**
> "I then compared our three versions word by word, 500 words in total. Only 78% of words were spelled the same by all three of us, so even three classmates disagree on more than one word in five. But the Dhvani keys matched for 91% of words: the sound key absorbs most of our differences."

## F3 · 4:45–5:15 · Where the key works and where it fails
**Do:** scroll to table **5 · Same word, three people**. Move the mouse along the rows.

**Screen shows (for example):**
`janasankhya / jansankhya / jansankhya → JNSNKY / JNSNKY / JNSNKY ✓ yes`
`hisaab / hisab / hisab → HSB / HSB / HSB ✓ yes`
`bhaagon / bhago / bhagon → BGN / BG / BGN ✗ no`

**Say:**
> "Here it works: *janasankhya* with or without the extra *a*, *hisaab* or *hisab*, all get one key. And here it fails, and the middle one is mine: I typed *bhago* without the final *n*, so my key is BG, not BGN. When a person actually drops a sound, the key can't bring it back."

*(If another row is clearer, use it, but read the spellings and keys exactly as they appear on screen.)*

## F4 · 5:15–5:35 · Does it work on real typing?
**Do:** scroll to table **6 · Search quality on the human queries**. Point at the three **Roman A1, A2, A3** columns, rows B1, B2 and S3.

**Screen shows:** B1 **0.020 / 0.019 / 0.013** · B2 **0.140 / 0.112 / 0.117** · S3 **0.448 / 0.435 / 0.438**.

**Say:**
> "On each of our three romanisations, normal search gets about 0.02, transliteration about 0.12, and LipiSetu about 0.44. So the system works on how real people type, not just on generated queries. Abhinav will now take you through the full evaluation."

---

# ABHINAV (5:35–7:35)

## G1 · 5:35–6:10 · Evaluation against the baseline
**Do:** Chrome → top menu **Evidence**. Point at the four tiles, then scroll to chart **1 · Search quality** and its orange **Takeaway** box.

**Screen shows:**
- tiles: **Script Gap 0.051** (baseline 0.436) · **CSC 0.75** (baseline 0.24) · **36%** neural · **37 MB** (from 448 MB)
- Takeaway: *B1 falls from 0.533 on Devanagari to 0.004 in Roman; S2 keeps 0.487; D0 gets 0.001 on Roman; L1 highest on Devanagari (0.642).*

**Say:**
> "Hi, I'm Abhinav. Every number on this page is read live from our results folder: 350 judged test questions from MIRACL, each asked in Devanagari, standard Roman and casual Roman, with all tuning done only on the separate train split. In the chart, each system has three bars, one per script; a script-invariant system has three equal bars. Normal BM25 falls from 0.533 to 0.004 when the same question is typed in Roman. With the Dhvani zone and pooled df, Roman stays at 0.487. The Script Gap drops from 0.436 for the transliteration baseline to 0.051 for us. And the plain neural model gets almost zero on Roman: it matches the script before the meaning."

## G2 · 6:10–6:40 · The gate and the ablation
**Do:** scroll to chart **2 · Quality vs neural compute**. Hover the blue line near the dot. Then scroll to table **3 · Which Dhvani rules matter** and its Takeaway.

**Screen shows:** the dot *"threshold from train: 36% neural, nDCG 0.538"* · hover tooltip near 35–38%: **learned gate 0.538, random gate ≈ 0.50** · Takeaway 2: *better than never (0.507) and always (0.496)* · Takeaway 3: *switching off drop_vowels: Roman nDCG 0.481 → 0.166*.

**Say:**
> "This chart shows the gate's trade-off. Running the neural stage for only 36% of queries gives 0.538, better than never running it, 0.507, and better than always running it, 0.496. A random gate with the same budget only reaches about 0.50, so the gate really learned which queries need it. And the ablation shows which rule matters most: without dropping vowels, Roman quality falls from 0.48 to 0.17."

## G3 · 6:40–7:00 · First limitation: code-mixed and English
**Do:** top menu **Human queries** → table **6** → point at the **code-mixed** and **English** columns (rows S3, D1, L1) and the Takeaway.

**Screen shows:** S3 **0.204** (code-mixed), **0.119** (English) · D1 **0.413** on English (green) · L1 **0.383** on code-mixed (green).

**Say:**
> "But on code-mixed and English questions our sparse engine drops to 0.20 and 0.12, because the Dhvani key matches sound, not meaning: *leader* doesn't sound like नेता. Only the neural encoder helps there, with 0.41 on English. We report this openly as a limitation."

## G4 · 7:00–7:35 · Second limitation, shown live
**Do:** top menu **Search** → select **LipiSetu (sparse) S3** → click the first example chip **kal ka mausam kaisa rahega** (the full sentence; with only "kal ka mausam" the table-tennis result does not appear). Point at result **02 टेबल टेनिस** and its highlighted **खेल**, then at results **04–05** (cricket).

**Screen shows:** result 02 *टेबल टेनिस* with **खेल / खेले** highlighted · results 04 *रॉयल लंदन वनडे कप* and 05 *आईसीसी विश्व क्रिकेट लीग* matched through **मौसम**.

**Say:**
> "And a limitation live: I searched 'how will the weather be tomorrow', and result two is about table tennis! The highlighted word is खेल, *khel*, 'game'. Because the key drops vowels and aspiration, *kal* and *khel* both become KL. Results four and five are cricket for a different reason: in cricket, मौसम means 'season'. The tuned zone weights limit this, but don't remove it."

---

# DEVANSH (7:35–7:45)

## H · Close
**Do:** top menu **Team**.

**Say:**
> "So we measured the Script Gap, closed most of it with classic IR, and run the neural model only when needed. Next: more Indian languages and a bigger human query set. Everything is reproducible from our GitHub README. Thank you!"

---

## After recording
- Check the total length (5:00–8:00) and that all three voices are clear.
- Upload to YouTube as **Unlisted** (or Google Drive, "Anyone with the link") and open the link in an **incognito** window to check it plays.
- Put the link in `scripts/report_text.py` (replace `[unlisted link]`), rebuild the report, and add it to the README.

## Checklist
- [ ] Every member explains their own part: Devansh (engine, Dhvani, gate), Anamika (human set and agreement), Abhinav (evaluation and limitations)
- [ ] Intermediate output: df/idf, postings, zone scores (B2), pooled df and gate features (D)
- [ ] Baseline comparison: B1/B2 vs S3 (B1, D, G1, F4)
- [ ] Limitation shown live: kal / khel (G4)
- [ ] Each teammate speaks for about 2 minutes; total between 5:00 and 8:00
