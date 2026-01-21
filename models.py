"""
Pydantic models for UI Analyzer MCP Server.
Defines structured data types for UI elements, issues, and analysis results.
"""

from typing import Literal
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Represents the position and size of an element on the page."""
    
    x: float = Field(description="X coordinate from left edge in pixels")
    y: float = Field(description="Y coordinate from top edge in pixels")
    width: float = Field(description="Element width in pixels")
    height: float = Field(description="Element height in pixels")


class ComputedStyles(BaseModel):
    """Key computed CSS styles for an element."""
    
    background_color: str | None = None
    color: str | None = None
    font_size: str | None = None
    font_family: str | None = None
    padding: str | None = None
    margin: str | None = None
    border: str | None = None
    display: str | None = None
    position: str | None = None
    z_index: str | None = None
    flex_direction: str | None = None
    justify_content: str | None = None
    align_items: str | None = None
    gap: str | None = None
    width: str | None = None
    height: str | None = None


class UIElement(BaseModel):
    """Represents a UI element identified on the page."""
    
    element_type: Literal[
        "button", 
        "link", 
        "heading", 
        "navbar", 
        "header", 
        "footer", 
        "hero", 
        "form", 
        "input",
        "image", 
        "section",
        "card",
        "modal",
        "dropdown",
        "menu",
        "sidebar",
        "container",
        "other"
    ] = Field(description="Semantic type of the UI element")
    
    tag_name: str = Field(description="HTML tag name (e.g., div, button, nav)")
    selector: str = Field(description="CSS selector to target this element")
    xpath: str | None = Field(default=None, description="XPath selector for precise targeting")
    text_content: str | None = Field(default=None, description="Visible text content, truncated if long")
    bounding_box: BoundingBox | None = Field(default=None, description="Position and size on page")
    aria_role: str | None = Field(default=None, description="ARIA role attribute")
    aria_label: str | None = Field(default=None, description="ARIA label for accessibility")
    classes: list[str] = Field(default_factory=list, description="CSS class names")
    element_id: str | None = Field(default=None, description="HTML id attribute")
    computed_styles: ComputedStyles | None = Field(default=None, description="Key computed CSS styles")
    children_count: int = Field(default=0, description="Number of direct child elements")
    is_visible: bool = Field(default=True, description="Whether element is visible on page")
    issues: list[str] = Field(default_factory=list, description="Detected issues with this element")


class UIIssue(BaseModel):
    """Represents a potential UI issue or problem detected on the page."""
    
    severity: Literal["error", "warning", "info"] = Field(
        description="Issue severity level"
    )
    element_selector: str = Field(description="CSS selector of the affected element")
    element_type: str = Field(description="Type of element affected")
    issue_type: Literal[
        "layout_broken",
        "overflow_hidden",
        "z_index_conflict", 
        "spacing_inconsistent",
        "alignment_off",
        "responsive_issue",
        "accessibility_missing",
        "contrast_low",
        "element_overlap",
        "invisible_element",
        "empty_container",
        "orphaned_element",
        "style_inconsistency",
        "missing_hover_state",
        "broken_flexbox",
        "broken_grid",
        "font_issue",
        "color_issue",
        "size_issue",
        "position_issue",
        "other"
    ] = Field(description="Category of the issue")
    description: str = Field(description="Human-readable description of the issue")
    suggested_fix: str = Field(description="Specific code change or CSS fix to resolve the issue")
    css_property: str | None = Field(default=None, description="The CSS property that needs to be changed")
    current_value: str | None = Field(default=None, description="Current value of the problematic property")
    recommended_value: str | None = Field(default=None, description="Recommended value to fix the issue")
    code_snippet: str | None = Field(default=None, description="Example code snippet showing the fix")


class ElementQuery(BaseModel):
    """Query parameters for finding specific UI elements."""
    
    element_type: str | None = Field(
        default=None,
        description="Type of element to find: navbar, header, footer, hero, button, form, etc."
    )
    text_contains: str | None = Field(
        default=None,
        description="Find elements containing this text"
    )
    selector: str | None = Field(
        default=None,
        description="Custom CSS selector to use"
    )
    near_text: str | None = Field(
        default=None,
        description="Find elements near text content (useful for vague queries)"
    )


class UIAnalysisResult(BaseModel):
    """Complete result of analyzing a webpage UI."""
    
    url: str = Field(description="URL that was analyzed")
    page_title: str = Field(description="Page title from document")
    viewport_width: int = Field(description="Viewport width used for analysis")
    viewport_height: int = Field(description="Viewport height used for analysis")
    
    elements_summary: dict[str, int] = Field(
        default_factory=dict,
        description="Count of each element type found"
    )
    
    elements: list[UIElement] = Field(
        default_factory=list,
        description="All identified UI elements"
    )
    
    issues: list[UIIssue] = Field(
        default_factory=list,
        description="Detected UI issues and problems"
    )
    
    accessibility_tree: str = Field(
        default="",
        description="ARIA accessibility tree snapshot in YAML format"
    )
    
    dom_structure: str = Field(
        default="",
        description="Simplified DOM structure showing element hierarchy"
    )
    
    screenshot_base64: str | None = Field(
        default=None,
        description="Base64 encoded PNG screenshot of the page"
    )
    
    analysis_notes: list[str] = Field(
        default_factory=list,
        description="Additional observations about the UI"
    )


class FixInstruction(BaseModel):
    """Precise instruction for fixing a UI issue."""
    
    priority: int = Field(description="Priority order for applying fixes (1 = highest)")
    target_description: str = Field(description="Human description of what element to target")
    selector: str = Field(description="CSS selector to find the element")
    file_hint: str | None = Field(
        default=None,
        description="Likely file where this element is defined (based on class names)"
    )
    action: Literal[
        "modify_css",
        "add_css",
        "remove_css",
        "modify_html",
        "add_html",
        "remove_html",
        "wrap_element",
        "unwrap_element",
        "move_element",
        "add_class",
        "remove_class",
        "restructure"
    ] = Field(description="Type of action to take")
    
    property_changes: dict[str, str] = Field(
        default_factory=dict,
        description="CSS properties to change: {property: new_value}"
    )
    
    before_code: str | None = Field(
        default=None,
        description="Example of current problematic code"
    )
    
    after_code: str | None = Field(
        default=None,
        description="Example of corrected code"
    )
    
    explanation: str = Field(
        description="Clear explanation of why this change fixes the issue"
    )


class FixInstructionsResult(BaseModel):
    """Complete set of fix instructions for resolving UI issues."""
    
    url: str = Field(description="URL that was analyzed")
    user_query: str = Field(description="Original user query/complaint about the UI")
    interpreted_problem: str = Field(
        description="How the analyzer interpreted the user's vague query"
    )
    
    affected_elements: list[UIElement] = Field(
        default_factory=list,
        description="Elements identified as related to the problem"
    )
    
    fix_instructions: list[FixInstruction] = Field(
        default_factory=list,
        description="Ordered list of fix instructions to apply"
    )
    
    summary: str = Field(
        description="Brief summary of all changes needed"
    )
    
    css_changes: str = Field(
        default="",
        description="Complete CSS changes as a code block"
    )
    
    html_changes: str = Field(
        default="",
        description="HTML structure changes if needed"
    )
    
    additional_recommendations: list[str] = Field(
        default_factory=list,
        description="Extra suggestions for improving the UI"
    )
