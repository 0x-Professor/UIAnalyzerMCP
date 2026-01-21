# UI Analyzer MCP Server

An MCP (Model Context Protocol) server that analyzes website UIs and provides precise fix instructions for AI coding assistants. Designed to solve the problem of "messy UI updates" when using agentic code IDEs like GitHub Copilot or Cursor.

## The Problem

When using AI coding assistants to build or update website UIs, the results can sometimes be messy:
- Layout breaks unexpectedly
- Elements overlap or misalign
- Spacing becomes inconsistent
- Responsive design breaks

Users often struggle to describe exactly what's wrong, saying things like "the navbar is broken" or "the hero section looks weird" - vague descriptions that don't help the AI understand what specific CSS or HTML changes are needed.

## The Solution

This MCP server bridges that gap by:

1. **Analyzing the live website** - Using Playwright to render and inspect the actual UI
2. **Identifying UI elements** - Finding navbars, headers, footers, heroes, buttons, forms, etc.
3. **Detecting issues** - Spotting layout problems, overflow, z-index conflicts, accessibility issues
4. **Interpreting vague queries** - Understanding what "the header is messed up" actually means
5. **Generating precise fix instructions** - Providing specific CSS selectors, property changes, and code snippets

## Installation

### Prerequisites

- Python 3.13 or higher
- uv package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/0x-Professor/UIAnalyzerMCP.git
cd UIAnalyzerMCP

# Install dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

## Usage

### Running the Server

```bash
# Run directly
uv run python server.py

# Or use the MCP CLI
uv run mcp run server.py

# For development with inspector
uv run mcp dev server.py
```

### VS Code / GitHub Copilot Configuration

Add to your VS Code settings.json or MCP configuration:

```json
{
  "mcpServers": {
    "ui-analyzer": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "/path/to/UIAnalyzerMCP"
    }
  }
}
```

### Cursor IDE Configuration

Add to your Cursor MCP settings (~/.cursor/mcp.json or project .cursor/mcp.json):

```json
{
  "mcpServers": {
    "ui-analyzer": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "/path/to/UIAnalyzerMCP"
    }
  }
}
```

### Claude Desktop Configuration

Add to your Claude Desktop config file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ui-analyzer": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "C:\\path\\to\\UIAnalyzerMCP"
    }
  }
}
```

## Available Tools

### analyze_page

Full UI analysis of a webpage. Returns elements, issues, accessibility tree, DOM structure, and screenshot.

```
analyze_page(url="http://localhost:3000", query="the navbar is broken")
```

### get_fix_instructions

The main tool for fixing messy UIs. Interprets vague user complaints and generates precise fix instructions.

```
get_fix_instructions(
    url="http://localhost:3000",
    user_complaint="the hero section looks weird and buttons are not aligned"
)
```

Returns:
- Interpreted problem description
- Affected elements with CSS selectors
- Ordered fix instructions with property changes
- Complete CSS changes to apply
- Additional recommendations

### get_screenshot

Capture a screenshot with optional element highlighting.

```
get_screenshot(url="http://localhost:3000", element_type="navbar")
get_screenshot(url="http://localhost:3000", highlight_selector=".hero-section")
```

### get_element_details

Get detailed information about specific UI element types.

```
get_element_details(url="http://localhost:3000", element_type="button")
```

### get_accessibility_snapshot

Get the accessibility tree in YAML format for understanding semantic structure.

```
get_accessibility_snapshot(url="http://localhost:3000")
```

### get_dom_overview

Get a simplified DOM structure overview.

```
get_dom_overview(url="http://localhost:3000", max_depth=5)
```

### compare_viewports

Compare the UI at different screen sizes to identify responsive issues.

```
compare_viewports(url="http://localhost:3000")
```

## Example Workflow

1. User runs their dev server: `npm run dev`

2. User tells the AI: "The navbar is messed up and the hero section has weird spacing"

3. AI uses `get_fix_instructions`:
```
get_fix_instructions(
    url="http://localhost:3000",
    user_complaint="The navbar is messed up and the hero section has weird spacing"
)
```

4. Server returns precise instructions:
```
Interpreted Problem: User is reporting alignment, spacing issues with the navbar, hero

Affected Elements:
- nav.navbar (selector: nav.navbar)
- section.hero (selector: .hero-section)

Fix Instructions:

1. Fix spacing on navbar
   Selector: nav.navbar
   CSS Changes:
   - padding: 1rem 2rem
   - gap: 1rem
   - align-items: center

2. Fix spacing on hero
   Selector: .hero-section
   CSS Changes:
   - padding: 4rem 2rem
   - margin: 0 auto
   - max-width: 1200px
```

5. AI applies the exact CSS changes to the codebase

## Supported UI Elements

The analyzer can identify and analyze:

- **navbar** - Navigation bars, menus
- **header** - Page headers, banners
- **footer** - Page footers
- **hero** - Hero sections, splash areas
- **button** - Buttons, CTAs
- **link** - Anchor links
- **heading** - H1-H6 headings
- **form** - Forms and form containers
- **input** - Input fields, textareas, selects
- **card** - Card components, panels
- **sidebar** - Side navigation, asides
- **modal** - Dialogs, popups
- **dropdown** - Dropdown menus, selects
- **image** - Images, SVGs
- **section** - Content sections
- **container** - Main containers, wrappers

## Detected Issue Types

- layout_broken
- overflow_hidden
- z_index_conflict
- spacing_inconsistent
- alignment_off
- responsive_issue
- accessibility_missing
- contrast_low
- element_overlap
- invisible_element
- empty_container
- broken_flexbox
- broken_grid

## Development

```bash
# Run with MCP inspector for debugging
uv run mcp dev server.py

# Run the test suite
uv run python test_mcp_server.py
```

### Test Suite

The test suite (`test_mcp_server.py`) tests all functionality:

- Query interpretation (vague user queries to element types)
- Page loading across multiple test sites
- Screenshot capture (full page, viewport, highlighted elements)
- Accessibility tree extraction
- DOM structure extraction
- Element identification by type
- Issue detection
- Full page analysis
- Fix instruction generation
- Viewport comparison (mobile, tablet, desktop)

Test artifacts are saved to `test_output/` directory:
- Screenshots at different viewports
- Accessibility tree YAML
- DOM structure text
- Detected elements JSON
- Analysis results JSON

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Acknowledgments

- Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Uses [Playwright](https://playwright.dev/) for browser automation
- Designed to work with [GitHub Copilot](https://github.com/features/copilot), [Cursor](https://cursor.sh/), and [Claude](https://claude.ai/)
