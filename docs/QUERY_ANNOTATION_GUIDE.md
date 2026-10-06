# Query Annotation Guide (for teammates)

**Time needed:** about 1.5–2 hours per person. **Deadline:** by H9 of the hackathon.
Your work becomes the **human Hinglish query set**, one of our main novelty points. It also counts as your real contribution in the work division.

## What you'll get
A TSV file `queries/human/sheet_<your_name>.tsv` with 60 Hindi questions (MIRACL dev queries) in Devanagari:
```
qid	devanagari	roman	code_mixed	english
1033752#0	कांग्रेस दल का नेता कौन है ?
```
Open it in VS Code, Google Sheets or Excel. **Save it as TSV with UTF-8 encoding.** In Excel, use "Save As → Unicode Text"; or just use Google Sheets and download as `.tsv`.

## What to write for each row
1. **`roman`** (all 3 annotators do all 60 rows). Type the question **the way you would type it on WhatsApp**, in Roman letters.
   - Example: `कांग्रेस दल का नेता कौन है ?` → `congress dal ka neta kaun hai`
   - Use **your own natural spelling**. Don't try to be "correct" or consistent with others. Different people spelling things differently is exactly what we want to measure.
2. **`code_mixed`** (only for the rows assigned to you, below). Write the question as people actually mix Hindi and English.
   - Example: `congress party ka leader kaun hai`
3. **`english`** (only for your assigned rows). A natural English version.
   - Example: `who is the leader of the congress party`

## Rules (important for valid results)
- **Work independently.** Don't look at the other annotators' sheets until everyone is done.
- **Don't use transliteration tools, Google Translate or AI** for the `roman` column. It must be your own typing. (You may use translation help for `english` only if you declare it; better not to.)
- **Don't search for the answer** or look at any documents. Only rewrite the question.
- Keep the meaning the same. Don't add or remove information.
- If a question doesn't make sense, write `SKIP` in the column and tell Devansh.

## Row assignment (for `code_mixed` and `english`)
| Annotator | Rows |
|---|---|
| Devansh | 1–20 |
| Teammate A | 21–40 |
| Teammate B | 41–60 |

**Avoiding bias:** Devansh designs the Dhvani key, so his romanisations could unconsciously match his own rules. Either Devansh fills in his `roman` column **at H0, before writing `dhvani.py`**, or a third person who hasn't seen the system (e.g. a friend) does the `roman` column instead. If a non-member helps, credit them as a volunteer annotator in the report.

## When done
Send your file to Devansh, or commit it yourself to `queries/human/` with the message `Add human query annotations (<your name>)`. Committing it yourself shows your contribution in the git history.
