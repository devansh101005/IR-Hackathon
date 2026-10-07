# Demo Video Script (target 7:20; allowed 5–8 minutes)

**Speakers:** Devansh Pandey (0:00–5:00 and the close), Anamika Pal (5:00–6:05), Abhinav Bachchas (6:05–7:05).
**PDF rules this video covers:** no slides · the system running live · intermediate output (postings, df/idf, scores) · evaluation against a baseline · one limitation shown live · every member explains their own part.

Each segment below lists: **Do** (exact click, command or scroll), **Screen shows** (what will appear, checked on Devansh's laptop), and **Say** (suggested words; say them in your own way, don't read them word for word). Every number in "Say" is on screen at that moment.

---

## Before recording (15 minutes)

1. Laptop **plugged in**, OMEN Gaming Hub → **Performance** mode, Windows notifications **off** (Focus assist), close other apps.
2. Open **two** PowerShell windows in `E:\IR_Midsem_Hackathon`. In **both** run:
   ```powershell
   $env:PYTHONPATH="src"; $env:PYTHONUTF8="1"; $env:PYTHONIOENCODING="utf-8"
   ```
   Terminal font size ≥ 18 (Ctrl + scroll wheel).
3. **Window 1 (server):** `.\.venv\Scripts\python.exe app\server.py` → wait for `Uvicorn running on http://127.0.0.1:8000`. Leave it running.
4. Chrome → `http://127.0.0.1:8000` → press **Ctrl + F5** once (loads the newest page) → zoom **110%** (Ctrl +) → make sure it is in **light mode** (top-right button says "Dark").
5. **Warm-up (important):** in the page, click every example once and switch through S3, G1, B2. In Window 2 run the two CLI commands from segment B once. The first run of anything is slow; on camera everything should be instant.
6. Open VS Code with `src/lipisetu/text/dhvani.py` and `src/lipisetu/retrieval/bm25.py` in two tabs.
7. **Refresh the page (F5) right before you press record.** The sound-key card always starts on *mausam → M S M* and changes every 4 seconds.
8. Record with **Xbox Game Bar (Win + Alt + R)** or OBS. Record all three parts in one sitting on this laptop, each person speaking their own part, so the system is live in every segment.

---

## A · 0:00–0:50 · The problem (Devansh)

**Do:** start on the top of the page. Don't scroll. Point the mouse at the four word boxes, then at the key.

**Screen shows:** "One question. Every script." · the card *The core idea · Dhvani key* with **mausam · mosam · मौसम · mousam → M S M** · the card *How to use this page*.

**Say:**
> "Hi, I'm Devansh, and this is LipiSetu, our project for Track T5, Indic-language search. Most Indians type Hindi in Roman letters, on WhatsApp or Google, and everyone spells it differently: mausam, mosam, mousam. But most Hindi text on the web is in Devanagari. A normal search engine matches exact words, so someone who types *kal ka mausam* gets nothing about कल का मौसम. We call this loss the **Script Gap**.
> Our fix is a sound key we call the Dhvani key. All four spellings here, in two scripts, become the same key, M S M. We store that key as its own zone in the inverted index."

---

## B · 0:50–2:50 · The engine running live in the terminal (Devansh)

### B1 · 0:50–1:35 · Baseline vs LipiSetu
**Do:** switch to **Window 2** and type:
```powershell
.\.venv\Scripts\python.exe -m lipisetu.cli compare "bharat ka samvidhan kab lagu hua" --systems B1,B2,S3
```
It takes about 10 seconds to load the index. Start talking while it loads.

**Screen shows:**
```
B1   वित्त मन्त्रालय | भरत व्यास | ...
B2   भरत मिलाप | भरत चक्रवर्ती | अयोध्याकाण्ड
S3   भारतीय संविधान का इतिहास | भारत का संविधान | भारत का संविधान
```
**Say:**
> "Everything you'll see is the real engine on 110,855 Hindi Wikipedia passages from the MIRACL dataset. The query is 'when did the Indian constitution come into force', typed in Roman.
> B1 is normal BM25: it can't match Roman words at all. B2 is the obvious fix, transliterate the query to Devanagari first. Look what it does: *bharat* becomes भरत, the Ramayana character, so it returns Bharat Milap. Our system, S3, returns the constitution passages."

### B2 · 1:35–2:50 · Every step, with real index values
**Do:** type:
```powershell
.\.venv\Scripts\python.exe -m lipisetu.cli search "kal ka mausam kaisa rahega" --system S3 --explain
```
When it prints, **scroll the terminal slowly from the top**, stopping at each block.

**Screen shows (top to bottom):**
- token table: `kal → KL`, `ka` and `kaisa` marked stop = yes, `mausam → MSM`, `rahega → RHG`
- `ZONE all`: kal, mausam, rahega all **df=0**
- `ZONE dhvani`: **KL df=12957 idf=2.147 · MSM df=712 idf=5.047 · RHG df=293 idf=5.934**
- `POOLED DF`: own df 0 → pooled df 12957 / 712 / 293
- `POSTINGS`: e.g. `MSM df=712  59#49 tf=1 [15] | 175#7 tf=1 [67] ...`
- `RESULTS`: #1 **भारतीय मौसम विज्ञान विभाग** with `dhvani=21.04 ... proximity=0.33 (window 4)` · `system S3, 7.0 ms`

**Say (one sentence per block as you scroll):**
> "First, tokenisation: our tokenizer uses explicit Unicode ranges, because Python's `\w` breaks Devanagari words. *ka* and *kaisa* are stop words. Each remaining word gets its Dhvani key: KL, MSM, RHG.
> In the normal word zone, all three words have **df zero**: these exact spellings never appear in the corpus. But in the Dhvani zone they match: MSM appears in 712 passages, RHG in 293.
> idf is log of N over df, so rare keys count more: RHG gets 5.9, the common KL only 2.1.
> These are real postings lists from the index: passage id, term frequency and word positions.
> We score BM25 in each zone, add the zones with weights tuned on the train split, then add a proximity boost: here the query words sit in a window of 4 words. The top result is the India Meteorological Department, in 7 milliseconds."

---

## C · 2:50–3:20 · The code behind it (Devansh)

**Do:** switch to VS Code → `dhvani.py`, scroll the docstring at the top (rules 1–7). Then switch to `bm25.py` and select the function `pooled_df_table`.

**Say:**
> "This is the Dhvani key, written from scratch. Each rule exists because Roman spelling can't show the difference: aspiration is merged, so *kh* equals *k*; retroflex equals dental; w equals v; and vowels are dropped. In our ablation, dropping vowels is the most important rule.
> And this is pooled df: in a mixed-script corpus a word's df is split across its spellings, so each spelling looks rare and gets too high an idf. We give every spelling the df of its whole sound class. It's Pirkola's idea from cross-language IR, applied to spellings."

---

## D · 3:20–4:15 · The web demo and the gate (Devansh)

**Do 1:** back to Chrome. Click **Search** in the top menu. Click the example chip **भारत का संविधान कब लागू हुआ** (system **LipiSetu (sparse) S3** selected).

**Screen shows:** the orange-bordered strip *"Same question, typed in Roman: bharat ka sanvidhan kab lagu hua"* with **LipiSetu (sparse): 6 of the top 10 are the same · RBO 0.57** and **Transliterate + BM25: 0 of the top 10 · RBO 0.00**.

**Say:**
> "Same question in Devanagari. The page automatically asks it again in Roman and compares the two top-10 lists. For LipiSetu, 6 of the top 10 are the same; for the baseline, none. That overlap is our consistency metric, RBO."

**Do 2:** click **LipiSetu cascade G1** in *Ranking system*. Point at the grey box under it that explains the system. Type `congress party ka leader kaun hai` → **Search**. In the right panel *What the engine did*, scroll down to **03 Pooled df**, then **05 Gate**.

**Screen shows:** pooled df **congress: own df 5 → pooled df 1,152** · Gate: blue bar past the black tick, **"Yes. Probability 0.65 is above the threshold 0.47, so the neural stage ran and the two lists were merged."**

**Say:**
> "Here is pooled df live: the Roman word *congress* appears in only 5 passages, but its sound class appears in 1,152, so we use 1,152.
> G1 is our cascade. A small logistic-regression gate, trained only on the train split, reads signals from the fast search and decides whether the expensive neural stage is worth running. For this question it says yes, probability 0.65 against a threshold of 0.47."

**Do 3:** type `kal ka mausam` → **Search** (G1 still selected). Scroll the right panel to **05 Gate**.

**Screen shows:** **"No. Probability 0.30 is below the threshold 0.47, so the fast result was returned and no neural model ran."**

**Say:**
> "For *kal ka mausam* the fast search is already confident, so the gate says no and saves the neural call."

---

## E · 4:15–5:00 · Evidence against the baseline (Devansh)

**Do:** click **Evidence** in the top menu. Pause on the four tiles, scroll to chart **1 · Search quality**, point at its orange *Takeaway* box, scroll to chart **2 · Quality vs neural compute** and its Takeaway, then to table **3 · Which Dhvani rules matter** and its Takeaway.

**Screen shows:**
- tiles: **Script Gap 0.051** (baseline 0.436) · **CSC 0.75** (baseline 0.24) · **36%** of queries needed the neural stage · **37 MB** (from 448 MB)
- Takeaway 1: *B1 falls from 0.533 on Devanagari to 0.004 in Roman; S2 keeps 0.487; D0 gets 0.001 on Roman*
- Takeaway 2: *gate: 36% neural, 0.538, better than never (0.507) and always (0.496)*
- Takeaway 3: *switching off drop_vowels: Roman nDCG 0.481 → 0.166*

**Say:**
> "Everything here is read live from our results folder: 350 judged test queries, each asked in Devanagari, standard Roman and casual Roman, with all tuning done on the separate train split.
> Normal BM25 falls from 0.533 to 0.004 when the same questions are typed in Roman. With the Dhvani zone and pooled df we keep 0.487. The plain neural model gets 0.001 on Roman: it matches script before meaning.
> The gate runs the neural stage for only 36% of queries and still beats both never running it and always running it.
> We also distilled the query encoder from 448 megabytes down to 37. And the ablation confirms dropping vowels is the most important rule.
> Now Anamika will show our human query set."

---

## F · 5:00–6:05 · The human query set (Anamika)

**Do:** click **Human queries** in the top menu. Pause on the four tiles. Then scroll to table **5 · Same word, three people** and move the mouse along the first rows.

**Screen shows:**
- tiles: **60** questions · **78%** words spelled the same by all three (so 22% differently) · **91%** words with the same Dhvani key · **LipiSetu on our Roman typing 0.44–0.45** (baseline B2 0.11–0.14)
- table rows, for example:
  `janasankhya / jansankhya / jansankhya → JNSNKY / JNSNKY / JNSNKY ✓ yes`
  `hisaab / hisab / hisab → HSB / HSB / HSB ✓ yes`
  `bhaagon / bhago / bhagon → BGN / BG / BGN ✗ no`

**Say:**
> "Hi, I'm Anamika. Our test questions in Roman were generated by a program, so we wanted to check the system on how real people type. Devansh, Abhinav and I each took the same 60 test questions and typed them in Roman on our own, the way we'd type on WhatsApp, with no transliteration tool and without looking at each other's sheets. Each of us also wrote code-mixed and English versions of 20 questions.
> Then I compared our spellings word by word. Only 78% of words were spelled the same by all three of us, so even three students from the same class disagree on about one word in five. But the Dhvani keys were the same for 91% of words: the sound key absorbs most of our differences.
> Here you can see it: *janasankhya* with or without the extra *a*, and *hisaab* versus *hisab*, all get the same key. But here's a failure: I typed *bhago* without the final *n*, so my key is BG instead of BGN. When a person actually drops a sound, the key can't recover it.
> On our real typing, LipiSetu reaches 0.44 to 0.45 nDCG, against 0.11 to 0.14 for the transliteration baseline. Abhinav will show the full results and a limitation."

*(Anamika: if a different row in the table is clearer for you, use it, but read the spellings and keys exactly as they appear on screen.)*

---

## G · 6:05–7:05 · Human-set results and the live limitation (Abhinav)

**Do 1:** scroll down to table **6 · Search quality on the human queries** and point at the **code-mixed** and **English** columns, then at the orange *Takeaway* under it.

**Screen shows:** S3 row **0.204** (code-mixed), **0.119** (English); D1 row **0.413** (English, in green); L1 row best on code-mixed **0.383**.

**Say:**
> "Hi, I'm Abhinav. This table is search quality on the questions the three of us typed. On our romanisations, LipiSetu holds up. But look at code-mixed and English: LipiSetu's sparse engine drops to 0.20 and 0.12. That's because the Dhvani key matches **sound**, not **meaning**: *leader* doesn't sound anything like नेता. Only the neural encoder can connect them; it gets 0.41 on English. We also found our gate was trained only on Hindi and Roman queries, so it calls the neural stage too rarely for these. That's in the report as a limitation."

**Do 2:** click **Search** in the top menu → select **LipiSetu (sparse) S3** → click the first example chip **kal ka mausam kaisa rahega** (use the full sentence: with only "kal ka mausam" the table-tennis result does not appear). Point at result **02 टेबल टेनिस** and its highlighted **खेल** words. Then point at **04 रॉयल लंदन वनडे कप** and **05 आईसीसी विश्व क्रिकेट लीग** (cricket), and scroll to **10 2019–21 आईसीसी विश्व टेस्ट चैम्पियनशिप फाइनल**, where **खेल** is highlighted again.

**Screen shows:** result 02 *टेबल टेनिस* with **खेल / खेले** highlighted five times; results 04–05 are cricket pages matched through **मौसम**; result 10 is a cricket final with **खेल** highlighted.

**Say:**
> "Now a limitation, live. I searched *kal ka mausam kaisa rahega*, 'how will the weather be tomorrow'. Result two is about table tennis! The highlighted word is खेल, *khel*, meaning 'game'. Because the Dhvani key drops vowels and aspiration, *kal* and *khel* both become KL, so sports passages leak in, and result ten is a cricket final for the same reason. Results four and five are cricket too, but for a different reason: in cricket, मौसम means 'season'. That's a meaning problem, not a sound problem. The tuned zone weights limit the damage but don't remove it. A next step is learning the key rules from data instead of writing them by hand."

---

## H · 7:05–7:20 · Close (Devansh)

**Do:** click **Team** in the top menu (the three name cards show).

**Say:**
> "So: we measured the Script Gap, closed most of it with classic IR, and run the neural model only when it's needed. Next we want more Indian languages, a larger human query set, and the encoder running in the browser. All code, data steps and results are in our GitHub README. Thank you!"

---

## After recording
- Check the length (between 5:00 and 8:00) and that every voice is clear.
- Upload to YouTube as **Unlisted** (or Google Drive with "Anyone with the link"). Open the link in an **incognito** window to check it plays.
- Put the link in `scripts/report_text.py` (the `[unlisted link]` text), rebuild the report, and add it to the README.

## Checklist
- [ ] Every member speaks about the part they actually did (Devansh A–E + H, Anamika F, Abhinav G)
- [ ] Intermediate output shown: df/idf, postings, per-zone scores (segment B2), gate features (D)
- [ ] Baseline comparison shown: B2 vs S3 (B1, D, E)
- [ ] At least one limitation shown live: kal / khel (G)
- [ ] Total length between 5:00 and 8:00
