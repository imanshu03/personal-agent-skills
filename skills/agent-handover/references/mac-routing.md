# macOS Routing

Support macOS first. Prefer reliable CLI routing over app routing because CLIs can receive a handover path and prompt.

## Detection

Detect CLIs with `command -v`:

```bash
command -v codex
command -v claude
```

Detect apps with Spotlight and common application paths:

```bash
mdfind 'kMDItemCFBundleIdentifier == "com.anthropic.claude"'
mdfind 'kMDItemCFBundleIdentifier == "com.openai.codex"'
ls /Applications ~/Applications
```

For Codex app routing, only treat `Codex.app` as the Codex target. Do not use `ChatGPT.app` as a Codex fallback because it can open the wrong product surface.

Detect terminals from common app names:

- Terminal
- iTerm
- Ghostty
- WezTerm
- Warp
- Alacritty
- kitty

## Surface Selection

`auto` routing:

1. Use a saved preference for the target agent when present.
2. If no preference exists, prefer CLI when the target CLI is installed.
3. Use app only when explicitly requested, saved as a preference, or chosen by the user after seeing available surfaces.
4. If both CLI and app are available and the user has not specified a surface, explain the tradeoff: CLI can receive the prompt directly; app routing only opens the app and requires pasting the prompt.
5. If CLI routing is selected and no terminal preference exists, ask which detected terminal to use before launching when more than one terminal is available. Offer to save the answer for future handoffs.
6. If the app cannot receive context reliably, open the app and print the handover path plus prompt.
7. If neither CLI nor app is available, create the handover file and report what is missing.

## App Caveat

Do not claim that Codex App or Claude App received full context unless a supported deep link, file-open route, or documented automation path was used. Opening an app is not the same as injecting task context.

When opening a receiving app, print the exact receiving prompt after launching the app so the user can paste it manually. CLI routing remains the recommended route for repeat handovers because it can pass the handover prompt directly.

## Preferences

Store preferences at:

```text
~/Library/Application Support/agent-handover/preferences.json
```

Shape:

```json
{
  "version": 1,
  "defaults": {
    "codex": {
      "surface": "cli",
      "terminal": "Ghostty"
    },
    "claude": {
      "surface": "cli",
      "terminal": "iTerm"
    }
  },
  "lastUsed": {
    "targetAgent": "claude",
    "surface": "cli",
    "terminal": "Ghostty"
  }
}
```
