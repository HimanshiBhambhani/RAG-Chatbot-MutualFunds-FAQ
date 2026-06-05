---
name: Mint Financial
colors:
  surface: '#faf8ff'
  surface-dim: '#d8d9e9'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f2ff'
  surface-container: '#ecedfd'
  surface-container-high: '#e6e7f7'
  surface-container-highest: '#e0e1f1'
  on-surface: '#181b26'
  on-surface-variant: '#3c4a43'
  inverse-surface: '#2d303c'
  inverse-on-surface: '#eff0ff'
  outline: '#6b7b72'
  outline-variant: '#bacac1'
  surface-tint: '#006c4f'
  primary: '#006c4f'
  on-primary: '#ffffff'
  primary-container: '#00d09c'
  on-primary-container: '#00533c'
  inverse-primary: '#2fe0aa'
  secondary: '#5a5d72'
  on-secondary: '#ffffff'
  secondary-container: '#dcdef7'
  on-secondary-container: '#5f6176'
  tertiary: '#af3015'
  on-tertiary: '#ffffff'
  tertiary-container: '#ff9e88'
  on-tertiary-container: '#8f1900'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#59fdc5'
  primary-fixed-dim: '#2fe0aa'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#dfe1fa'
  secondary-fixed-dim: '#c3c5dd'
  on-secondary-fixed: '#171a2c'
  on-secondary-fixed-variant: '#43465a'
  tertiary-fixed: '#ffdad3'
  tertiary-fixed-dim: '#ffb4a4'
  on-tertiary-fixed: '#3d0600'
  on-tertiary-fixed-variant: '#8c1800'
  background: '#faf8ff'
  on-background: '#181b26'
  surface-variant: '#e0e1f1'
typography:
  display-lg:
    fontFamily: DM Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: DM Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: DM Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: DM Sans
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  headline-sm:
    fontFamily: DM Sans
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: DM Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: DM Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: DM Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: DM Sans
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: DM Sans
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  container-max: 1200px
  gutter: 24px
  margin-mobile: 16px
---

## Brand & Style

The design system is engineered for the modern fintech landscape, prioritizing clarity, speed, and trust. It balances a professional financial services aesthetic with an approachable, retail-investing friendliness. The visual language is deeply rooted in **Corporate Modernism** with a focus on high legibility and a systematic application of color to signal financial performance and action.

The target audience ranges from first-time investors to experienced traders. Therefore, the UI evokes an emotional response of **empowerment and calm**. By utilizing generous whitespace, a vibrant primary accent, and refined geometric typography, the interface remains clean and focused, reducing the cognitive load typically associated with complex financial data.

## Colors

The color palette is functional and semantic. The **Primary Green (#00D09C)** is the signature brand color, used for primary actions, growth indicators, and successful states. It signifies prosperity and momentum.

The typography uses a tiered grayscale: 
- **Primary Text (#44475B):** A deep, charcoal navy for high-contrast headers and body text.
- **Secondary Text (#7C7E8C):** A balanced gray for labels, hints, and less critical information.

Surface colors are strictly controlled to maintain a clean appearance. Use the **Secondary Background (#F5F7FA)** for layout sections to create subtle depth without relying on heavy borders. A tertiary red (suggested #EB5B3C) should be used sparingly for negative market trends and destructive actions to maintain visual balance with the vibrant primary green.

## Typography

This design system utilizes **DM Sans** for its geometric yet friendly proportions, which provides excellent legibility for numerical data. 

Headlines utilize tighter letter-spacing and heavier weights to establish a clear hierarchy. For financial figures (NAV, Portfolio Value, etc.), use the `headline` roles even within body layouts to ensure critical data points are immediately scannable. `label-sm` is reserved for metadata and small captions, often used in conjunction with the secondary text color to deprioritize auxiliary information.

## Layout & Spacing

The system follows a **Fixed-Fluid Hybrid** grid. On desktop, content is contained within a 1200px centered wrapper using a 12-column grid. On mobile and tablet, the layout transitions to a fluid 4-column and 8-column grid respectively.

Spacing is governed by a 4px base unit. 
- Use **24px (lg)** for the primary gutters and margins between major card components. 
- Use **16px (md)** for internal card padding and spacing between related groups. 
- Vertical rhythm should prioritize white space to ensure the UI feels "breathable," reflecting the calm nature of the brand.

## Elevation & Depth

This design system uses **Tonal Layers** combined with **Ambient Shadows** to communicate hierarchy. 

The primary canvas is always `#FFFFFF`. To separate content blocks, use the `#F5F7FA` background for the page body and place white cards on top. Depth is reinforced through a singular, consistent shadow style: `0 2px 8px rgba(0,0,0,0.06)`. This shadow is soft and diffused, intended to make cards appear slightly lifted without creating heavy visual noise. 

Interactive elements like buttons or active search bars may use a slightly more pronounced shadow on hover to provide tactile feedback, but the "floating" effect should remain subtle across the entire ecosystem.

## Shapes

The design system employs a **Variable Roundedness** strategy to categorize different UI interactions:

- **Cards & Containers:** Use a **12px** radius. This provides a soft, modern container that feels sturdy yet friendly.
- **Bubbles & Chips:** Use a **24px** radius (near-pill). These are used for tags, filters, and status indicators.
- **Inputs & Search Bars:** Use a **30px** fully-rounded radius. This creates a distinct visual language for "active" or "entry" areas, making them easy to identify as interactive touchpoints.
- **Buttons:** Use a tighter **8px** radius for a more precise, professional feel that contrasts with the softer inputs.

## Components

### Buttons
- **Primary:** Background `#00D09C`, Text `#FFFFFF`. Bold and impactful.
- **Secondary:** Transparent background, Border `1px solid #E8E8E8`, Text `#44475B`.
- **Tertiary/Ghost:** No background or border, Text `#00D09C`. Used for navigation within cards.

### Input Fields
- Height of 48px or 56px with a **30px** border radius.
- Background `#FFFFFF` with a `1px` border of `#E8E8E8`.
- Focus state: Border changes to `#00D09C` with a subtle glow.

### Cards
- White background, **12px** radius, and the standard ambient shadow.
- Used for grouping stock info, portfolio summaries, and news items.

### Chips & Tags
- Height of 32px with **24px** radius.
- Minimal styling: Light gray background (`#F5F7FA`) or outlined with `#E8E8E8`.
- Active state uses a light tint of the primary color (e.g., `#00D09C` at 10% opacity) with primary green text.

### Progress & Charts
- Line charts should use the Primary Green for growth and the Tertiary Red for decline.
- Stroke widths should remain thin (2px) to maintain the clean, lightweight aesthetic.