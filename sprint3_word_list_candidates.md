# Sprint 3: Candidate Words to Seed (Gate G1)

> **Purpose:** a list of words to add to the seed. Shokhina drafted it on 2026-10-30 from what the LLM generator kept reaching for and was rejected.
>
> **Status:** DRAFT. Nothing here is seeded yet. Mark each group (or word) **keep**, **drop** or **change**. Once signed off, the words go into `backend/scripts/seed_data.py` and are seeded on local Docker first, then on Neon `dev` under the Gate G6 rules.

---

## Why we need more words

The story generator may only use seeded words, and today it uses Mia's patterns (SH, CH, TH, FR). On 2026-10-30 we measured 10 stories per round:

| Round | Stories from the LLM | Rejected words by type |
|---|---|---|
| Before any change | 0 / 10 | mostly ordinary words |
| Better prompt + "edit your draft" retry | 8 / 10 | ordinary words; stories ungrammatical |
| + word endings (-s, -ed, -ing) | 5 / 10 | **only** ordinary words; grammar fixed |

With 10 runs per round, 8 against 5 is within chance. What is clear is that every rejection that remains is an ordinary word we have not seeded. Across all three rounds the most rejected were: **water (26), friends (25), swam (20), splash (17), happy (14), felt (13), back (11), met (10), pals (10), glad (8)**, then rest, shore, became, pond, swim, eyes, each, other, sea, shark, high, hello.

## How the words would be seeded

The same rules as the 2026-10-16 seeding decisions:

- **Group A words fit a pattern we already teach** and are tagged with it, so reading them changes the child's mastery. A † marks a word that also contains a pattern we don't teach yet. As in decision B, it is tagged only with the taught pattern, so a miss on the untaught part adds a little noise to that pattern's score.
- **Group B words have no taught pattern.** They are seeded like the filler and noun words (decision C): allowed in stories and saved when read, but they change no mastery.
- Verbs and nouns would also go into the word-ending lists (`REGULAR_VERBS`, `IRREGULAR_VERBS`, `PLURAL_NOUNS`), so `friends`, `splashed` and `swimming` come with them.

---

## Group A: fits a taught pattern

| Pattern | Words | Notes |
|---|---|---|
| SH | splash, brush, crash, flash, dash, cash, trash, shelf, shark †, shore †, sheep †, shy † | † r-controlled vowel (shark, shore), ee (sheep), y as long i (shy) |
| CH | bench, inch, chest, chick †, check †, each †, beach †, reach †, teach † | † ck (chick, check), ea (each, beach, reach, teach) |
| TH | thing, cloth, tooth †, other †, mother †, brother †, father † | † oo; irregular vowel + er. **Question:** should other/mother/brother/father be sight words instead? |
| BL | block †, blast, blend, blank | † ck |
| CL | class, cliff, close † | † o_e |
| FR | frost, frame (also a_e), free †, fruit †, friend † | † ee, ui; **friend has an irregular vowel. It was rejected 25 times, so it matters most.** Tag it FR, or make it a sight word? |
| a_e | became, wave, cave, plane, plate, grape, skate, snake, bake, safe, shape (also SH), whale † | † wh |
| ai / ay | paint, train, sail, snail, tray, gray, hay | |
| -MP | swamp †, stamp, stump, stomp, plump, chimp (also CH), blimp (also BL) | † the "a" in swamp sounds like o |

## Group B: no taught pattern (seeded like filler and nouns)

| Kind | Words |
|---|---|
| Most rejected | water, happy, back, met, glad, felt, rest, pond, rock, swim, swam, sea, high, eyes, hello, hi, more, next, pal |
| Everyday short words (CVC) | cat, hen, fox, bug, mud, sad, mom, dad, pet, wet, hop, hug, nap, bus, log, dock, bank, flip, skip |
| Other common words | night, cool, food, star, moon, began, smile, let's |
| The fixture children's interests | ocean: sea, sand, crab (and wave, whale, shark, shell above); space and trucks: truck, rocket, moon, star |

## Deliberately left out

- **Character names** (Shelly, Chad). The prompt now says "the frog", "the girl".
- **dinosaur, ocean.** These are long, multi-syllable words with patterns we don't teach. Mia's "the ocean" interest is covered by sea, sand, crab, wave, whale and shark instead.
- **Rude phrases.** One passing story ended "they shut up and went to sleep". Both words are fine alone, so a word list can't block the phrase. That needs a separate phrase check, which is not part of this list.

## Questions for the sign-off

1. Keep the † words (decision B noise), or only seed words whose every sound is taught?
2. **friend** and **other / mother / brother / father**: pattern words or sight words?
3. Is Group B fine as unpatterned words, even though reading them never shows up on the dashboard?
4. Anything to add for real tester interests at the usability sessions?
