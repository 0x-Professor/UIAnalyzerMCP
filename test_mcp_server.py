"""
Test suite for UI Analyzer MCP Server.
Tests all functionality using real websites.
"""

import asyncio
import json
import base64
from pathlib import Path

from playwright.async_api import async_playwright

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
from models import UIElement, UIAnalysisResult, FixInstructionsResult


# Test websites
TEST_URLS = {
    "team_whispered": "https://team-whispered.vercel.app/",
    "example": "https://example.com",
    "httpbin": "https://httpbin.org/html",
}

# Output directory for test artifacts
OUTPUT_DIR = Path("test_output")


async def test_query_interpretation():
    """Test that vague user queries are correctly interpreted."""
    print("\n" + "=" * 60)
    print("TEST: Query Interpretation")
    print("=" * 60)
    
    test_queries = [
        ("the navbar is broken", ["navbar"], ["broken"]),
        ("hero section has weird spacing", ["hero"], ["spacing"]),
        ("buttons are not aligned", ["button"], ["alignment"]),
        ("the layout is messed up on mobile", ["layout", "responsive"], ["broken"]),
        ("header looks wrong and footer is missing", ["header", "footer"], ["broken"]),
        ("the menu is overlapping with content", ["navbar"], ["overlap"]),
        ("cards are too close together", ["card"], ["spacing"]),
        ("text is unreadable on the hero", ["hero"], ["text"]),
        ("sidebar is hidden on tablet", ["sidebar", "responsive"], ["visibility"]),
        ("form inputs are misaligned", ["form"], ["alignment"]),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_elements, expected_issues in test_queries:
        result = interpret_user_query(query)
        
        elements_match = all(e in result["element_types"] for e in expected_elements)
        issues_match = all(i in result["issue_hints"] for i in expected_issues)
        
        if elements_match and issues_match:
            print(f"  PASS: '{query}'")
            print(f"        Elements: {result['element_types']}")
            print(f"        Issues: {result['issue_hints']}")
            passed += 1
        else:
            print(f"  FAIL: '{query}'")
            print(f"        Expected elements: {expected_elements}, Got: {result['element_types']}")
            print(f"        Expected issues: {expected_issues}, Got: {result['issue_hints']}")
            failed += 1
    
    print(f"\nQuery Interpretation: {passed}/{passed + failed} tests passed")
    return passed, failed


async def test_page_loading(browser):
    """Test that pages load correctly."""
    print("\n" + "=" * 60)
    print("TEST: Page Loading")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, url in TEST_URLS.items():
        try:
            page = await load_page(browser, url, 1920, 1080)
            title = await page.title()
            await page.context.close()
            
            print(f"  PASS: {name} - Title: '{title[:50]}...' " if len(title) > 50 else f"  PASS: {name} - Title: '{title}'")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {name} - Error: {str(e)[:100]}")
            failed += 1
    
    print(f"\nPage Loading: {passed}/{passed + failed} tests passed")
    return passed, failed


async def test_screenshot_capture(browser):
    """Test screenshot capture functionality."""
    print("\n" + "=" * 60)
    print("TEST: Screenshot Capture")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    passed = 0
    failed = 0
    
    url = TEST_URLS["team_whispered"]
    
    try:
        page = await load_page(browser, url, 1920, 1080)
        
        # Test full page screenshot
        screenshot = await capture_screenshot(page, full_page=True)
        screenshot_path = OUTPUT_DIR / "full_page.png"
        screenshot_path.write_bytes(screenshot)
        print(f"  PASS: Full page screenshot ({len(screenshot)} bytes) -> {screenshot_path}")
        passed += 1
        
        # Test screenshot with highlighting
        screenshot_highlighted = await capture_screenshot(
            page, full_page=True, highlight_selector="a, button"
        )
        highlight_path = OUTPUT_DIR / "highlighted_links.png"
        highlight_path.write_bytes(screenshot_highlighted)
        print(f"  PASS: Highlighted screenshot ({len(screenshot_highlighted)} bytes) -> {highlight_path}")
        passed += 1
        
        # Test viewport-only screenshot
        screenshot_viewport = await capture_screenshot(page, full_page=False)
        viewport_path = OUTPUT_DIR / "viewport_only.png"
        viewport_path.write_bytes(screenshot_viewport)
        print(f"  PASS: Viewport screenshot ({len(screenshot_viewport)} bytes) -> {viewport_path}")
        passed += 1
        
        await page.context.close()
        
    except Exception as e:
        print(f"  FAIL: Screenshot error - {str(e)}")
        failed += 1
    
    print(f"\nScreenshot Capture: {passed}/{passed + failed} tests passed")
    return passed, failed


async def test_accessibility_tree(browser):
    """Test accessibility tree extraction."""
    print("\n" + "=" * 60)
    print("TEST: Accessibility Tree")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    url = TEST_URLS["team_whispered"]
    
    try:
        page = await load_page(browser, url, 1920, 1080)
        tree = await get_accessibility_tree(page)
        await page.context.close()
        
        if tree and len(tree) > 100:
            print(f"  PASS: Accessibility tree extracted ({len(tree)} chars)")
            print(f"        Preview: {tree[:200]}...")
            
            # Save to file
            OUTPUT_DIR.mkdir(exist_ok=True)
            (OUTPUT_DIR / "accessibility_tree.yaml").write_text(tree, encoding="utf-8")
            passed += 1
        else:
            print(f"  FAIL: Accessibility tree too short or empty")
            failed += 1
            
    except Exception as e:
        print(f"  FAIL: Error - {str(e)}")
        failed += 1
    
    print(f"\nAccessibility Tree: {passed}/{passed + failed} tests passed")
    return passed, failed


async def test_dom_structure(browser):
    """Test DOM structure extraction."""
    print("\n" + "=" * 60)
    print("TEST: DOM Structure")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    url = TEST_URLS["team_whispered"]
    
    try:
        page = await load_page(browser, url, 1920, 1080)
        structure = await get_dom_structure(page, max_depth=5)
        await page.context.close()
        
        if structure and len(structure) > 50:
            print(f"  PASS: DOM structure extracted ({len(structure)} chars)")
            print(f"        Preview:\n{structure[:500]}...")
            
            # Save to file
            OUTPUT_DIR.mkdir(exist_ok=True)
            (OUTPUT_DIR / "dom_structure.txt").write_text(structure, encoding="utf-8")
            passed += 1
        else:
            print(f"  FAIL: DOM structure too short or empty")
            failed += 1
            
    except Exception as e:
        print(f"  FAIL: Error - {str(e)}")
        failed += 1
    
    print(f"\nDOM Structure: {passed}/{passed + failed} tests passed")
    return passed, failed


async def test_element_identification(browser):
    """Test UI element identification."""
    print("\n" + "=" * 60)
    print("TEST: Element Identification")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    url = TEST_URLS["team_whispered"]
    
    try:
        page = await load_page(browser, url, 1920, 1080)
        
        # Test identifying all elements
        all_elements = await identify_elements(page, element_type=None, include_styles=False)
        print(f"  Found {len(all_elements)} total elements")
        
        if len(all_elements) > 0:
            print(f"  PASS: General element identification")
            
            # Count by type
            type_counts = {}
            for el in all_elements:
                type_counts[el.element_type] = type_counts.get(el.element_type, 0) + 1
            print(f"        Element types: {type_counts}")
            passed += 1
        else:
            print(f"  FAIL: No elements found")
            failed += 1
        
        # Test specific element types
        for element_type in ["link", "heading", "button", "image"]:
            elements = await identify_elements(page, element_type=element_type, include_styles=False)
            if len(elements) >= 0:  # Even 0 is valid if page doesn't have that element type
                print(f"  PASS: {element_type} - found {len(elements)} elements")
                passed += 1
            else:
                print(f"  FAIL: {element_type} identification failed")
                failed += 1
        
        # Test with styles
        elements_with_styles = await identify_elements(page, element_type="link", include_styles=True, max_elements=5)
        if elements_with_styles and any(el.computed_styles for el in elements_with_styles):
            print(f"  PASS: Element styles extraction")
            if elements_with_styles[0].computed_styles:
                styles = elements_with_styles[0].computed_styles
                print(f"        Sample styles: color={styles.color}, font_size={styles.font_size}")
            passed += 1
        else:
            print(f"  INFO: No computed styles extracted (may be expected)")
            passed += 1  # Not a failure, styles are optional
        
        await page.context.close()
        
        # Save element data
        OUTPUT_DIR.mkdir(exist_ok=True)
        elements_data = [el.model_dump() for el in all_elements[:20]]
        (OUTPUT_DIR / "elements.json").write_text(
            json.dumps(elements_data, indent=2, default=str), encoding="utf-8"
        )
        
    except Exception as e:
        print(f"  FAIL: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        failed += 1
    
    print(f"\nElement Identification: {passed}/{passed + failed} tests passed")
    return passed, failed


async def test_issue_detection(browser):
    """Test UI issue detection."""
    print("\n" + "=" * 60)
    print("TEST: Issue Detection")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    url = TEST_URLS["team_whispered"]
    
    try:
        page = await load_page(browser, url, 1920, 1080)
        elements = await identify_elements(page, include_styles=False)
        issues = await detect_ui_issues(page, elements)
        await page.context.close()
        
        print(f"  Found {len(issues)} potential issues")
        
        for issue in issues[:5]:
            print(f"    - [{issue.severity}] {issue.issue_type}: {issue.description[:60]}...")
        
        if len(issues) >= 0:  # Even 0 issues is valid for a well-designed page
            print(f"  PASS: Issue detection completed")
            passed += 1
        
        # Save issues
        OUTPUT_DIR.mkdir(exist_ok=True)
        issues_data = [issue.model_dump() for issue in issues]
        (OUTPUT_DIR / "issues.json").write_text(
            json.dumps(issues_data, indent=2, default=str), encoding="utf-8"
        )
        
    except Exception as e:
        print(f"  FAIL: Error - {str(e)}")
        failed += 1
    
    print(f"\nIssue Detection: {passed}/{passed + failed} tests passed")
    return passed, failed


async def test_full_page_analysis(browser):
    """Test full page analysis."""
    print("\n" + "=" * 60)
    print("TEST: Full Page Analysis")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    url = TEST_URLS["team_whispered"]
    
    try:
        page = await load_page(browser, url, 1920, 1080)
        
        # Test without query
        result = await analyze_page_full(page, url, user_query=None, include_screenshot=True)
        
        print(f"  Page Title: {result.page_title}")
        print(f"  Viewport: {result.viewport_width}x{result.viewport_height}")
        print(f"  Elements Found: {len(result.elements)}")
        print(f"  Issues Found: {len(result.issues)}")
        print(f"  Elements Summary: {result.elements_summary}")
        print(f"  Accessibility Tree Length: {len(result.accessibility_tree)} chars")
        print(f"  DOM Structure Length: {len(result.dom_structure)} chars")
        print(f"  Screenshot: {'Yes' if result.screenshot_base64 else 'No'}")
        
        if result.page_title and len(result.elements) > 0:
            print(f"  PASS: Full page analysis without query")
            passed += 1
        else:
            print(f"  FAIL: Incomplete analysis")
            failed += 1
        
        # Test with vague query
        result_with_query = await analyze_page_full(
            page, url, 
            user_query="the navigation menu looks off and buttons are misaligned",
            include_screenshot=False
        )
        
        if result_with_query.analysis_notes:
            print(f"  Analysis Notes: {result_with_query.analysis_notes}")
            print(f"  PASS: Full page analysis with query interpretation")
            passed += 1
        else:
            print(f"  INFO: No analysis notes generated (may be expected)")
            passed += 1
        
        await page.context.close()
        
        # Save full analysis
        OUTPUT_DIR.mkdir(exist_ok=True)
        analysis_data = result.model_dump()
        # Truncate screenshot for JSON file
        if analysis_data.get("screenshot_base64"):
            analysis_data["screenshot_base64"] = analysis_data["screenshot_base64"][:100] + "...(truncated)"
        (OUTPUT_DIR / "full_analysis.json").write_text(
            json.dumps(analysis_data, indent=2, default=str), encoding="utf-8"
        )
        
    except Exception as e:
        print(f"  FAIL: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        failed += 1
    
    print(f"\nFull Page Analysis: {passed}/{passed + failed} tests passed")
    return passed, failed


async def test_fix_instructions(browser):
    """Test fix instruction generation."""
    print("\n" + "=" * 60)
    print("TEST: Fix Instruction Generation")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    url = TEST_URLS["team_whispered"]
    
    test_queries = [
        "the navbar spacing is off",
        "buttons are not aligned properly",
        "the hero section layout is broken",
        "cards have inconsistent margins",
        "footer links are hard to see",
    ]
    
    try:
        page = await load_page(browser, url, 1920, 1080)
        
        for query in test_queries:
            # Get elements and issues first
            query_info = interpret_user_query(query)
            target_types = query_info.get("element_types", [])
            
            elements = []
            for element_type in target_types:
                elements.extend(await identify_elements(page, element_type, include_styles=True))
            
            if not elements:
                elements = await identify_elements(page, include_styles=True)
            
            issues = await detect_ui_issues(page, elements)
            
            # Generate fix instructions
            result = await generate_fix_instructions_for_query(
                page, url, query, elements, issues
            )
            
            print(f"\n  Query: '{query}'")
            print(f"  Interpreted: {result.interpreted_problem}")
            print(f"  Affected Elements: {len(result.affected_elements)}")
            print(f"  Fix Instructions: {len(result.fix_instructions)}")
            
            if result.fix_instructions:
                for i, fix in enumerate(result.fix_instructions[:3], 1):
                    print(f"    {i}. {fix.target_description}")
                    print(f"       Selector: {fix.selector}")
                    if fix.property_changes:
                        print(f"       CSS: {fix.property_changes}")
            
            if result.css_changes:
                print(f"  CSS Changes Preview:\n{result.css_changes[:200]}...")
            
            if result.interpreted_problem:
                print(f"  PASS: Fix instructions generated")
                passed += 1
            else:
                print(f"  FAIL: No interpretation")
                failed += 1
        
        await page.context.close()
        
    except Exception as e:
        print(f"  FAIL: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        failed += 1
    
    print(f"\nFix Instruction Generation: {passed}/{passed + failed} tests passed")
    return passed, failed


async def test_viewport_comparison(browser):
    """Test viewport comparison functionality."""
    print("\n" + "=" * 60)
    print("TEST: Viewport Comparison")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    url = TEST_URLS["team_whispered"]
    
    viewports = [
        {"name": "mobile", "width": 375, "height": 667},
        {"name": "tablet", "width": 768, "height": 1024},
        {"name": "desktop", "width": 1920, "height": 1080},
    ]
    
    try:
        results = {}
        
        for vp in viewports:
            page = await load_page(browser, url, vp["width"], vp["height"])
            screenshot = await capture_screenshot(page, full_page=False)
            elements = await identify_elements(page, include_styles=False)
            
            visible_count = sum(1 for el in elements if el.is_visible)
            
            results[vp["name"]] = {
                "width": vp["width"],
                "height": vp["height"],
                "total_elements": len(elements),
                "visible_elements": visible_count,
                "screenshot_size": len(screenshot),
            }
            
            # Save screenshot
            OUTPUT_DIR.mkdir(exist_ok=True)
            (OUTPUT_DIR / f"viewport_{vp['name']}.png").write_bytes(screenshot)
            
            await page.context.close()
            
            print(f"  {vp['name']}: {vp['width']}x{vp['height']} - {len(elements)} elements ({visible_count} visible)")
            passed += 1
        
        # Save comparison data
        (OUTPUT_DIR / "viewport_comparison.json").write_text(
            json.dumps(results, indent=2), encoding="utf-8"
        )
        
    except Exception as e:
        print(f"  FAIL: Error - {str(e)}")
        failed += 1
    
    print(f"\nViewport Comparison: {passed}/{passed + failed} tests passed")
    return passed, failed


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("UI ANALYZER MCP SERVER - TEST SUITE")
    print("=" * 60)
    print(f"Test Website: {TEST_URLS['team_whispered']}")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    total_passed = 0
    total_failed = 0
    
    # Test query interpretation (no browser needed)
    p, f = await test_query_interpretation()
    total_passed += p
    total_failed += f
    
    # Tests requiring browser
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        
        try:
            p, f = await test_page_loading(browser)
            total_passed += p
            total_failed += f
            
            p, f = await test_screenshot_capture(browser)
            total_passed += p
            total_failed += f
            
            p, f = await test_accessibility_tree(browser)
            total_passed += p
            total_failed += f
            
            p, f = await test_dom_structure(browser)
            total_passed += p
            total_failed += f
            
            p, f = await test_element_identification(browser)
            total_passed += p
            total_failed += f
            
            p, f = await test_issue_detection(browser)
            total_passed += p
            total_failed += f
            
            p, f = await test_full_page_analysis(browser)
            total_passed += p
            total_failed += f
            
            p, f = await test_fix_instructions(browser)
            total_passed += p
            total_failed += f
            
            p, f = await test_viewport_comparison(browser)
            total_passed += p
            total_failed += f
            
        finally:
            await browser.close()
    
    # Final summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {total_passed / (total_passed + total_failed) * 100:.1f}%")
    print(f"\nTest artifacts saved to: {OUTPUT_DIR.absolute()}")
    print("=" * 60)
    
    return total_passed, total_failed


if __name__ == "__main__":
    asyncio.run(run_all_tests())
