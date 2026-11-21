# Source hierarchy, provenance and citations

## Reliability tiers

| Tier | Source class | Can directly establish | Cannot establish alone |
|---|---|---|---|
| 1 | Current upstream Linux source, DT bindings, Git history, subsystem docs, MAINTAINERS, lore maintainer discussion | Current code/interface/history and reviewed intent | Target board wiring or untested runtime behavior |
| 2 | Official vendor kernel/source, official firmware/OTA, boot docs, lawful schematics/datasheets | Shipped/downstream implementation and documented hardware | Mainline suitability, current upstream status or another variant |
| 3 | Reproducible open-source device ports and maintained project repositories | A specific source/patch/userspace combination and useful leads | Upstream acceptance or untouched target equivalence |
| 4 | Complete target logs, decoded images, package metadata, teardowns, measured results, careful community findings | Observed target facts within provenance/test limits | General support or unexplained causal claims |
| 5 | Search snippets, forums/chats, retail specs, AI text, unsourced lists | Search leads only | Final technical proof |

User-provided target logs can be stronger than a generic primary document for the narrow fact they directly show. The tier describes source class, not permission to overclaim.

## Mandatory source record

| Field | Record |
|---|---|
| Locator | URL; repository + path; lore message; artifact filename |
| Revision | Full commit/tag/branch and tree status; firmware/build ID; log timestamp |
| Acquisition | How obtained and from which exact device/variant |
| Integrity | Hash for local/downloaded artifacts when decision-relevant |
| State | Current upstream, linux-next, pending, historical, downstream-only, community-only |
| Proves | Narrow direct claim |
| Does not prove | Closest tempting overclaim |
| Independence | Original or mirror/derivative of another source |
| Confidence impact | Why the claim is Verified/Strongly supported/etc. |

## Citation form

For source-tree evidence, cite:

~~~text
Tier 1 — linux.git <full commit>, <path>:<symbol/node>.
Proves: <narrow fact>.
Does not prove: <board/runtime fact>.
State: <released/next/pending/historical>.
~~~

For patch series, cite cover letter and individual patch message IDs, version, base commit, prerequisite series and current disposition. For artifacts, cite exact device model/firmware, original filename/hash and derivation tool/version.

## Cross-check rules

- Mirrors are not independent confirmations.
- A downstream tree copied from another OEM/tree is one lineage.
- A device wiki and pmaports entry may share the same maintainer/test and are not automatically independent.
- Retail specs can confirm marketed capacity/display size but rarely controller, topology or revision.
- A binding proves an ABI exists, not that the target uses it.
- A driver match entry proves code can match that compatible, not that all dependencies are supported or tested.
- A DTS node proves stated configuration at that revision, not physical correctness.
- A successful log proves behavior under its exact image/firmware/test, not permanent reliability.

## Currency and negative searches

Record when and where a search was run. “Not found” must specify repositories, refs, paths, terms and date. Absence from one branch or search index is not proof no work exists. Check renames, aliases, predecessor IP names, maintainer trees, linux-next, lore versions and device codenames.

When a source is unreachable, preserve its locator and label claims unverified. Search snippets remain Tier 5.

## Confidence assignment

| Label | Minimum standard |
|---|---|
| Verified | Directly supported by a primary source, exact target artifact/log, lawful schematic/datasheet, or reproduced result |
| Strongly supported | At least two genuinely independent reliable indirect sources, no unresolved material contradiction |
| Plausible | Technically coherent, bounded, and paired with a falsifiable validation |
| Unknown | Missing, ambiguous or contradictory evidence; implementation prohibited |

Confidence belongs to a claim, not a source or whole dossier. One report may contain Verified SoC identity and Unknown panel wiring.

