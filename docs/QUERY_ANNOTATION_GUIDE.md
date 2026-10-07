# Query Annotation Guide (for my teammates)

**Time needed:** about 1.5–2 hours each.
This becomes our **human Hinglish query set**, one of the main novelty points of the project, and it's the part you'll explain in the video. Please do it carefully and on your own.

## What you'll get
A file `queries/human/sheet_<your_name>.tsv` with 60 Hindi questions (from MIRACL dev) in Devanagari:
```
qid	devanagari	roman	code_mixed	english
1033752#0	कांग्रेस दल का नेता कौन है ?
```
Open it in Google Sheets, Excel or VS Code. **Save it as TSV with UTF-8 encoding.** Easiest: Google Sheets → File → Download → Tab-separated values.

## What to write in each row
1. **`roman`** (everyone does all 60 rows). Type the question **the way you'd type it on WhatsApp**, in Roman letters.
   - Example: `कांग्रेस दल का नेता कौन है ?` → `congress dal ka neta kaun hai`
   - Use **your own natural spelling**. Don't try to be "correct" or match anyone else. Different people spelling things differently is exactly what I'm measuring.
2. **`code_mixed`** (only your assigned rows, below). Write the question the way people actually mix Hindi and English.
   - Example: `congress party ka leader kaun hai`
3. **`english`** (only your assigned rows). A natural English version.
   - Example: `who is the leader of the congress party`

## Rules (these keep the results valid)
- **Work on your own.** Don't look at anyone else's sheet until all three are done.
- **Don't use transliteration tools, Google Translate or any AI** for the `roman` column. It has to be your own typing.
- **Don't search for the answer** or look at any documents. Only rewrite the question.
- Keep the meaning exactly the same.
- If a question doesn't make sense, write `SKIP` and tell me.

## Row assignment (for `code_mixed` and `english`)
| Annotator | Rows |
|---|---|
| Devansh (`sheet_devansh.tsv`) | 1–20 |
| Anamika Pal (`sheet_teammate_a.tsv`) | 21–40 |
| Abhinav Bachchas (`sheet_teammate_b.tsv`) | 41–60 |

I fill in my own `roman` column **before** I look at the Dhvani rule table, so my spellings aren't biased by my own system.

## When you're done
Commit your file to `queries/human/` with the message `Add human query annotations (<your name>)`, or send it to me.
Keep the file name and the first three columns exactly as they are.

## After all three sheets are in (Devansh)
```bash
python scripts/run_all_eval.py          # adds results/human_metrics.csv and human_invariance.csv
python scripts/annotator_agreement.py   # E12
python scripts/significance.py
python scripts/make_plots.py && python scripts/make_report.py
```
