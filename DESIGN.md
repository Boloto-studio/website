---
name: Boloto Studio
colors:
  surface: '#02170b'
  surface-dim: '#02170b'
  surface-bright: '#273e2f'
  surface-container-lowest: '#001207'
  surface-container-low: '#092013'
  surface-container: '#0d2417'
  surface-container-high: '#182f21'
  surface-container-highest: '#233a2b'
  on-surface: '#cee9d4'
  on-surface-variant: '#d1c5ab'
  inverse-surface: '#cee9d4'
  inverse-on-surface: '#1f3527'
  outline: '#9a9078'
  outline-variant: '#4e4632'
  surface-tint: '#f0c100'
  primary: '#ffe8ae'
  on-primary: '#3d2f00'
  primary-container: '#f9c806'
  on-primary-container: '#6b5500'
  inverse-primary: '#745b00'
  secondary: '#ddffe4'
  on-secondary: '#00391f'
  secondary-container: '#00f999'
  on-secondary-container: '#006e41'
  tertiary: '#c1f2ff'
  on-tertiary: '#00363f'
  tertiary-container: '#39e0ff'
  on-tertiary-container: '#00606f'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffe089'
  primary-fixed-dim: '#f0c100'
  on-primary-fixed: '#241a00'
  on-primary-fixed-variant: '#574400'
  secondary-fixed: '#56ffa8'
  secondary-fixed-dim: '#00e38b'
  on-secondary-fixed: '#002110'
  on-secondary-fixed-variant: '#00522f'
  tertiary-fixed: '#a7edff'
  tertiary-fixed-dim: '#2bd9f7'
  on-tertiary-fixed: '#001f25'
  on-tertiary-fixed-variant: '#004e5b'
  background: '#02170b'
  on-background: '#cee9d4'
  surface-variant: '#233a2b'
typography:
  display-xl:
    fontFamily: Space Mono
    fontSize: 72px
    fontWeight: '700'
    lineHeight: '1.0'
    letterSpacing: -0.05em
  display-xl-mobile:
    fontFamily: Space Mono
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
  headline-lg:
    fontFamily: Space Mono
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: 0.05em
  body-md:
    fontFamily: Space Mono
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-sm:
    fontFamily: Space Mono
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1.0'
    letterSpacing: 0.15em
  code-snippet:
    fontFamily: Space Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.4'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  sidebar-width: 30%
  main-padding: 3rem
  gutter: 1.5rem
  section-gap: 4rem
  baseline: 4px
---

## Brand & Style

Boloto Studio is a **Cyber-Brutalist** design system inspired by 1980s mainframe terminals and tactical military interfaces. It targets hardcore gamers, developers, and tech enthusiasts who value efficiency, high-stakes environments, and a "classified" aesthetic.

The brand personality is cold, industrial, and utilitarian. It evokes a sense of urgency and desolation through high-contrast accents, monospace typography, and artificial scanline overlays. The visual style relies on heavy borders, raw structural elements, and subtle "glitch" animations (like CRT flickering) to create a tactile digital experience that feels both vintage and futuristic.

## Colors

The palette is anchored in deep "Void Black" (`#080C0A`) and "Tactical Green" (`#738C7A`), creating a low-light environment that mimics a night-vision HUD or an old-school monitor. 

- **Primary (Hazard Yellow):** Used exclusively for high-priority actions, warnings, and interactive hovers.
- **Secondary (Spring Green):** Reserved for system status indicators (Optimal/Online) and decorative code brackets.
- **Neutral (Field Drab):** Used for borders, secondary text, and structural dividers to maintain a muted, industrial feel.
- **Semantic Error:** A sharp, vibrating red used for data corruption or critical system failures.

Backgrounds should use layered shades of near-black to differentiate between the global navigation sidebar and the main content terminal.

## Typography

The system utilizes **Space Mono** exclusively to maintain a rigid, technical structure across all information densities. 

- **Display & Headlines:** Should be uppercase with tight line height. Large display text should feature a subtle drop shadow (`2px 2px 0px #111A14`) to simulate hardware-rendered depth.
- **Body Text:** Uses standard weights with generous line spacing for readability against dark backgrounds.
- **Labels:** Always uppercase with increased letter spacing to mimic serial numbers or system tags.
- **ASCII Art:** Reserved for brand identity and high-level section headers to reinforce the "terminal" metaphor.

## Layout & Spacing

Boloto studio uses a **Dual-Pane Fixed Grid** layout.
- **Sidebar:** A fixed 30% width pane on the left contains global navigation and system metadata. It is demarcated by a solid 1px vertical border.
- **Main Terminal:** The 70% right-hand pane handles all content scrolls independently.
- **Rhythm:** Spacing follows a strict 4px/8px baseline, but large container padding is set to `3rem` (48px) to provide "breathing room" for dense technical logs.
- **Responsive:** On mobile, the sidebar collapses into a top-level hidden drawer, and the main terminal expands to 100% width.

## Elevation & Depth

This system avoids traditional shadows in favor of **Structural Outlines** and **Glow Effects**.

- **Layers:** Depth is communicated by color shifting rather than elevation. The background is the darkest layer (`#080C0A`), while interactive cards and sidebars sit on a slightly lighter surface (`#111A14`).
- **Borders:** All interactive elements are contained by 1px solid borders (`#738C7A`).
- **Glows:** Use `box-shadow` only to simulate light emission. Active status lights or primary buttons should have a soft, colored bloom (e.g., `0 0 15px rgba(249, 200, 6, 0.3)`) to suggest a glowing CRT phosphor screen.
- **Overlays:** A global scanline gradient and a periodic "CRT flicker" animation create a sense of looking through a physical monitor.

## Shapes

The shape language is **Softened Geometric**. 
- **Corners:** UI elements utilize a subtle 4px (0.25rem) radius. This softens the aggressive brutalism slightly, suggesting a more modern "ruggedized" hardware interface.
- **Exceptions:** Very small pills (e.g., system status indicator) are allowed to be fully circular to represent physical LEDs.
- **Dividers:** Use horizontal rules with 1px weight to separate content logs.

## Components

- **Buttons:** Large, uppercase, and slightly rounded. The primary button is a solid block of Hazard Yellow with black text. Hover states should invert the colors or increase the outer glow.
- **Terminal Cards:** Rectangular containers with a 4px corner radius and a 1px border. Hovering on a card should change the border color to Spring Green (`#00FA9A`) and the title text to Hazard Yellow.
- **Navigation Links:** Text-based links enclosed in brackets: `[ HOME ]`. On hover, the brackets change color to Spring Green while the text transitions to Yellow.
- **System Status:** Small circular "LEDs" with an `animate-pulse` effect to indicate live system connectivity.
- **Terminal Input:** Represented by a blocky underscore cursor `_` with a 1s step-end blink animation.
- **Scrollbars:** Custom styled with a thin `1px` track border and a solid Field Drab thumb that turns Yellow on hover.