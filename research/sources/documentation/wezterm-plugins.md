---
source: https://wezterm.org/config/plugins.html
fetched: 2026-02-11
type: documentation
project: WezTerm
---

# WezTerm Plugins

WezTerm plugins are packages of Lua files that extend the terminal emulator's functionality. They're distributed via Git repositories and managed through a built-in plugin system.

## Installation

```lua
local wezterm = require 'wezterm'
local a_plugin = wezterm.plugin.require 'https://github.com/owner/repo'

local config = wezterm.config_builder()
a_plugin.apply_to_config(config)

return config
```

### Requirements

- Plugins must use HTTPS or file protocol URLs
- The default branch (typically `main`) is automatically checked out
- Plugins can accept configuration parameters as a second argument to `apply_to_config()`

## Plugin Management

### Updating

Call `wezterm.plugin.update_all()` to sync all plugins with their upstream repositories. This can be executed via the Lua REPL in the Debug Overlay.

### Removing

Plugins are stored in the runtime directory under `plugins/NAME`. Delete the appropriate directory to remove a plugin. Use `wezterm.plugin.list()` to discover plugin locations.

## Plugin Development

### Basic Structure

1. Create a local development repository
2. Add `plugin/init.lua` that exports an `apply_to_config` function
3. The function must accept a config builder parameter (and optionally additional configuration)
4. Use file protocol URLs for local development: `file:///path/to/plugin`

### Multi-Module Plugins

For plugins with multiple Lua modules, update `package.path` to include the plugin directory:

```lua
function findPluginPackagePath(projectUrl)
  for _, v in ipairs(wezterm.plugin.list()) do
    if v.url == projectUrl then
      local separator = package.config:sub(1, 1) == '\\' and '\\' or '/'
      return v.plugin_dir .. separator .. 'plugin' .. separator .. '?.lua'
    end
  end
end
```

### Development Workflow

- Run `wezterm.plugin.update_all()` after local changes to sync into the runtime directory
- To modify existing plugins: fork the repo, clone locally, create a development branch, and set it as default using `git symbolic-ref HEAD refs/heads/mybranch`

## Resources

Michael Brusegard maintains [a curated list of available WezTerm plugins](https://github.com/michaelbrusegard/awesome-wezterm) for discovering community-developed extensions.
