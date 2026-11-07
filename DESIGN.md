---
name: WorldFork
description: A dispatch ledger for comparing and replaying agent decisions.
colors:
  teal: "#096958"
  amber: "#946015"
  rose: "#aa3c46"
  paper: "#f5f4ef"
  surface: "#ffffff"
  ink: "#172c30"
  muted: "#526469"
  line: "#d9dfdc"
typography:
  display:
    fontFamily: "Manrope Variable, sans-serif"
    fontSize: "40px"
    fontWeight: 650
    lineHeight: 1.16
    letterSpacing: "-0.035em"
  body:
    fontFamily: "IBM Plex Sans Variable, sans-serif"
rounded:
  control: "8px"
  panel: "14px"
spacing:
  world-gap: "20px"
  section-gap: "32px"
components:
  button-primary:
    backgroundColor: "{colors.teal}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "12px 16px"
  replay-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
---

# Design System: WorldFork

## Overview

**Creative North Star: "Dispatch ledger"**

The lab feels like an airport operations desk. An ink-dark departure board sits inside a daylight paper workspace. Ruled rows keep routes, bookings and tool receipts easy to follow across two worlds.

**Key Characteristics:**

- Paired world panels with consistent alignment.
- Dark departure boards set into a light workspace.
- Recorded outcomes, playback position and live status have separate labels.

## Colors

Teal marks the primary action and active controls. Amber and rose identify cautions and errors. The paper workspace, white panels and ink departure boards use neutral rules to separate groups. World A and B retain their letter labels wherever their colors recur.

## Typography

Manrope sets the headline and section titles. IBM Plex Sans carries controls, operational copy and data. Inventory, arrival times, scores and ticks use tabular numerals. The headline steps down to 36px at 960px and 32px at 700px.

## Layout

The desktop comparison aligns two worlds in equal columns. Navigation moves above the workspace at 960px and worlds stack at 700px. Playback sits above the paired state, so a reviewer can change the tick while watching the effect. The ledger and playback bar link back to each other.

## Elevation & Depth

Panels rely on rules and surface tones for separation. The evidence inspector uses a soft leftward shadow to mark its position above the workspace.

## Shapes

Controls and panels use the rounded tokens in the frontmatter. Native selects have a 7px radius, and the primary action uses the control radius.

## Components

- **Primary action:** solid teal on live setup, with a darker hover state and visible keyboard outline.
- **Replay overview:** a ruled surface with final scores and direct links to the decision ledger and run archive.
- **Playback:** native slider with play, pause and return-to-latest controls. Its label gives both the current and maximum ticks.
- **Evidence inspector:** shows the selected passenger or decision, opens focus on its close control and returns focus to the source on dismissal.

## Do's and Don'ts

- Do keep an explicit label beside every status color.
- Do keep the final outcome visibly separate from a historical snapshot.
- Don't animate inferred outcomes or decorate a board with fictional results.
