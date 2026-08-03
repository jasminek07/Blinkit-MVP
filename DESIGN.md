---
name: Velocity Commerce
colors:
  surface: '#fff8f0'
  surface-dim: '#e1d9c9'
  surface-bright: '#fff8f0'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#fcf3e2'
  surface-container: '#f6eddc'
  surface-container-high: '#f0e7d6'
  surface-container-highest: '#eae2d1'
  on-surface: '#1f1b11'
  on-surface-variant: '#4d4633'
  inverse-surface: '#343025'
  inverse-on-surface: '#f9f0df'
  outline: '#7f7660'
  outline-variant: '#d0c6ac'
  surface-tint: '#725c00'
  primary: '#725c00'
  on-primary: '#ffffff'
  primary-container: '#fad02c'
  on-primary-container: '#6e5900'
  inverse-primary: '#ebc31a'
  secondary: '#006d38'
  on-secondary: '#ffffff'
  secondary-container: '#74f9a0'
  on-secondary-container: '#00723a'
  tertiary: '#5f5e60'
  on-tertiary: '#ffffff'
  tertiary-container: '#d6d3d6'
  on-tertiary-container: '#5c5b5d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffe07d'
  primary-fixed-dim: '#ebc31a'
  on-primary-fixed: '#231b00'
  on-primary-fixed-variant: '#564500'
  secondary-fixed: '#77fca3'
  secondary-fixed-dim: '#59df89'
  on-secondary-fixed: '#00210d'
  on-secondary-fixed-variant: '#005228'
  tertiary-fixed: '#e4e2e4'
  tertiary-fixed-dim: '#c8c6c8'
  on-tertiary-fixed: '#1b1b1d'
  on-tertiary-fixed-variant: '#474649'
  background: '#fff8f0'
  on-background: '#1f1b11'
  surface-variant: '#eae2d1'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 40px
    fontWeight: '800'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '700'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-bold:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
  price-display:
    fontFamily: Outfit
    fontSize: 18px
    fontWeight: '700'
    lineHeight: 24px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-margin: 16px
  gutter: 12px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 24px
  card-padding: 12px
---

## Brand & Style
The design system focuses on the urgency and reliability of quick-commerce. It utilizes a **Corporate / Modern** aesthetic with a heavy emphasis on high-contrast visual cues that guide users through a high-speed purchasing funnel. The brand personality is energetic yet dependable, evoking an emotional response of "instant gratification" and "total efficiency."

The style leverages generous whitespace to prevent cognitive overload during rapid browsing, while high-density information is organized through clear, rounded containers. Visual metaphors favor speed—using directional shifts, vibrant status indicators, and prominent action buttons.

## Colors
The palette is built for high visibility. **Primary Yellow (#FAD02C)** is used as the "attention" color—reserved for highlights, categories, and brand moments. **Primary Green (#00A859)** is the functional "action" color, used strictly for buttons (Add to Cart), success states, and confirmations to drive conversion. 

The background uses a cool-toned **#F5F7FB** to make the pure white (**#FFFFFF**) product cards pop, creating a distinct separation between the interface frame and the interactive content.

## Typography
The system uses a dual-font approach. **Outfit** is utilized for headlines and price displays to provide a friendly, modern, and high-impact geometric feel. **Inter** is the workhorse for body copy and UI labels, ensuring maximum legibility at small sizes (essential for product descriptions and weight metrics).

- **Weight Strategy:** Use 700 and 800 weights for headers to establish a clear hierarchy against the lighter body weights.
- **Price Styling:** Always use `price-display` (Outfit Bold) to ensure the cost is the most legible element on a product card.

## Layout & Spacing
The layout follows a **fluid grid** model optimized for mobile-first consumption. 

- **Grid:** A 12-column grid for desktop, collapsing to a 2-column grid for product listings on mobile.
- **Rhythm:** An 8px base unit drives all spacing. 
- **Margins:** Standard mobile horizontal margin is 16px.
- **Product Grids:** Use a 12px gutter between product cards to maintain high density while ensuring touch targets are distinct.

## Elevation & Depth
Depth is created through a combination of **low-contrast outlines** and **ambient shadows**. This ensures the UI feels "tactile" and physical, like items on a shelf.

- **Level 1 (Cards):** 1px border (#EFEFEF) with a very soft, diffused shadow (0px 4px 12px, 4% opacity black).
- **Level 2 (Floating Actions/Modals):** A more pronounced shadow (0px 8px 24px, 8% opacity black) to indicate the element is above the main scrollable area.
- **Surface Layering:** Use the Neutral Background (#F5F7FB) as the base layer, with White (#FFFFFF) containers for all interactive components.

## Shapes
The shape language is friendly and approachable. 
- **Standard Cards:** 18px corner radius.
- **Secondary Elements (Buttons/Inputs):** 14px corner radius.
- **Search Bars:** 12px or fully rounded (pill) depending on the width.
- **Badges:** Use a 4px radius for a "sticker" look on discounts and offers.

## Components

- **Product Cards:** Must feature the 18px radius and 1px #EFEFEF border. The image should occupy the top 60% of the card. The "ADD" button should be positioned at the bottom right, using the Primary Green.
- **Action Buttons:** 
    - **Primary:** Solid Primary Green (#00A859) with white `label-bold` text. 
    - **Secondary:** White background, 1px Primary Green border, Green text.
- **Chips & Badges:** 
    - **Discount Badge:** Primary Yellow background with Black text, positioned at the top-left of product images.
    - **Category Chips:** White background with #EFEFEF border; when active, fill with Primary Yellow.
- **Input Fields:** 14px radius, #F5F7FB background, and a subtle 1px border that turns Primary Green on focus.
- **Cart Summary (Sticky):** A floating bottom bar with a Primary Green background, displaying "Item Count" and "View Cart" with a chevron icon to imply speed and forward movement.
- **Lists:** Clean dividers using #EFEFEF with 16px vertical padding for high-density information like address selection or order history.