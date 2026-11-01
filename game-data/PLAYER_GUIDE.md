# Playing Whispers of Blackthorn Manor

In 1926, inventor Elias Blackthorn died during a midnight gathering. A century
later, you enter his haunted mansion to investigate the official accident account.
Three spirits remember different parts of that night. Your objective is to collect
records, test connections and build an evidence-supported explanation of what
happened and why. This guide does not reveal the solution.

## Start and move around

Choose a session mode and start an investigation. **Demo** uses authored responses
without a model call. **Live** attempts the configured local open-weight model;
each reply labels its actual source. **Fallback** means a live attempt could not
produce an accepted response. You can keep investigating during an AI outage.
The backend decides discoveries, puzzle results and endings in every mode.

Use **Explore** to move between rooms. The Entrance Hall connects the open wings:
Library, Study, Laboratory and Grand Ballroom. Return to the Hall to change wings.
A Hidden Passage becomes accessible through investigation; a locked destination
cannot be opened simply by selecting its name. Revisit places after discoveries.

Click a scene hotspot or choose the same object from the readable object list.
Inspecting reveals its description and may record a clue. A drawer, compartment or
mechanism can also have a separate **Open** or other permitted operation in the
inspection panel. Inspecting and opening are different actions. Watch for the
server-confirmed discovery or state change; moving an illustration is not enough.
Close an inspection panel to return to the scene.

## Journal and puzzles

**Journal** keeps collected evidence and notes. Read the words carefully, compare
sources and revisit notes when a new object or dialogue topic becomes available.

For the torn-letter puzzle, read each fragment and arrange one fragment in each
reading position. You can drag pieces or use the labeled selectors. Choose
**Submit reconstruction** to check the arrangement. **Reset draft** changes only
your unsent arrangement. An incorrect attempt does not consume the pieces.

For the machine puzzle, first investigate its associated records and apparatus.
Use the labeled power and choice controls, then submit the configuration. The
clues explain the settings; you do not need the private answer key. If controls
are unavailable, continue exploring and inspect the apparatus again after relevant
discoveries. Incorrect settings allow a safe retry.

## Connections and conversations

On **Board**, arrange collected cards for your own reference. Dragging has labeled
control alternatives. Select two different collected clues and submit their
connection. A supported pair earns a confirmed insight; an unsupported pair does
not grant progress. Suspect-card placement or decorative threads do not prove a
theory. Keep investigating rather than treating every visual link as confirmed.

Question an available ghost in its room: Eleanor in the Library, Thomas in the
Grand Ballroom and Clara in the Laboratory. Type a natural-language question,
choose your tone and optionally present collected evidence. Ask about what that
ghost could know. Trust and suspicion affect reactions and optional detail, but
low trust cannot permanently block the mystery. Relevant records can challenge an
account. Read the transcript and the live/demo/fallback label together.

The local AI helps select permitted character material and a reaction in context;
it cannot invent authoritative clues, change the fixed truth or decide an ending.
You still need to inspect, solve and connect evidence yourself.

## Theory, endings and starting over

Use **Theory** when available. Choose hypotheses about the actors, actions, motives
and cause, then attach collected evidence supporting each part. Evidence quantity
alone is not enough: each claim needs relevant support. Finish outstanding puzzles
and confirmed deductions before expecting a complete explanation.

A valid submission ends the investigation as **Truth Revealed**, **Partial Truth**
or **False Accusation**, based on deterministic rules and collected evidence. The
ending explains the support your theory achieved. To try another account, choose
**Restart investigation** and confirm. Restart clears clues, puzzle/deduction
progress, relationships and conversation history after server confirmation.

A browser refresh can resume a session while the same backend process retains it.
There is no durable saved game across a backend restart. If a session is lost or
capacity is reached, follow the displayed recovery controls; creating a new
investigation clears your current local view and requires confirmation.

## Keyboard, motion and sound

Use Tab/Shift+Tab to move focus, Enter/Space on buttons, and standard keyboard
selection controls. Every required drag mechanic has a labeled non-drag route.
Use the object list if precise scene targeting is difficult. Reduced-motion
settings preserve the clues and controls; supernatural effects are presentation,
not timing challenges. Audio begins off and is optional. Where audio is supplied,
use its opt-in control; readable descriptions/transcripts retain the information.
Media availability depends on the reviewed build and is not evidence of a rule
being completed.

## Spoiler warning

This guide avoids solutions. The backend story data and validation tests in the
repository contain puzzle answers and the complete mystery. Avoid reading those
source files until after your first playthrough if you want to discover it yourself.
