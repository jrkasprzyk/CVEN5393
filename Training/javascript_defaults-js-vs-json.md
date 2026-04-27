# Lecture Notes: Organizing Game Settings with JSON, `defaults.js`, and Runtime Config

## 1. The problem: when `Config.js` and `Settings.js` fight

A common game-project problem is having two or more places that claim to be the “source of truth” for the same values.

For example:

```js
// Config.js
export const TRACK_WIDTH = 72;
export const CAMERA_DISTANCE = 18;
export const MAX_SPEED = 180;
```

```js
// Settings.js
export const settings = {
  trackWidth: 50,
  cameraDistance: 24,
  maxSpeed: 160,
};
```

Now the codebase has a basic question it cannot answer cleanly:

> Which value is the real value?

This gets worse when some systems import from `Config.js`, others import from `Settings.js`, and some values are copied manually between them. Bugs become hard to trace because changing one file may not affect the part of the game you expected.

The goal is not merely to “move settings somewhere else.” The goal is to create a clear configuration architecture.

A good architecture answers:

1. Where do default values live?
2. Where do human-editable project values live?
3. Where do runtime/player-modified values live?
4. Which values are allowed to override which other values?
5. What shape must the settings have?
6. What happens if a value is missing, invalid, or obsolete?

---

## 2. Three different kinds of settings

Before choosing JSON or JavaScript, separate settings by role.

### 2.1 Engine defaults

These are safe fallback values that the game can always use.

Example:

```js
const defaults = {
  car: {
    maxSpeed: 180,
    acceleration: 42,
    steeringSensitivity: 0.85,
  },
  camera: {
    followDistance: 18,
    height: 7,
    stiffness: 0.12,
  },
  track: {
    width: 72,
    banking: 0.0,
  },
};
```

These values should be boring, stable, and known-good.

### 2.2 Project/game tuning settings

These are values you actively tune while developing the game.

Example:

```json
{
  "car": {
    "maxSpeed": 165,
    "steeringSensitivity": 0.72
  },
  "camera": {
    "followDistance": 21
  },
  "track": {
    "width": 80
  }
}
```

These should be easy to edit and review.

### 2.3 Runtime/player settings

These are values controlled by the player or saved locally.

Example:

```json
{
  "audio": {
    "musicVolume": 0.4,
    "sfxVolume": 0.8
  },
  "graphics": {
    "shadows": true
  }
}
```

These should usually not be mixed with core physics or track-tuning constants.

---

## 3. What is a `defaults.js` ES module?

An ES module is a JavaScript file that exports values using `export` and imports them using `import`.

Example:

```js
// defaults.js
export const DEFAULT_SETTINGS = {
  car: {
    maxSpeed: 180,
    acceleration: 42,
    steeringSensitivity: 0.85,
  },
  camera: {
    followDistance: 18,
    height: 7,
    stiffness: 0.12,
  },
  track: {
    width: 72,
    banking: 0.0,
  },
};
```

Then another file can use it:

```js
// settingsManager.js
import { DEFAULT_SETTINGS } from './defaults.js';

console.log(DEFAULT_SETTINGS.car.maxSpeed);
```

The word “defaults” matters. A `defaults.js` file should usually contain the fallback values, not every final value the game will ever use.

The final settings used by the game might be constructed from multiple layers:

```txt
defaults.js
    ↓ overridden by
project-settings.json
    ↓ overridden by
saved player settings
    ↓ produces
active runtime settings
```

---

## 4. Why not just use a human-editable JSON file?

A JSON file is a very reasonable idea. It has major advantages.

Example:

```json
{
  "car": {
    "maxSpeed": 180,
    "acceleration": 42,
    "steeringSensitivity": 0.85
  },
  "camera": {
    "followDistance": 18,
    "height": 7,
    "stiffness": 0.12
  },
  "track": {
    "width": 72,
    "banking": 0.0
  }
}
```

JSON is good when you want configuration to be data, not code.

### Pros of JSON

- Easy for humans and tools to edit.
- Easy for AI tools to rewrite without accidentally adding executable code.
- Portable across JavaScript, Python, editors, build tools, and game engines.
- Cannot contain arbitrary JavaScript logic.
- Clear distinction between data and behavior.
- Good for saved settings, exported configs, modding, and tuning files.

### Cons of JSON

- No comments in strict JSON.
- No trailing commas.
- No constants, expressions, or computed values.
- No imports.
- No functions.
- Validation must happen elsewhere.
- Some development environments require special handling to import JSON.

For example, this is invalid JSON:

```json
{
  "trackWidth": 72, // wide oval track
}
```

The comment and trailing comma are not allowed.

---

## 5. Why use `defaults.js` instead?

A `defaults.js` file keeps the defaults inside the JavaScript module system.

That means the defaults can be imported naturally by the rest of the code.

```js
import { DEFAULT_SETTINGS } from './defaults.js';
```

### Pros of `defaults.js`

- Works naturally with JavaScript imports.
- Can include comments.
- Can export named groups of settings.
- Can use constants to avoid repetition.
- Can freeze objects to prevent accidental mutation.
- Can be type-checked with JSDoc or TypeScript-style tooling.
- Can contain small helper values when appropriate.

Example with comments and constants:

```js
const BASE_TRACK_WIDTH = 72;

export const DEFAULT_SETTINGS = Object.freeze({
  track: Object.freeze({
    // Width in world units. Roughly 8 car-widths.
    width: BASE_TRACK_WIDTH,
    banking: 0.0,
  }),
  camera: Object.freeze({
    followDistance: 18,
    height: 7,
  }),
});
```

### Cons of `defaults.js`

- It is code, so an AI or human can accidentally add logic.
- Less portable outside JavaScript.
- Slightly less friendly as a pure data file.
- Can become another messy config file if it starts doing too much.
- If defaults contain computed logic, it may become harder to inspect the final values.

The danger is that `defaults.js` can slowly turn into the same kind of mess as `Config.js` unless its role is narrow and well-defined.

---

## 6. The key idea: use both, but give them different jobs

A strong pattern is:

```txt
defaults.js             Safe fallback values, versioned with code
project-settings.json   Human-editable tuning overrides
settingsManager.js      Loads, validates, merges, and exposes final settings
```

This gives you the best of both worlds.

`defaults.js` gives the codebase reliable known-good values.

`project-settings.json` gives you a simple file to edit while tuning the game.

`settingsManager.js` makes sure the rest of the game imports settings from one place.

The rest of the game should not import directly from both `defaults.js` and `project-settings.json`. That recreates the original problem.

Instead, most systems should import only the final active settings:

```js
import { settings } from './settingsManager.js';

car.maxSpeed = settings.car.maxSpeed;
camera.followDistance = settings.camera.followDistance;
```

---

## 7. A clean project structure

One possible structure:

```txt
src/
  config/
    defaults.js
    project-settings.json
    schema.js
    settingsManager.js
  systems/
    CarController.js
    CameraController.js
    Track.js
```

Each file has a distinct job.

### `defaults.js`

Contains complete default settings.

```js
export const DEFAULT_SETTINGS = Object.freeze({
  car: Object.freeze({
    maxSpeed: 180,
    acceleration: 42,
    steeringSensitivity: 0.85,
  }),
  camera: Object.freeze({
    followDistance: 18,
    height: 7,
    stiffness: 0.12,
  }),
  track: Object.freeze({
    width: 72,
    banking: 0.0,
  }),
});
```

### `project-settings.json`

Contains only values you want to override.

```json
{
  "car": {
    "steeringSensitivity": 0.72
  },
  "camera": {
    "followDistance": 21
  },
  "track": {
    "width": 80
  }
}
```

This file does not need to repeat everything. Missing values fall back to defaults.

### `settingsManager.js`

Merges defaults and overrides.

```js
import { DEFAULT_SETTINGS } from './defaults.js';
import projectSettings from './project-settings.json';

function deepMerge(base, override) {
  const output = structuredClone(base);

  for (const [key, value] of Object.entries(override ?? {})) {
    if (
      value &&
      typeof value === 'object' &&
      !Array.isArray(value) &&
      typeof output[key] === 'object'
    ) {
      output[key] = deepMerge(output[key], value);
    } else {
      output[key] = value;
    }
  }

  return output;
}

export const settings = deepMerge(DEFAULT_SETTINGS, projectSettings);
```

Now the game has one place to get settings.

---

## 8. The most important rule: one public settings import

To stop `Config.js` and `Settings.js` from fighting, create one public settings interface.

Good:

```js
import { settings } from './config/settingsManager.js';
```

Risky:

```js
import { TRACK_WIDTH } from './Config.js';
import { settings } from './Settings.js';
import { DEFAULT_SETTINGS } from './config/defaults.js';
```

When every system chooses its own source, you lose control.

A good rule is:

> Game systems import from `settingsManager.js`, not from raw config files.

The raw files are implementation details.

---

## 9. Validation matters

Merging is not enough. You also need to catch bad values.

For example, this JSON is syntactically valid but logically bad:

```json
{
  "car": {
    "maxSpeed": "very fast"
  },
  "track": {
    "width": -10
  }
}
```

The game should reject or warn about these values.

A simple manual validator might look like this:

```js
export function validateSettings(settings) {
  const errors = [];

  if (typeof settings.car.maxSpeed !== 'number') {
    errors.push('car.maxSpeed must be a number');
  }

  if (settings.car.maxSpeed <= 0) {
    errors.push('car.maxSpeed must be greater than 0');
  }

  if (settings.track.width <= 0) {
    errors.push('track.width must be greater than 0');
  }

  if (settings.camera.followDistance <= 0) {
    errors.push('camera.followDistance must be greater than 0');
  }

  return errors;
}
```

Then in `settingsManager.js`:

```js
import { DEFAULT_SETTINGS } from './defaults.js';
import projectSettings from './project-settings.json';
import { validateSettings } from './schema.js';

const mergedSettings = deepMerge(DEFAULT_SETTINGS, projectSettings);
const errors = validateSettings(mergedSettings);

if (errors.length > 0) {
  throw new Error(`Invalid settings:\n${errors.join('\n')}`);
}

export const settings = mergedSettings;
```

This turns silent weirdness into obvious errors.

---

## 10. Avoid these traps

### Trap 1: Two files with overlapping authority

Bad:

```txt
Config.js says track width is 72.
Settings.js says track width is 50.
Track.js imports from Config.js.
Car.js imports from Settings.js.
```

Better:

```txt
defaults.js says default track width is 72.
project-settings.json overrides track width to 80.
settingsManager.js exports final track width as 80.
Every game system imports from settingsManager.js.
```

### Trap 2: Putting logic into the settings file

Avoid turning settings into code like this:

```js
export const DEFAULT_SETTINGS = {
  car: {
    maxSpeed: window.innerWidth > 1200 ? 220 : 160,
  },
};
```

That makes the value depend on runtime conditions and becomes harder to reason about.

Prefer:

```js
export const DEFAULT_SETTINGS = {
  car: {
    maxSpeed: 180,
  },
};
```

Then put adaptive logic in a system that has a clear job.

### Trap 3: Huge flat config files

This becomes hard to manage:

```js
export const TRACK_WIDTH = 72;
export const TRACK_BANKING = 0;
export const CAR_MAX_SPEED = 180;
export const CAR_ACCELERATION = 42;
export const CAMERA_DISTANCE = 18;
export const CAMERA_HEIGHT = 7;
```

Prefer grouped settings:

```js
export const DEFAULT_SETTINGS = {
  track: {
    width: 72,
    banking: 0,
  },
  car: {
    maxSpeed: 180,
    acceleration: 42,
  },
  camera: {
    followDistance: 18,
    height: 7,
  },
};
```

Grouped settings make ownership clearer.

### Trap 4: Mutating global settings during gameplay

Avoid this:

```js
settings.car.maxSpeed = 999;
```

That makes debugging difficult.

Instead, treat settings as input data. If gameplay needs temporary changes, put them in game state:

```js
car.currentMaxSpeed = settings.car.maxSpeed * boostMultiplier;
```

Settings describe the baseline. Runtime state describes what is currently happening.

---

## 11. JSON vs `defaults.js`: comparison

| Feature | JSON | `defaults.js` ES module |
|---|---:|---:|
| Human-editable | Excellent | Good |
| Allows comments | No, not strict JSON | Yes |
| Portable outside JS | Excellent | Limited |
| Can contain logic | No | Yes |
| Safe as pure data | Excellent | Depends on discipline |
| Easy to import in JS | Sometimes needs bundler support | Excellent |
| Can use constants | No | Yes |
| Good for defaults | Good | Excellent |
| Good for user/player settings | Excellent | Usually not ideal |
| Good for AI editing | Excellent | Good, but riskier |

The short version:

- Use `defaults.js` for stable code-level defaults.
- Use JSON for human-editable overrides and saved settings.
- Use a settings manager to merge, validate, and export the final settings.

---

## 12. A practical migration plan

### Step 1: Inventory duplicate settings

Find every setting currently defined in both `Config.js` and `Settings.js`.

Create a table like this:

| Setting | Current locations | Intended owner |
|---|---|---|
| Track width | `Config.js`, `Settings.js` | `settings.track.width` |
| Camera distance | `Config.js`, `Settings.js` | `settings.camera.followDistance` |
| Max speed | `Config.js`, `Settings.js` | `settings.car.maxSpeed` |

Do not rewrite everything at once if the game is fragile.

### Step 2: Create `defaults.js`

Move known-good fallback values there.

```js
export const DEFAULT_SETTINGS = {
  track: {
    width: 72,
    banking: 0,
  },
  car: {
    maxSpeed: 180,
    acceleration: 42,
    steeringSensitivity: 0.85,
  },
  camera: {
    followDistance: 18,
    height: 7,
    stiffness: 0.12,
  },
};
```

### Step 3: Create `project-settings.json`

Put only the values you are actively tuning.

```json
{
  "track": {
    "width": 80
  },
  "camera": {
    "followDistance": 21
  },
  "car": {
    "steeringSensitivity": 0.72
  }
}
```

### Step 4: Create `settingsManager.js`

This file becomes the only public source of settings.

```js
import { DEFAULT_SETTINGS } from './defaults.js';
import projectSettings from './project-settings.json';

function deepMerge(base, override) {
  const output = structuredClone(base);

  for (const [key, value] of Object.entries(override ?? {})) {
    if (
      value &&
      typeof value === 'object' &&
      !Array.isArray(value) &&
      typeof output[key] === 'object'
    ) {
      output[key] = deepMerge(output[key], value);
    } else {
      output[key] = value;
    }
  }

  return output;
}

export const settings = deepMerge(DEFAULT_SETTINGS, projectSettings);
```

### Step 5: Change imports gradually

Replace direct imports from `Config.js` and `Settings.js` with imports from `settingsManager.js`.

Before:

```js
import { TRACK_WIDTH } from './Config.js';
```

After:

```js
import { settings } from './config/settingsManager.js';

const trackWidth = settings.track.width;
```

### Step 6: Deprecate the old files

Once references are removed, delete the old files or leave a temporary warning comment:

```js
// Deprecated. Do not add new settings here.
// Use src/config/settingsManager.js instead.
```

---

## 13. Suggested pattern for your game

For a Rosebud-style browser game, I would aim for this:

```txt
src/config/defaults.js
src/config/project-settings.json
src/config/settingsManager.js
```

Use these categories:

```js
export const DEFAULT_SETTINGS = {
  car: {
    maxSpeed: 180,
    acceleration: 42,
    braking: 55,
    grip: 0.92,
    steeringSensitivity: 0.85,
  },
  camera: {
    followDistance: 18,
    height: 7,
    stiffness: 0.12,
    accelerationZoomOut: 2.0,
  },
  track: {
    width: 72,
    doglegWidth: 90,
    banking: 0.0,
    asphaltTextureScale: 1.0,
  },
  debug: {
    showTrackSpline: false,
    showPhysicsVectors: false,
  },
};
```

This keeps car feel, camera feel, and track feel separate.

That separation is important because otherwise a later AI edit may “fix the camera” by changing car acceleration, or “fix the road” by changing physics.

---

## 14. How to prompt an AI to make this change safely

A good prompt would be:

```txt
Refactor the configuration system so there is one public settings source.

Create:
- src/config/defaults.js for complete fallback defaults
- src/config/project-settings.json for human-editable overrides
- src/config/settingsManager.js for merging defaults with overrides and exporting `settings`

Rules:
- Game systems should import settings only from settingsManager.js.
- Do not let Config.js and Settings.js both define active values.
- Preserve the current gameplay values as much as possible.
- Group settings into car, camera, track, audio, graphics, and debug where appropriate.
- Do not add runtime logic to defaults.js.
- Do not mutate settings during gameplay.
- Add comments explaining where future settings should go.
- After refactoring, list every old import that was replaced.
```

A stronger version adds:

```txt
Before editing, identify all duplicated settings and explain which value you will preserve.
```

That forces the AI to notice conflicts instead of blindly moving values around.

---

## 15. Recommended final architecture

The cleanest mental model is:

```txt
defaults.js
  “What should the game use if nothing else is specified?”

project-settings.json
  “What values am I currently tuning for this game?”

settingsManager.js
  “What are the final validated settings the game should actually use?”

runtime game state
  “What is happening right now during play?”
```

Do not let those categories collapse into each other.

Once they collapse, configuration becomes mysterious again.

---

## 16. Bottom line

The AI suggestion of a `defaults.js` ES module is good, but only if it is used as part of a larger pattern.

A `defaults.js` file by itself does not solve the problem. It can even become the new messy `Config.js`.

The better solution is:

```txt
Complete defaults in defaults.js
Human-editable overrides in JSON
Final merged settings exported from settingsManager.js
All game systems import from settingsManager.js
```

That gives you a single source of truth while still preserving the convenience of human-editable tuning files.

For your case, where game feel is drifting because car physics, camera behavior, and track parameters are all being changed by AI edits, this architecture would help a lot. It creates a stable place for known-good defaults, a controlled place for experimental tuning, and a single final object that the game actually uses.
