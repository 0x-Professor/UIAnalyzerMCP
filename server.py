"""
UI Analyzer MCP Server

An MCP server that analyzes website UIs and provides precise fix instructions
for AI coding assistants. Helps fix messy UI updates by identifying elements
and generating specific CSS/HTML changes.

Supports detection of:
- JS Frameworks: React, Vue, Angular, Svelte, and more
- Meta Frameworks: Next.js, Nuxt, Remix, Gatsby, Astro
- CSS Frameworks: Tailwind CSS, Bootstrap, Bulma, Foundation
- UI Libraries: shadcn/ui, Material UI, Chakra UI, Ant Design
"""

import base64
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Literal

from mcp.server.fastmcp import FastMCP, Context, Image
from playwright.async_api import async_playwright, Browser, Playwright

from models import (
    UIElement,
    UIAnalysisResult,
    FixInstructionsResult,
    ElementQuery,
    TechStackInfo,
)
from analyzer import (
    load_page,
    capture_screenshot,
    get_accessibility_tree,
    get_dom_structure,
    identify_elements,
    detect_ui_issues,
    analyze_page_full,
    generate_fix_instructions_for_query,
    interpret_user_query,
    ELEMENT_SELECTORS,
)
from framework_detector import get_tech_stack_summary, detect_tech_stack


@dataclass
class AppContext:
    """Application context holding shared resources."""
    playwright: Playwright
    browser: Browser


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage browser lifecycle - keeps browser running across tool calls."""
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    try:
        yield AppContext(playwright=pw, browser=browser)
    finally:
        await browser.close()
        await pw.stop()


# Create the MCP server with lifespan for shared browser
mcp = FastMCP(
    "UI Analyzer",
    instructions="Analyzes website UIs and provides precise fix instructions for AI coding assistants. Use this server to diagnose and fix messy UI updates.",
    lifespan=app_lifespan,
)


@mcp.tool()
async def analyze_page(
    url: str,
    query: str | None = None,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    include_screenshot: bool = True,
    ctx: Context = None,
) -> UIAnalysisResult:
    """
    Analyze a webpage UI and identify elements, issues, and structure.
    
    Use this tool when you need to understand the current state of a webpage's UI.
    It will identify all major UI components (navbar, header, footer, hero, buttons, etc.)
    and detect common issues like layout problems, overflow, and accessibility issues.
    
    Args:
        url: The URL of the webpage to analyze (can be localhost for dev servers)
        query: Optional vague user query like "the navbar is broken" to focus analysis
        viewport_width: Viewport width in pixels (default: 1920)
        viewport_height: Viewport height in pixels (default: 1080)
        include_screenshot: Whether to include a base64 screenshot (default: True)
    
    Returns:
        Complete analysis including elements, issues, accessibility tree, and DOM structure
    """
    if ctx:
        await ctx.info(f"Starting UI analysis of {url}")
    
    app_ctx: AppContext = ctx.request_context.lifespan_context if ctx else None
    
    if app_ctx:
        browser = app_ctx.browser
    else:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
    
    try:
        if ctx:
            await ctx.report_progress(0.1, 1.0)
        
        page = await load_page(browser, url, viewport_width, viewport_height)
        
        if ctx:
            await ctx.report_progress(0.3, 1.0)
            await ctx.info("Page loaded, analyzing UI elements...")
        
        result = await analyze_page_full(page, url, query, include_screenshot)
        
        if ctx:
            await ctx.report_progress(1.0, 1.0)
            await ctx.info(f"Analysis complete: found {len(result.elements)} elements, {len(result.issues)} issues")
        
        await page.context.close()
        
        return result
    
    finally:
        if not app_ctx:
            await browser.close()
            await pw.stop()


@mcp.tool()
async def get_screenshot(
    url: str,
    highlight_selector: str | None = None,
    element_type: str | None = None,
    full_page: bool = True,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    ctx: Context = None,
) -> Image:
    """
    Capture a screenshot of a webpage, optionally highlighting specific elements.
    
    Use this tool to visually see the current state of the UI. You can highlight
    specific elements to help identify problem areas.
    
    Args:
        url: The URL of the webpage to screenshot
        highlight_selector: CSS selector of elements to highlight with red outline
        element_type: Type of element to highlight (navbar, header, footer, hero, button, etc.)
        full_page: Capture full scrollable page or just viewport (default: True)
        viewport_width: Viewport width in pixels (default: 1920)
        viewport_height: Viewport height in pixels (default: 1080)
    
    Returns:
        PNG screenshot as an Image object
    """
    app_ctx: AppContext = ctx.request_context.lifespan_context if ctx else None
    
    if app_ctx:
        browser = app_ctx.browser
    else:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
    
    try:
        page = await load_page(browser, url, viewport_width, viewport_height)
        
        # Determine selector to highlight
        selector = highlight_selector
        if not selector and element_type and element_type in ELEMENT_SELECTORS:
            selector = ", ".join(ELEMENT_SELECTORS[element_type])
        
        screenshot_bytes = await capture_screenshot(page, full_page, selector)
        
        await page.context.close()
        
        return Image(data=screenshot_bytes, format="png")
    
    finally:
        if not app_ctx:
            await browser.close()
            await pw.stop()


@mcp.tool()
async def get_element_details(
    url: str,
    element_type: Literal[
        "navbar", "header", "footer", "hero", "button", "link",
        "heading", "form", "input", "card", "sidebar", "modal",
        "dropdown", "image", "section", "container"
    ],
    include_styles: bool = True,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    ctx: Context = None,
) -> list[UIElement]:
    """
    Get detailed information about specific UI elements on a webpage.
    
    Use this tool when you need to focus on a specific type of element,
    such as all buttons, the navbar, header, footer, hero section, etc.
    Returns detailed info including selectors, positions, and computed styles.
    
    Args:
        url: The URL of the webpage to analyze
        element_type: Type of element to find (navbar, header, footer, hero, button, etc.)
        include_styles: Include computed CSS styles for each element (default: True)
        viewport_width: Viewport width in pixels (default: 1920)
        viewport_height: Viewport height in pixels (default: 1080)
    
    Returns:
        List of UIElement objects with full details
    """
    app_ctx: AppContext = ctx.request_context.lifespan_context if ctx else None
    
    if app_ctx:
        browser = app_ctx.browser
    else:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
    
    try:
        page = await load_page(browser, url, viewport_width, viewport_height)
        elements = await identify_elements(page, element_type, include_styles)
        await page.context.close()
        
        return elements
    
    finally:
        if not app_ctx:
            await browser.close()
            await pw.stop()


@mcp.tool()
async def get_fix_instructions(
    url: str,
    user_complaint: str,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    ctx: Context = None,
) -> FixInstructionsResult:
    """
    Generate precise fix instructions based on a user's vague complaint about the UI.
    
    This is the main tool for helping fix messy UI updates. It interprets vague
    user queries like "the navbar is broken" or "the layout is messed up" and
    generates specific, actionable fix instructions including CSS changes.
    
    Args:
        url: The URL of the webpage with UI issues
        user_complaint: The user's description of the problem (can be vague)
                       Examples: "the header is messed up", "buttons are not aligned",
                       "the hero section looks wrong", "spacing is off"
        viewport_width: Viewport width in pixels (default: 1920)
        viewport_height: Viewport height in pixels (default: 1080)
    
    Returns:
        Detailed fix instructions including:
        - Interpreted problem description
        - Affected elements with selectors
        - Ordered fix instructions with CSS changes
        - Code snippets showing before/after
        - Additional recommendations
    """
    if ctx:
        await ctx.info(f"Analyzing UI issue: {user_complaint}")
    
    app_ctx: AppContext = ctx.request_context.lifespan_context if ctx else None
    
    if app_ctx:
        browser = app_ctx.browser
    else:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
    
    try:
        if ctx:
            await ctx.report_progress(0.1, 1.0)
        
        page = await load_page(browser, url, viewport_width, viewport_height)
        
        if ctx:
            await ctx.report_progress(0.3, 1.0)
        
        # Get query interpretation
        query_info = interpret_user_query(user_complaint)
        target_types = query_info.get("element_types", [])
        
        # Get relevant elements
        elements = []
        if target_types:
            for element_type in target_types:
                elements.extend(await identify_elements(page, element_type, include_styles=True))
        else:
            elements = await identify_elements(page, include_styles=True)
        
        if ctx:
            await ctx.report_progress(0.6, 1.0)
        
        # Detect issues
        issues = await detect_ui_issues(page, elements)
        
        if ctx:
            await ctx.report_progress(0.8, 1.0)
        
        # Generate fix instructions
        result = await generate_fix_instructions_for_query(
            page, url, user_complaint, elements, issues
        )
        
        if ctx:
            await ctx.report_progress(1.0, 1.0)
            await ctx.info(f"Generated {len(result.fix_instructions)} fix instructions")
        
        await page.context.close()
        
        return result
    
    finally:
        if not app_ctx:
            await browser.close()
            await pw.stop()


@mcp.tool()
async def get_accessibility_snapshot(
    url: str,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    ctx: Context = None,
) -> str:
    """
    Get the accessibility tree snapshot of a webpage in YAML format.
    
    The accessibility tree shows the semantic structure of the page as
    assistive technologies see it. Useful for understanding the logical
    structure and identifying accessibility issues.
    
    Args:
        url: The URL of the webpage to analyze
        viewport_width: Viewport width in pixels (default: 1920)
        viewport_height: Viewport height in pixels (default: 1080)
    
    Returns:
        Accessibility tree in YAML format
    """
    app_ctx: AppContext = ctx.request_context.lifespan_context if ctx else None
    
    if app_ctx:
        browser = app_ctx.browser
    else:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
    
    try:
        page = await load_page(browser, url, viewport_width, viewport_height)
        tree = await get_accessibility_tree(page)
        await page.context.close()
        
        return tree
    
    finally:
        if not app_ctx:
            await browser.close()
            await pw.stop()


@mcp.tool()
async def get_dom_overview(
    url: str,
    max_depth: int = 5,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    ctx: Context = None,
) -> str:
    """
    Get a simplified DOM structure overview of a webpage.
    
    Shows the hierarchy of significant elements (header, nav, main, section, etc.)
    with their IDs, classes, and roles. Useful for understanding page structure
    without the full complexity of the DOM.
    
    Args:
        url: The URL of the webpage to analyze
        max_depth: Maximum nesting depth to show (default: 5)
        viewport_width: Viewport width in pixels (default: 1920)
        viewport_height: Viewport height in pixels (default: 1080)
    
    Returns:
        Simplified DOM structure as indented text
    """
    app_ctx: AppContext = ctx.request_context.lifespan_context if ctx else None
    
    if app_ctx:
        browser = app_ctx.browser
    else:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
    
    try:
        page = await load_page(browser, url, viewport_width, viewport_height)
        structure = await get_dom_structure(page, max_depth)
        await page.context.close()
        
        return structure
    
    finally:
        if not app_ctx:
            await browser.close()
            await pw.stop()


@mcp.tool()
async def compare_viewports(
    url: str,
    viewports: list[dict] | None = None,
    ctx: Context = None,
) -> dict:
    """
    Compare how a webpage looks at different viewport sizes.
    
    Useful for identifying responsive design issues. Captures screenshots
    and element counts at different screen sizes.
    
    Args:
        url: The URL of the webpage to analyze
        viewports: List of viewport configurations. Default includes:
                  mobile (375x667), tablet (768x1024), desktop (1920x1080)
    
    Returns:
        Comparison data including screenshots and element visibility at each size
    """
    if viewports is None:
        viewports = [
            {"name": "mobile", "width": 375, "height": 667},
            {"name": "tablet", "width": 768, "height": 1024},
            {"name": "desktop", "width": 1920, "height": 1080},
        ]
    
    app_ctx: AppContext = ctx.request_context.lifespan_context if ctx else None
    
    if app_ctx:
        browser = app_ctx.browser
    else:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
    
    try:
        results = {}
        
        for i, vp in enumerate(viewports):
            if ctx:
                await ctx.report_progress(i / len(viewports), 1.0)
            
            page = await load_page(browser, url, vp["width"], vp["height"])
            
            # Capture screenshot
            screenshot_bytes = await capture_screenshot(page, full_page=False)
            
            # Count visible elements
            elements = await identify_elements(page, include_styles=False)
            visible_count = sum(1 for el in elements if el.is_visible)
            
            results[vp["name"]] = {
                "width": vp["width"],
                "height": vp["height"],
                "visible_elements": visible_count,
                "total_elements": len(elements),
                "screenshot_base64": base64.b64encode(screenshot_bytes).decode("utf-8"),
            }
            
            await page.context.close()
        
        if ctx:
            await ctx.report_progress(1.0, 1.0)
        
        return results
    
    finally:
        if not app_ctx:
            await browser.close()
            await pw.stop()


@mcp.tool()
async def get_tech_stack(
    url: str,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    ctx: Context = None,
) -> dict:
    """
    Detect the technology stack (frameworks, libraries, CSS approach) used on a webpage.
    
    Use this tool to understand what technologies a website is built with before
    suggesting fixes. This helps generate framework-appropriate fix instructions.
    
    Detects:
    - JS Frameworks: React, Vue, Angular, Svelte, Solid, Preact
    - Meta Frameworks: Next.js, Nuxt, Remix, Gatsby, Astro, SvelteKit, Vite
    - CSS Frameworks: Tailwind CSS, Bootstrap, Bulma, Foundation
    - UI Libraries: shadcn/ui, Material UI, Chakra UI, Ant Design, Radix UI
    - CSS Approach: CSS Modules, styled-components, inline styles, CSS variables
    - JS Libraries: jQuery, HTMX, Alpine.js
    
    Args:
        url: The URL of the webpage to analyze
        viewport_width: Viewport width in pixels (default: 1920)
        viewport_height: Viewport height in pixels (default: 1080)
    
    Returns:
        Tech stack information including detected frameworks, libraries, and
        framework-specific fix guidance.
    """
    if ctx:
        await ctx.info(f"Detecting tech stack for {url}")
    
    app_ctx: AppContext = ctx.request_context.lifespan_context if ctx else None
    
    if app_ctx:
        browser = app_ctx.browser
    else:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
    
    try:
        page = await load_page(browser, url, viewport_width, viewport_height)
        
        if ctx:
            await ctx.info("Analyzing page for frameworks and libraries...")
        
        # Use the comprehensive tech stack detection
        tech_stack = await get_tech_stack_summary(page)
        
        await page.context.close()
        
        if ctx:
            primary = tech_stack.get("summary", {}).get("primary_framework", "Unknown")
            css_lib = tech_stack.get("summary", {}).get("primary_css_library", "Unknown")
            await ctx.info(f"Detected: {primary} with {css_lib}")
        
        return tech_stack
    
    finally:
        if not app_ctx:
            await browser.close()
            await pw.stop()


@mcp.resource("element-selectors://common")
def get_common_selectors() -> str:
    """
    Get a reference of common CSS selectors for UI elements.
    
    Returns the selector patterns used to identify different types of
    UI elements like navbars, headers, footers, buttons, etc.
    """
    result = "Common UI Element Selectors\n"
    result += "=" * 40 + "\n\n"
    
    for element_type, selectors in ELEMENT_SELECTORS.items():
        result += f"{element_type.upper()}:\n"
        for selector in selectors:
            result += f"  - {selector}\n"
        result += "\n"
    
    return result


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

