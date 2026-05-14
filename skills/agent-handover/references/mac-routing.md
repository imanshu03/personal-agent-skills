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
mdfind 'kMDItemCFBundleIdentifier == "com.openai.chatgpt"'
ls /Applications ~/Applications
```

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
3. Use app only when explicitly requested or saved as a preference.
4. If the app cannot receive context reliably, open the app and print the handover path plus prompt.
5. If neither CLI nor app is available, create the handover file and report what is missing.

## App Caveat

Do not claim that Codex App or Claude App received full context unless a supported deep link, file-open route, or documented automation path was used. Opening an app is not the same as injecting task context.

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
