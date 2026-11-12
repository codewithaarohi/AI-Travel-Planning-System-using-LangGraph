# Dark / light mode for the Streamlit frontend

## Goal
Let a user switch the travel planner between its current dark look and a light look, from a toggle in the sidebar.

## Behaviour
- A `🌙 Dark mode` toggle sits at the top of the sidebar. It is **on by default**, so the app opens looking exactly as it does today.
- Turning it off switches the whole page to light mode immediately (one Streamlit rerun).
- The choice is stored in the URL as `?theme=light` (no parameter means dark). A refresh or a bookmarked link keeps the mode. Any other value of `theme` is treated as dark.

## Approach
All colours in the custom stylesheet in `frontend.py` become CSS custom properties (`var(--app-bg)`, `var(--text)`, …).
The stylesheet is written once. A small `:root { … }` block with either the dark or the light values is injected according to the toggle.

- **Dark values** are the existing hard-coded colours, mapped one-to-one, so dark mode does not change visually.
- **Light values:** off-white page (`#f4f7fb`), white cards (`#ffffff`), blue-grey borders (`#d5e1ee`), navy text (`#1f3347` body, `#0d2236` headings), and the same blue accent, darkened to `#1a5fa8` / `#1a6bbf` where it is used as text on white.
- **Fixed in both modes** (they sit on darkened photos or solid blue): the hero banner, the destination photo cards, and the white-on-blue Generate and quick-pick buttons. The button drop shadow is softened in light mode.
- **Themed:** page and sidebar backgrounds, sidebar chips and text, text area and User ID input, labels, agent result cards, section headers, metric boxes, final plan card, save bar, download button, warnings, markdown text, code, and links.

## Streamlit-drawn elements
Streamlit draws some elements itself, using its own theme, which follows the device's dark/light setting rather than the toggle. The agent result cards are among these (they are `stExpander` elements, while the current CSS targets `stStatusWidget`).
The stylesheet themes the visible ones explicitly, so they follow the toggle:
- the expander cards (header strip, body, and border)
- the warning box (`stAlertContainer`), with amber colours from the palette
- the borders of the text area and text input, which sit on wrapper elements (`stTextAreaRootElement`, `stTextInputRootElement`)
- the toggle's track and knob
- the `hr` divider

Tooltip popups may still follow the device setting. That is accepted.

The hero banner gets a fixed dark backdrop. Streamlit overrides its `object-fit: cover` with `scale-down`, so the photo does not span the banner, and without the backdrop the white hero text would sit on the light page.

## Out of scope
Following the device setting automatically, any other theme beyond dark and light, and redesigning the dark look.

## Testing
- **Automated (Streamlit `AppTest`, with the agent pipeline stubbed):**
  - Default is dark.
  - Turning the toggle off injects the light values and sets `?theme=light`.
  - Loading with `?theme=light` starts in light mode, with the toggle off.
  - An unknown `theme` value falls back to dark.
- **Visual (Playwright screenshots):** both modes, on the start page and on the results view. Results come from a stub pipeline served on a separate port, so no API quota is spent. Text contrast on cards is checked in both modes.
