# Asian noodles cleanup — proposals

Scanned canonicals with tokens `noodle`, `noodles`, `mein`, `ramen`, `pho`,
`udon`, `soba`, `pad` (whole-word). 4,782 canonicals matched.

## Findings

**Dominant pattern: `pasta` is a noise token.** Restaurants file Asian noodle
dishes under "pasta" menu sections, so the upstream extraction picked up
`pasta` as a token. Because canonical names are alphabetized,
`chicken lo mein` and `chicken lo mein pasta` end up as two clusters for the
same dish — over and over. Examples:

| noisy | clean | action |
|---|---|---|
| `chicken lo mein pasta` (421) | `chicken lo mein` (639) | merge |
| `pad pasta thai` (766) | `pad thai` (214) | merge → `pad thai` |
| `lo mein pasta shrimp` (370) | `lo mein shrimp` (584) | merge |
| `ew pad pasta see` (442) | `ew pad see` (77) | merge → `ew pad see` |
| `pasta tempura udon` (130) | `tempura udon` (25) | merge |

**Other patterns:** `phad→pad`, `lomein→lo mein`, `chowmein→chow mein`;
Vietnamese `ga pho→chicken pho`, `chay pho→pho vegetarian`; singular/plural
`noodle`↔`noodles` (82 paired groups merged into higher-count form).

## Output (`category_asian_noodles.csv`)

- **368 merges** (286 high, 82 medium sing/plural).
- **2,510 renames** (168 high as corollary of merge groups; 2,342 medium
  standalone — strip `pasta` from canonicals with no paired clean cluster).

~4,512 menu rows consolidated by merges; ~12,836 rows touched by standalone
renames (medium-flagged so user can opt to skip).

## NOT proposed
- Different broths (`miso`/`tonkotsu`/`shoyu`/`shio` ramen) kept distinct.
- `udon` / `soba` / `ramen` as TYPES never merged with each other.
- Different Thai dishes (`pad thai`, `pad see ew`, `pad kee mao`,
  `pad woon sen`, `pad ped`, `pad pak`, `pad prik`, `pad phet`) kept distinct.
- Different proteins always kept distinct.
- Thai protein words (`gai`, `goong`, `moo`) — all 1-count singletons with no
  paired English-protein cluster; deferred to singleton layer.
