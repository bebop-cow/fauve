You're building the desktop UI for Fauve, an open-source, security-focused agentic app. The user chats with an agent that works inside a sandbox, runs on local models and can reach GitHub. The layout is approved and fixed ("Gallery wall"): three columns. Don't restructure it. Use `theme.py` for every color and font.

## Layout (1280×800 reference)
| Column | Width | Job |
|---|---|---|
| Sidebar | 240px, fixed | Navigation between tasks ("case files") |
| Chat | flexible | Conversation with the agent, including approval requests |
| Painting | 380px, fixed | Ambient status: a full-height painting with a status card over the bottom |

## 1. Sidebar: case files
- What it's for: switching between tasks. Each task is a "case".
- Contents from top to bottom: the app icon (`icon-day.png` or `icon-night.png`) and the FAUVE wordmark; a "+ New case" button; the label "CASE FILES"; the list of cases.
- The active case has a panel background, a 1px border and semi-bold text. Inactive cases are in muted text. Long names end in an ellipsis on one line.
- It doesn't change when the agent's state changes. Only the theme affects it.

## 2. Chat: the work
- Header (60px): the case title on the left and a status pill on the right ("● WORKING" or "● WAITING ON YOU").
- Messages: the user's messages are on the right, in dark ink with light text (radius 16/4/16/16). The agent's messages are on the left, in a bubble color with a 1px border (radius 4/16/16/16). Each is at most about 520px wide.
- **Approval card**: this is the only place the agent asks for permission. It appears in the message thread when the agent wants to do something outside the sandbox, like a network call or a write outside allowed folders.
  - Gold strip: "HELD AT THE SANDBOX DOOR"
  - What it wants, in plain words: "Fauve wants to reach api.osv.dev"
  - Technical details in Courier Prime: method, scope, read-only or write, and what closes afterwards
  - Buttons: ALLOW ONCE (filled) and DENY (outline). Nothing happens until the user picks one. The agent never submits, logs in or approves anything by itself.
- Composer at the bottom, with the hint text "Give Fauve a lead…".

## 3. Painting column: what state the agent is in, at a glance
- What it's for: showing the agent's state without the user reading the chat. It's ambient and can't be interacted with, apart from the status card.
- The painting shows the current state and cross-fades when the state changes:
  | State | Day (6am–6pm) | Night |
  |---|---|---|
  | Idle | The Paperboy (`cat-newsboy.png`) | The Detective (`cat-detective.png`) |
  | Working | Morning Edition | Night Desk |
  | Needs approval | The Red Studio (`red-studio.webp`), day or night | same |
- The status card sits over the bottom of the painting, 16px in from the edges:
  - Kicker: "DAY SHIFT · IDLE" or "NIGHT SHIFT · WORKING"; when waiting on approval, "PAUSED · YOUR MOVE"
  - Headline (Josefin Sans 300):
    - Idle: "Morning. What's the case?" or "Evening. What's the case?"
    - Waiting on approval: "One question before I go on."
    - After approval: "Back on it."
    - After denial: "Understood. Standing down."
  - Fact rows: Sandbox (On · network off / Paused · asking for network / On · network closed), Network, and Your data ("Stays on this device").
  - A small sandbox map can go here. It shows what the agent can reach, what's locked and which requests are held.
- When approval is needed, the card switches to the Red Studio palette: red background, cream text, gold border. This is the strongest signal in the app, so don't use red anywhere else for decoration.

## State machine (it drives all three columns at once)
`idle (0) → working (1) → needs_approval (2) → resumed (3: approved or denied) → working/idle`
- On entering state 2: the chat shows the approval card, the header pill reads "WAITING ON YOU", the painting cross-fades to The Red Studio and the status card turns red.
- On leaving state 2: everything goes back to the working visuals. The headline reflects the user's choice.

## Theme
- Day from 6am to 6pm: cream #f3e9d2, ink #231b1b, accent gold.
- Night: prussian blue #0b1228, cream ink, gold accent #ddb13c.
- Check the clock on launch and every minute.
- Fonts: Josefin Sans Light for display text, Courier Prime for labels, technical details and buttons, Libre Franklin for body text.
