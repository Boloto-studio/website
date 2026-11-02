---
description: "Use when editing Django templates or site CSS for the Boloto public site or frogs.net. Covers layout shells, terminal-theme consistency, translation tags, and where to make shared style changes."
name: "Boloto Templates and Styles"
applyTo:
  - "base/templates/**/*.html"
  - "frogsnet/templates/**/*.html"
  - "base/static/**/*.css"
  - "frogsnet/static/**/*.css"
---

# Template and Styling Workflow

- Reuse the existing layout shells before creating new top-level structure: public pages extend `base/templates/base/public_layout.html`, frogs.net content pages extend `frogsnet/templates/frogsnet/layout.html`, and auth pages use `frogsnet/templates/frogsnet/auth_layout.html`.
- Keep shared public-site styling in `base/static/base/project-styles.css`; extend the existing CSS variables, nav components, terminal panels, and scanline effects before introducing new styling patterns.
- Preserve the current visual direction: cyber-brutalist terminal UI, `Space Mono` and `VT323`, uppercase labels, bordered panels, hazard-yellow highlights, and neon-green status accents.
- When you touch visible copy, add `{% trans %}` or `{% blocktrans %}` instead of hard-coding new English text.
- Keep layouts responsive. The sidebar shell and terminal content area already encode the main desktop-to-mobile behavior, so prefer adapting those components over creating parallel layouts.
- If the intended look is unclear, follow [DESIGN.md](../../DESIGN.md) rather than inventing a separate visual system.