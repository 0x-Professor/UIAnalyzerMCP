"""
Playwright-based UI analyzer for extracting and analyzing webpage elements.
Provides async functions for page loading, DOM inspection, and issue detection.
"""

import base64
import re
from typing import Any
from playwright.async_api import Page, Browser, async_playwright, Playwright

from models import (
    BoundingBox,
    ComputedStyles,
    UIElement,
    UIIssue,
    UIAnalysisResult,
    FixInstruction,
    FixInstructionsResult,
)


# Element type mapping: selectors for common UI components
ELEMENT_SELECTORS: dict[str, list[str]] = {
    "navbar": [
        "nav",
        "[role='navigation']",
        ".navbar",
        ".nav",
        "#navbar",
        "#nav",
        ".navigation",
        "header nav",
    ],
    "header": [
        "header",
        "[role='banner']",
        ".header",
        "#header",
        ".site-header",
        ".page-header",
    ],
    "footer": [
        "footer",
        "[role='contentinfo']",
        ".footer",
        "#footer",
        ".site-footer",
        ".page-footer",
    ],
    "hero": [
        ".hero",
        ".hero-section",
        "[data-section='hero']",
        ".banner",
        ".jumbotron",
        ".masthead",
        "section:first-of-type",
        ".intro",
        ".landing",
    ],
    "button": [
        "button",
        "[role='button']",
        "input[type='submit']",
        "input[type='button']",
        ".btn",
        ".button",
        "a.btn",
        "a.button",
    ],
    "link": [
        "a[href]",
        "[role='link']",
    ],
    "heading": [
        "h1", "h2", "h3", "h4", "h5", "h6",
        "[role='heading']",
    ],
    "form": [
        "form",
        "[role='form']",
        ".form",
    ],
    "input": [
        "input:not([type='hidden'])",
        "textarea",
        "select",
        "[role='textbox']",
        "[role='combobox']",
    ],
    "card": [
        ".card",
        ".card-container",
        "[class*='card']",
        ".tile",
        ".panel",
    ],
    "sidebar": [
        "aside",
        "[role='complementary']",
        ".sidebar",
        "#sidebar",
        ".side-nav",
    ],
    "modal": [
        "[role='dialog']",
        ".modal",
        ".dialog",
        ".popup",
        "[aria-modal='true']",
    ],
    "dropdown": [
        "[role='menu']",
        "[role='listbox']",
        ".dropdown",
        ".dropdown-menu",
        "select",
    ],
    "image": [
        "img",
        "[role='img']",
        "picture",
        "svg",
        ".image",
    ],
    "section": [
        "section",
        "[role='region']",
        ".section",
        "main > div",
    ],
    "container": [
        ".container",
        ".wrapper",
        ".content",
        "main",
        "[role='main']",
    ],
}


# Vague query keywords mapped to element types
QUERY_KEYWORDS: dict[str, list[str]] = {
    "navbar": ["navbar", "navigation", "nav", "menu", "top bar", "topbar", "main menu"],
    "header": ["header", "top", "banner", "head", "title area"],
    "footer": ["footer", "bottom", "foot", "copyright"],
    "hero": ["hero", "banner", "splash", "intro", "landing", "main banner", "first section", "top section"],
    "button": ["button", "btn", "cta", "call to action", "click", "submit"],
    "form": ["form", "input", "field", "textbox", "login", "signup", "register", "contact form"],
    "card": ["card", "tile", "box", "panel", "item"],
    "sidebar": ["sidebar", "side bar", "side menu", "aside", "left menu", "right menu"],
    "modal": ["modal", "popup", "dialog", "overlay", "lightbox"],
    "heading": ["heading", "title", "h1", "h2", "headline"],
    "image": ["image", "img", "picture", "photo", "icon", "logo"],
    "section": ["section", "area", "part", "block", "div"],
    "layout": ["layout", "grid", "flex", "spacing", "alignment", "margin", "padding"],
    "responsive": ["mobile", "responsive", "breakpoint", "screen size", "viewport", "tablet", "phone", "desktop"],
}


async def create_browser(playwright: Playwright, headless: bool = True) -> Browser:
    """Create a new browser instance."""
    return await playwright.chromium.launch(headless=headless)


async def load_page(
    browser: Browser,
    url: str,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    wait_for_load: bool = True,
) -> Page:
    """Load a webpage and return the page object."""
    context = await browser.new_context(
        viewport={"width": viewport_width, "height": viewport_height},
        device_scale_factor=1,
    )
    page = await context.new_page()
    
    try:
        await page.goto(url, wait_until="networkidle" if wait_for_load else "domcontentloaded")
    except Exception:
        await page.goto(url, wait_until="domcontentloaded")
    
    # Wait a bit for any animations to settle
    await page.wait_for_timeout(500)
    
    return page


async def capture_screenshot(
    page: Page,
    full_page: bool = True,
    highlight_selector: str | None = None,
) -> bytes:
    """Capture a screenshot of the page, optionally highlighting elements."""
    
    if highlight_selector:
        await page.evaluate(
            """(selector) => {
                document.querySelectorAll(selector).forEach(el => {
                    el.style.outline = '3px solid #ff0000';
                    el.style.outlineOffset = '2px';
                    el.style.boxShadow = '0 0 10px rgba(255,0,0,0.5)';
                });
            }""",
            highlight_selector,
        )
    
    screenshot = await page.screenshot(full_page=full_page, type="png")
    
    # Remove highlights after screenshot
    if highlight_selector:
        await page.evaluate(
            """(selector) => {
                document.querySelectorAll(selector).forEach(el => {
                    el.style.outline = '';
                    el.style.outlineOffset = '';
                    el.style.boxShadow = '';
                });
            }""",
            highlight_selector,
        )
    
    return screenshot


async def get_accessibility_tree(page: Page) -> str:
    """Get the accessibility tree snapshot as YAML."""
    try:
        snapshot = await page.locator("body").aria_snapshot()
        return snapshot or ""
    except Exception as e:
        return f"Error getting accessibility tree: {str(e)}"


async def get_dom_structure(page: Page, max_depth: int = 5) -> str:
    """Get simplified DOM structure showing element hierarchy."""
    
    structure = await page.evaluate(
        """(maxDepth) => {
            function getStructure(element, depth = 0) {
                if (depth > maxDepth) return '';
                
                const tag = element.tagName.toLowerCase();
                const id = element.id ? '#' + element.id : '';
                const classes = element.classList.length > 0 
                    ? '.' + Array.from(element.classList).slice(0, 3).join('.') 
                    : '';
                const role = element.getAttribute('role') ? `[role="${element.getAttribute('role')}"]` : '';
                
                const indent = '  '.repeat(depth);
                let result = `${indent}${tag}${id}${classes}${role}\\n`;
                
                const children = Array.from(element.children);
                const significantTags = ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer', 'div', 'form'];
                
                for (const child of children) {
                    const childTag = child.tagName.toLowerCase();
                    if (significantTags.includes(childTag) || child.id || child.classList.length > 0) {
                        result += getStructure(child, depth + 1);
                    }
                }
                
                return result;
            }
            
            return getStructure(document.body, 0);
        }""",
        max_depth,
    )
    
    return structure or ""


async def get_element_computed_styles(page: Page, selector: str) -> ComputedStyles | None:
    """Get computed CSS styles for an element."""
    
    try:
        styles = await page.evaluate(
            """(selector) => {
                const el = document.querySelector(selector);
                if (!el) return null;
                
                const computed = getComputedStyle(el);
                return {
                    background_color: computed.backgroundColor,
                    color: computed.color,
                    font_size: computed.fontSize,
                    font_family: computed.fontFamily,
                    padding: computed.padding,
                    margin: computed.margin,
                    border: computed.border,
                    display: computed.display,
                    position: computed.position,
                    z_index: computed.zIndex,
                    flex_direction: computed.flexDirection,
                    justify_content: computed.justifyContent,
                    align_items: computed.alignItems,
                    gap: computed.gap,
                    width: computed.width,
                    height: computed.height
                };
            }""",
            selector,
        )
        
        if styles:
            return ComputedStyles(**styles)
        return None
    except Exception:
        return None


async def identify_elements(
    page: Page,
    element_type: str | None = None,
    include_styles: bool = True,
    max_elements: int = 50,
) -> list[UIElement]:
    """Identify UI elements on the page."""
    
    if element_type and element_type in ELEMENT_SELECTORS:
        selectors = ELEMENT_SELECTORS[element_type]
    elif element_type == "all":
        # Get all significant elements
        selectors = [
            "header", "nav", "main", "section", "article", "aside", "footer",
            "h1", "h2", "h3", "h4", "h5", "h6",
            "button", "a[href]", "form", "input", "textarea", "select",
            "img", "picture", "svg",
            "div[class]", "div[id]",
            "[role]",
        ]
    else:
        # Get all major element types from ELEMENT_SELECTORS
        selectors = []
        for sel_list in ELEMENT_SELECTORS.values():
            selectors.extend(sel_list)
    
    combined_selector = ", ".join(list(dict.fromkeys(selectors))[:30])  # Dedupe and limit
    
    elements_data = await page.evaluate(
        """(selector) => {
            const elements = document.querySelectorAll(selector);
            const results = [];
            
            for (const el of elements) {
                if (results.length >= 50) break;
                
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 && rect.height === 0) continue;
                
                const computedStyle = getComputedStyle(el);
                const isVisible = computedStyle.display !== 'none' 
                    && computedStyle.visibility !== 'hidden'
                    && computedStyle.opacity !== '0';
                
                // Generate a unique selector
                let uniqueSelector = el.tagName.toLowerCase();
                if (el.id) {
                    uniqueSelector = '#' + el.id;
                } else if (el.classList.length > 0) {
                    uniqueSelector = el.tagName.toLowerCase() + '.' + Array.from(el.classList).join('.');
                }
                
                // Generate XPath
                function getXPath(element) {
                    if (element.id) return `//*[@id="${element.id}"]`;
                    if (element === document.body) return '/html/body';
                    
                    let ix = 0;
                    const siblings = element.parentNode ? element.parentNode.childNodes : [];
                    for (let i = 0; i < siblings.length; i++) {
                        const sibling = siblings[i];
                        if (sibling === element) {
                            const parentPath = element.parentNode ? getXPath(element.parentNode) : '';
                            return parentPath + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                        }
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                            ix++;
                        }
                    }
                    return '';
                }
                
                results.push({
                    tag_name: el.tagName.toLowerCase(),
                    selector: uniqueSelector,
                    xpath: getXPath(el),
                    text_content: el.textContent?.trim().substring(0, 100) || null,
                    bounding_box: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    },
                    aria_role: el.getAttribute('role'),
                    aria_label: el.getAttribute('aria-label'),
                    classes: Array.from(el.classList),
                    element_id: el.id || null,
                    children_count: el.children.length,
                    is_visible: isVisible
                });
            }
            
            return results;
        }""",
        combined_selector,
    )
    
    elements: list[UIElement] = []
    
    for data in elements_data[:max_elements]:
        # Determine element type from tag and attributes
        detected_type = detect_element_type(data)
        
        # Get computed styles if requested
        computed_styles = None
        if include_styles and data.get("selector"):
            computed_styles = await get_element_computed_styles(page, data["selector"])
        
        elements.append(
            UIElement(
                element_type=detected_type,
                tag_name=data["tag_name"],
                selector=data["selector"],
                xpath=data.get("xpath"),
                text_content=data.get("text_content"),
                bounding_box=BoundingBox(**data["bounding_box"]) if data.get("bounding_box") else None,
                aria_role=data.get("aria_role"),
                aria_label=data.get("aria_label"),
                classes=data.get("classes", []),
                element_id=data.get("element_id"),
                computed_styles=computed_styles,
                children_count=data.get("children_count", 0),
                is_visible=data.get("is_visible", True),
            )
        )
    
    return elements


def detect_element_type(element_data: dict[str, Any]) -> str:
    """Detect the semantic type of an element based on its properties."""
    
    tag = element_data.get("tag_name", "").lower()
    role = element_data.get("aria_role", "").lower() if element_data.get("aria_role") else ""
    classes = [c.lower() for c in element_data.get("classes", [])]
    element_id = (element_data.get("element_id") or "").lower()
    
    # Direct tag matches
    tag_type_map = {
        "nav": "navbar",
        "header": "header",
        "footer": "footer",
        "button": "button",
        "form": "form",
        "input": "input",
        "textarea": "input",
        "select": "input",
        "img": "image",
        "picture": "image",
        "svg": "image",
        "aside": "sidebar",
        "section": "section",
        "main": "container",
        "h1": "heading",
        "h2": "heading",
        "h3": "heading",
        "h4": "heading",
        "h5": "heading",
        "h6": "heading",
        "a": "link",
    }
    
    if tag in tag_type_map:
        return tag_type_map[tag]
    
    # Role-based detection
    role_type_map = {
        "navigation": "navbar",
        "banner": "header",
        "contentinfo": "footer",
        "button": "button",
        "link": "link",
        "form": "form",
        "textbox": "input",
        "dialog": "modal",
        "menu": "dropdown",
        "heading": "heading",
        "img": "image",
        "complementary": "sidebar",
        "main": "container",
        "region": "section",
    }
    
    if role in role_type_map:
        return role_type_map[role]
    
    # Class-based detection
    class_keywords = {
        "hero": "hero",
        "navbar": "navbar",
        "nav": "navbar",
        "navigation": "navbar",
        "header": "header",
        "footer": "footer",
        "card": "card",
        "btn": "button",
        "button": "button",
        "sidebar": "sidebar",
        "modal": "modal",
        "dialog": "modal",
        "dropdown": "dropdown",
        "menu": "dropdown",
        "form": "form",
        "container": "container",
        "wrapper": "container",
    }
    
    for cls in classes:
        for keyword, element_type in class_keywords.items():
            if keyword in cls:
                return element_type
    
    # ID-based detection
    for keyword, element_type in class_keywords.items():
        if keyword in element_id:
            return element_type
    
    return "other"


def interpret_user_query(query: str) -> dict[str, Any]:
    """Interpret a vague user query to determine what UI elements they're referring to."""
    
    query_lower = query.lower()
    
    result = {
        "element_types": [],
        "issue_hints": [],
        "interpreted_meaning": "",
    }
    
    # Detect element types mentioned
    for element_type, keywords in QUERY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                if element_type not in result["element_types"]:
                    result["element_types"].append(element_type)
    
    # Detect issue types
    issue_keywords = {
        "broken": ["broken", "messed up", "messed", "wrong", "bad", "ugly", "terrible"],
        "alignment": ["aligned", "alignment", "align", "center", "centered", "left", "right", "off"],
        "spacing": ["spacing", "space", "gap", "margin", "padding", "too close", "too far", "crowded"],
        "overlap": ["overlap", "overlapping", "on top of", "behind", "in front"],
        "size": ["too big", "too small", "size", "width", "height", "narrow", "wide"],
        "visibility": ["hidden", "invisible", "can't see", "not showing", "missing", "disappeared"],
        "color": ["color", "colour", "dark", "light", "contrast", "faded", "bright"],
        "responsive": ["mobile", "phone", "tablet", "responsive", "screen size", "shrink"],
        "layout": ["layout", "grid", "flex", "row", "column", "side by side", "stacked"],
        "text": ["text", "font", "readable", "unreadable", "too small", "too big"],
        "position": ["position", "moved", "shifted", "wrong place", "top", "bottom"],
    }
    
    for issue_type, keywords in issue_keywords.items():
        for keyword in keywords:
            if keyword in query_lower:
                if issue_type not in result["issue_hints"]:
                    result["issue_hints"].append(issue_type)
    
    # Generate interpreted meaning
    elements_str = ", ".join(result["element_types"]) if result["element_types"] else "general UI"
    issues_str = ", ".join(result["issue_hints"]) if result["issue_hints"] else "unknown issues"
    
    result["interpreted_meaning"] = f"User is reporting {issues_str} with the {elements_str}"
    
    return result


async def detect_ui_issues(page: Page, elements: list[UIElement]) -> list[UIIssue]:
    """Detect common UI issues based on element analysis."""
    
    issues: list[UIIssue] = []
    
    # Run JavaScript to detect issues
    detected_issues = await page.evaluate(
        """() => {
            const issues = [];
            
            // Check for overflow issues
            document.querySelectorAll('*').forEach(el => {
                const rect = el.getBoundingClientRect();
                const style = getComputedStyle(el);
                
                // Element extends beyond viewport
                if (rect.right > window.innerWidth && style.position !== 'fixed') {
                    if (el.scrollWidth > el.clientWidth && style.overflowX === 'visible') {
                        issues.push({
                            selector: el.id ? '#' + el.id : el.className ? '.' + el.className.split(' ')[0] : el.tagName.toLowerCase(),
                            type: 'overflow_hidden',
                            description: 'Element extends beyond viewport causing horizontal scroll',
                            element_type: el.tagName.toLowerCase()
                        });
                    }
                }
                
                // Check for very high z-index (potential stacking issues)
                const zIndex = parseInt(style.zIndex);
                if (zIndex > 9999) {
                    issues.push({
                        selector: el.id ? '#' + el.id : el.className ? '.' + el.className.split(' ')[0] : el.tagName.toLowerCase(),
                        type: 'z_index_conflict',
                        description: `Element has extremely high z-index (${zIndex}) which may cause stacking issues`,
                        element_type: el.tagName.toLowerCase(),
                        current_value: zIndex.toString()
                    });
                }
            });
            
            // Check for empty containers
            document.querySelectorAll('div, section, main, article').forEach(el => {
                if (el.children.length === 0 && el.textContent?.trim() === '') {
                    const rect = el.getBoundingClientRect();
                    if (rect.height > 50) {
                        issues.push({
                            selector: el.id ? '#' + el.id : el.className ? '.' + el.className.split(' ')[0] : el.tagName.toLowerCase(),
                            type: 'empty_container',
                            description: 'Empty container taking up space',
                            element_type: 'container'
                        });
                    }
                }
            });
            
            // Check for accessibility issues
            document.querySelectorAll('img').forEach(el => {
                if (!el.alt && !el.getAttribute('aria-label')) {
                    issues.push({
                        selector: el.id ? '#' + el.id : el.className ? '.' + el.className.split(' ')[0] : 'img',
                        type: 'accessibility_missing',
                        description: 'Image missing alt text',
                        element_type: 'image'
                    });
                }
            });
            
            document.querySelectorAll('button, a').forEach(el => {
                if (!el.textContent?.trim() && !el.getAttribute('aria-label')) {
                    issues.push({
                        selector: el.id ? '#' + el.id : el.className ? '.' + el.className.split(' ')[0] : el.tagName.toLowerCase(),
                        type: 'accessibility_missing',
                        description: 'Interactive element missing accessible name',
                        element_type: el.tagName.toLowerCase() === 'button' ? 'button' : 'link'
                    });
                }
            });
            
            return issues.slice(0, 20);
        }"""
    )
    
    for issue_data in detected_issues:
        issues.append(
            UIIssue(
                severity="warning",
                element_selector=issue_data["selector"],
                element_type=issue_data.get("element_type", "other"),
                issue_type=issue_data.get("type", "other"),
                description=issue_data["description"],
                suggested_fix=generate_fix_suggestion(issue_data),
                current_value=issue_data.get("current_value"),
            )
        )
    
    return issues


def generate_fix_suggestion(issue_data: dict[str, Any]) -> str:
    """Generate a fix suggestion for a detected issue."""
    
    issue_type = issue_data.get("type", "")
    selector = issue_data.get("selector", "element")
    
    suggestions = {
        "overflow_hidden": f"Add 'overflow-x: hidden' to the parent container or 'max-width: 100%' to {selector}",
        "z_index_conflict": f"Reduce z-index on {selector} to a reasonable value (10-100 for most UI elements)",
        "empty_container": f"Remove the empty {selector} element or add content to it",
        "accessibility_missing": f"Add appropriate alt text or aria-label to {selector}",
        "element_overlap": f"Adjust position or z-index of {selector} to prevent overlap",
        "spacing_inconsistent": f"Standardize padding/margin values on {selector}",
    }
    
    return suggestions.get(issue_type, f"Review and fix the {issue_type} issue on {selector}")


async def analyze_page_full(
    page: Page,
    url: str,
    user_query: str | None = None,
    include_screenshot: bool = True,
) -> UIAnalysisResult:
    """Perform a full analysis of a webpage."""
    
    # Get page title
    title = await page.title()
    
    viewport = page.viewport_size
    viewport_width = viewport["width"] if viewport else 1920
    viewport_height = viewport["height"] if viewport else 1080
    
    # Identify elements
    query_info = interpret_user_query(user_query) if user_query else {}
    target_types = query_info.get("element_types", [])
    
    elements = []
    if target_types:
        for element_type in target_types:
            elements.extend(await identify_elements(page, element_type))
    else:
        elements = await identify_elements(page)
    
    # Get accessibility tree
    accessibility_tree = await get_accessibility_tree(page)
    
    # Get DOM structure
    dom_structure = await get_dom_structure(page)
    
    # Detect issues
    issues = await detect_ui_issues(page, elements)
    
    # Capture screenshot
    screenshot_base64 = None
    if include_screenshot:
        screenshot_bytes = await capture_screenshot(page)
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
    
    # Count elements by type
    elements_summary = {}
    for el in elements:
        el_type = el.element_type
        elements_summary[el_type] = elements_summary.get(el_type, 0) + 1
    
    # Generate analysis notes
    analysis_notes = []
    if query_info:
        analysis_notes.append(query_info.get("interpreted_meaning", ""))
    
    return UIAnalysisResult(
        url=url,
        page_title=title,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        elements_summary=elements_summary,
        elements=elements,
        issues=issues,
        accessibility_tree=accessibility_tree,
        dom_structure=dom_structure,
        screenshot_base64=screenshot_base64,
        analysis_notes=analysis_notes,
    )


async def generate_fix_instructions_for_query(
    page: Page,
    url: str,
    user_query: str,
    elements: list[UIElement],
    issues: list[UIIssue],
) -> FixInstructionsResult:
    """Generate precise fix instructions based on user query and detected issues."""
    
    query_info = interpret_user_query(user_query)
    
    # Find relevant elements
    target_types = query_info.get("element_types", [])
    affected_elements = [
        el for el in elements if el.element_type in target_types
    ] if target_types else elements[:10]
    
    # Generate fix instructions
    fix_instructions: list[FixInstruction] = []
    css_changes: list[str] = []
    html_changes: list[str] = []
    
    priority = 1
    
    # Process detected issues
    for issue in issues:
        if not target_types or any(t in issue.element_type for t in target_types):
            instruction = create_fix_instruction(issue, priority)
            fix_instructions.append(instruction)
            
            if instruction.property_changes:
                css_rule = f"{issue.element_selector} {{\n"
                for prop, value in instruction.property_changes.items():
                    css_rule += f"    {prop}: {value};\n"
                css_rule += "}"
                css_changes.append(css_rule)
            
            priority += 1
    
    # Add general fixes based on query hints
    issue_hints = query_info.get("issue_hints", [])
    for hint in issue_hints:
        if hint == "spacing" and affected_elements:
            for el in affected_elements[:3]:
                fix_instructions.append(
                    FixInstruction(
                        priority=priority,
                        target_description=f"Adjust spacing on {el.element_type}",
                        selector=el.selector,
                        action="modify_css",
                        property_changes={
                            "padding": "1rem",
                            "margin": "0 auto",
                            "gap": "1rem",
                        },
                        explanation=f"Standardize spacing on the {el.element_type} element to fix layout issues",
                    )
                )
                priority += 1
        
        elif hint == "alignment" and affected_elements:
            for el in affected_elements[:3]:
                fix_instructions.append(
                    FixInstruction(
                        priority=priority,
                        target_description=f"Fix alignment on {el.element_type}",
                        selector=el.selector,
                        action="modify_css",
                        property_changes={
                            "display": "flex",
                            "align-items": "center",
                            "justify-content": "center",
                        },
                        explanation=f"Use flexbox to properly align content within {el.element_type}",
                    )
                )
                priority += 1
        
        elif hint == "layout" and affected_elements:
            for el in affected_elements[:2]:
                fix_instructions.append(
                    FixInstruction(
                        priority=priority,
                        target_description=f"Fix layout on {el.element_type}",
                        selector=el.selector,
                        action="modify_css",
                        property_changes={
                            "display": "flex",
                            "flex-direction": "row",
                            "flex-wrap": "wrap",
                            "gap": "1rem",
                        },
                        explanation=f"Apply proper flexbox layout to {el.element_type}",
                    )
                )
                priority += 1
    
    # Generate summary
    summary_parts = []
    if fix_instructions:
        summary_parts.append(f"Found {len(fix_instructions)} fixes to apply")
    if affected_elements:
        summary_parts.append(f"Affects {len(affected_elements)} elements")
    summary = ". ".join(summary_parts) if summary_parts else "No specific fixes identified"
    
    # Combine CSS changes
    css_changes_str = "\n\n".join(css_changes) if css_changes else ""
    
    return FixInstructionsResult(
        url=url,
        user_query=user_query,
        interpreted_problem=query_info.get("interpreted_meaning", "General UI issue"),
        affected_elements=affected_elements,
        fix_instructions=fix_instructions,
        summary=summary,
        css_changes=css_changes_str,
        html_changes="\n".join(html_changes) if html_changes else "",
        additional_recommendations=generate_recommendations(query_info, elements),
    )


def create_fix_instruction(issue: UIIssue, priority: int) -> FixInstruction:
    """Create a fix instruction from a UI issue."""
    
    action_map = {
        "layout_broken": "modify_css",
        "overflow_hidden": "modify_css",
        "z_index_conflict": "modify_css",
        "spacing_inconsistent": "modify_css",
        "alignment_off": "modify_css",
        "element_overlap": "modify_css",
        "broken_flexbox": "modify_css",
        "broken_grid": "modify_css",
        "accessibility_missing": "modify_html",
        "empty_container": "remove_html",
    }
    
    property_changes = {}
    
    if issue.css_property and issue.recommended_value:
        property_changes[issue.css_property] = issue.recommended_value
    elif issue.issue_type == "overflow_hidden":
        property_changes["overflow-x"] = "hidden"
        property_changes["max-width"] = "100%"
    elif issue.issue_type == "z_index_conflict":
        property_changes["z-index"] = "10"
    elif issue.issue_type == "spacing_inconsistent":
        property_changes["padding"] = "1rem"
        property_changes["margin"] = "0"
    
    return FixInstruction(
        priority=priority,
        target_description=f"Fix {issue.issue_type} on {issue.element_type}",
        selector=issue.element_selector,
        action=action_map.get(issue.issue_type, "modify_css"),
        property_changes=property_changes,
        explanation=issue.suggested_fix,
        code_snippet=issue.code_snippet,
    )


def generate_recommendations(query_info: dict[str, Any], elements: list[UIElement]) -> list[str]:
    """Generate additional recommendations based on analysis."""
    
    recommendations = []
    
    # Check for common patterns
    element_types = [el.element_type for el in elements]
    
    if "navbar" not in element_types:
        recommendations.append("Consider adding a proper <nav> element with role='navigation' for better accessibility")
    
    if "footer" not in element_types:
        recommendations.append("Consider adding a <footer> element for site information and links")
    
    # Check for issue hints
    issue_hints = query_info.get("issue_hints", [])
    
    if "responsive" in issue_hints:
        recommendations.append("Add CSS media queries to handle different screen sizes")
        recommendations.append("Use relative units (rem, %, vw) instead of fixed pixels for better responsiveness")
    
    if "layout" in issue_hints:
        recommendations.append("Consider using CSS Grid or Flexbox for complex layouts")
        recommendations.append("Use a consistent spacing system (e.g., 0.5rem, 1rem, 2rem)")
    
    return recommendations
