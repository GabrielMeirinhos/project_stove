---
name: Luminous Obsidian
colors:
  surface: '#101416'
  surface-dim: '#101416'
  surface-bright: '#363a3c'
  surface-container-lowest: '#0b0f11'
  surface-container-low: '#181c1e'
  surface-container: '#1c2022'
  surface-container-high: '#272b2d'
  surface-container-highest: '#313538'
  on-surface: '#e0e3e5'
  on-surface-variant: '#b9cbbc'
  inverse-surface: '#e0e3e5'
  inverse-on-surface: '#2d3133'
  outline: '#849587'
  outline-variant: '#3b4a3f'
  surface-tint: '#00e38b'
  primary: '#f4fff3'
  on-primary: '#00391f'
  primary-container: '#00ff9d'
  on-primary-container: '#007143'
  inverse-primary: '#006d40'
  secondary: '#bdf4ff'
  on-secondary: '#00363d'
  secondary-container: '#00e3fd'
  on-secondary-container: '#00616d'
  tertiary: '#fffaff'
  on-tertiary: '#3c0090'
  tertiary-container: '#e7d9ff'
  on-tertiary-container: '#7623ff'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#56ffa8'
  primary-fixed-dim: '#00e38b'
  on-primary-fixed: '#002110'
  on-primary-fixed-variant: '#00522f'
  secondary-fixed: '#9cf0ff'
  secondary-fixed-dim: '#00daf3'
  on-secondary-fixed: '#001f24'
  on-secondary-fixed-variant: '#004f58'
  tertiary-fixed: '#e9ddff'
  tertiary-fixed-dim: '#d1bcff'
  on-tertiary-fixed: '#23005b'
  on-tertiary-fixed-variant: '#5700c9'
  background: '#101416'
  on-background: '#e0e3e5'
  surface-variant: '#313538'
  emerald-glow: '#00FF9D'
  cyan-accent: '#00E5FF'
  obsidian-surface: '#101416'
  slate-muted: '#b9cbbc'
  glass-border: rgba(0, 255, 157, 0.1)
typography:
  display-xl:
    fontFamily: Manrope
    fontSize: 96px
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.05em
  headline-lg:
    fontFamily: Manrope
    fontSize: 72px
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.03em
  headline-lg-mobile:
    fontFamily: Manrope
    fontSize: 48px
    fontWeight: '800'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Manrope
    fontSize: 36px
    fontWeight: '700'
    lineHeight: '1.2'
  title-lg:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '800'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Manrope
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Manrope
    fontSize: 11px
    fontWeight: '800'
    lineHeight: '1'
    letterSpacing: 0.2em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  container-max: 1280px
  gutter: 1.5rem
  margin-mobile: 1.5rem
  margin-desktop: 5rem
  section-gap: 8rem
---

## Brand & Style
Luminous Obsidian is a high-tech, futuristic design system tailored for smart agriculture and industrial monitoring. The brand personality is precise, advanced, and reliable, evoking a sense of "digital mastery" over organic environments.

The visual style is a hybrid of **Glassmorphism** and **Cyberpunk Minimalism**. It utilizes deep, dark backgrounds (Obsidian) contrasted with vibrant, glowing UI elements (Luminous) to represent the intersection of technology and nature. Key characteristics include:
- **Neon Accents:** Strategically used to draw attention to critical data and system status.
- **Translucency:** Layered surfaces with high blur values to maintain legibility while suggesting depth.
- **Kinetic Energy:** Subtle pulse animations and glowing borders to indicate live, real-time data streaming.

## Colors
The palette is rooted in a deep, near-black "Obsidian" neutral to maximize the impact of neon luminescence.

- **Primary (Emerald Glow):** Represents health, growth, and system vitality. Used for primary actions, success states, and key data points.
- **Secondary (Cyan Accent):** Represents connectivity and digital transmission. Used for secondary features and supportive data metrics.
- **Surface Strategy:** The background is a solid `#101416`. Overlays utilize translucent variants of the primary color or neutral greys with `backdrop-filter: blur(20px)` to create a layered "glass" effect.
- **Semantic Colors:** Success is tied to the primary emerald; warnings and errors utilize high-saturation corals and reds (#ffb4ab) but are used sparingly to maintain the "cool" tech aesthetic.

## Typography
Manrope is used exclusively to maintain a clean, geometric, and modern feel that bridges the gap between technical and humanistic.

- **Scale & Impact:** Large, extra-bold weights are used for hero headlines to create a strong visual hierarchy.
- **Tracking:** Tight letter spacing is applied to large headings to maintain a compact, "designed" feel. Conversely, wide letter-spacing is applied to `label-caps` for optimal legibility at small sizes.
- **Contrast:** Typography uses color to define hierarchy—white/near-white for primary headlines, and `on-surface-variant` (muted slate) for body text and descriptions.

## Layout & Spacing
The system uses a **Fixed Grid** approach for the main content container, ensuring a premium, editorial feel on ultra-wide screens.

- **Vertical Rhythm:** Generous section gaps (128px on desktop) prevent the UI from feeling cluttered, allowing the background ambient glows to "breathe."
- **Grid:** A 12-column grid is standard for desktop. Elements like feature cards and statistics typically span 3 or 4 columns.
- **Mobile Adaptation:** On mobile, margins reduce to 24px and section gaps to 80px. Grid items reflow to a single column stack.
- **Floating Elements:** The navigation bar is detached from the viewport edge, using a fixed-width floating container to emphasize the "glass" aesthetic.

## Elevation & Depth
Depth is not communicated via traditional shadows, but through **Luminance and Blur**.

- **Level 1 (Base):** Solid `#101416` background.
- **Level 2 (Panels):** `rgba(49, 53, 56, 0.4)` with `backdrop-filter: blur(20px)`. These panels have a 1px border of `rgba(0, 255, 157, 0.1)` to define their edges.
- **Level 3 (Interactive):** When hovered or active, panels increase their border opacity and gain a "Neon Glow" (`box-shadow: 0 0 15px rgba(0, 255, 157, 0.1)`).
- **Ambient Depth:** Large, blurred radial gradients in the background (Primary and Secondary containers at 5% opacity) create a sense of environmental light without being distracting.

## Shapes
The shape language is dominated by **Hyper-Rounded** corners, creating a friendly yet sophisticated tech feel.

- **Base Radius:** Large components like sections or hero containers use a `2.5rem` (40px) radius.
- **Standard Components:** Cards and buttons use `rounded-2xl` (1rem) to `rounded-3xl` (1.5rem).
- **Micro-Components:** Status indicators and search bars are fully pill-shaped (rounded-full).
- **Asymmetry:** Occasionally, large sections use `clip-path` for subtle diagonal "asymmetric" edges to break the grid and add dynamic movement.

## Components
### Buttons
- **Primary:** High-saturation emerald fill with black text. Features a strong outer glow (`0 0 20px rgba(0, 255, 157, 0.3)`).
- **Secondary/Ghost:** Translucent background with a primary-colored border. Includes a leading icon (e.g., `play_circle`).

### Cards
- **Glass Panel:** Semi-transparent with a high backdrop-blur. 
- **Indicator Cards:** Small, floating cards used for real-time stats (e.g., Temperature) featuring large icons and bold numerical data.

### Navigation
- **Floating Nav:** A persistent top-bar with a `backdrop-blur-xl` and a subtle emerald border. Active links are denoted by an emerald bottom border.

### Status Indicators
- **Pulse Dot:** A 8px primary-colored circle with a concentric, animating ring that pulses outward, indicating an "active" or "live" system state.

### Input Fields
- **Search Bar:** Muted container with a low-opacity border, utilizing the `Material Symbols Outlined` set for leading icons.