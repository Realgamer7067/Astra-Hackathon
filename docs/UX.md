# ASTRA product and interaction specification

Design requirements; no UI is implemented yet. Preserve scientific positions independently of decorative effects.

## 10. CINEMATIC 3D UX / PRODUCT DESIGN

Design language: premium scientific mission control; dark navy/charcoal (not pure-black everywhere), deep blue/teal cool highlights, amber for hypothetical situations, red only for actual modeled collision markers, legible text, realistic Earth atmosphere/day-night cues, restrained glow, elegant typography and polished transitions. Keep it useful for the public, not a hard-to-read Hollywood HUD.

**Desktop layout:**
- Main full-bleed globe, smooth orbit/fly camera, Earth-centered view, camera controls, subtle stars, visible terminator/day-night illumination where supported, optional satellite orbit arcs, dynamic selection halos, debris trails. Attribution always visible.
- Top strip: project branding, UTC time, `LIVE CATALOG / CACHED / OFFLINE DEMO`, catalog count, object coverage, source timestamp/age, settings and help.
- Left drawer: search by name/NORAD ID, filters (active/inactive/debris/rocket body/unknown, altitude, inclination, mission type), selectable objects, collision lab form.
- Right inspector: object identity, type, known/assumed size/mass, altitude, speed, inclination, ephemeris/epoch, distance, selected trajectory and direct explanation of what is real versus hypothetical.
- Bottom timeline: play/pause, step forward/back, arbitrary scrub, speed presets (1×, 10×, 100×, 1000×, 10000× if stable), exact UTC time, event pins, jump to impact, replay from checkpoint, timeline end state. Maintain consistent world state while scrubbing.
- Collapsible results drawer: collision summary, fragment distribution charts, affected orbital shells, close-approach table, data provenance, export.
- 3 distinct modes: `Live Orbit`, `Collision Laboratory`, `Impact Intelligence`, with seamless transitions.

**Signature 20–30 second demonstration flow:**
1. Realistic globe, many genuine cataloged orbital markers visible, live/cached timestamps, user selects two spacecraft.
2. UI warns forced impact is fictional and shows chosen epoch; user clicks `Simulate Hypothetical Collision`.
3. Camera smoothly approaches the event at a comprehensible visual scale; near-impact countdown, velocity vector trails, cinematic slow-motion and brief shock-like light bloom **explicitly decorative**.
4. Fragments shoot outward and curve along integrated orbital trajectories, not straight-line forever; size/altitude coloring and optional exaggerated visual scale.
5. Scrub time forward; Earth overlays illuminate affected orbital bands, close approaches, and only legitimate entry-threshold markers.
6. Click a fragment or threatened spacecraft to see numeric source-backed results, limitations and provenance. Export concise scenario report.

**Visual integrity:** spacecraft are microscopic at planetary scale. Use exaggerated icon/model scaling and annotate it `visual sizes exaggerated`; orbital positions and physical distances must still use truthful numerical coordinates. Separate lens-friendly VFX particle positions from scientific debris position arrays. No flash effect necessary on lower-power GPUs; progressive enhancement. Optimize camera to avoid clipping/strobing. Provide `Reduce motion` and `Low graphics` toggles.

**Responsive/mobile:** smaller catalog and visual effects defaults; search, scenario preset, globe, timeline and result summaries remain usable without hover. Keyboard accessibility, screen reader labels, color-vision safe legends, errors/empty states. Use real, meaningful text—not placeholder charts and counters.
