"""
Framework and Technology Detection Module.
Detects frontend frameworks, CSS libraries, and build tools used in a webpage.
"""

from dataclasses import dataclass, field
from typing import Literal
from playwright.async_api import Page


@dataclass
class FrameworkInfo:
    """Information about a detected framework or library."""
    name: str
    version: str | None = None
    confidence: Literal["high", "medium", "low"] = "medium"
    category: Literal[
        "js_framework",
        "css_framework", 
        "ui_library",
        "build_tool",
        "meta_framework",
        "state_management",
        "animation",
        "icon_library",
        "other"
    ] = "other"
    indicators: list[str] = field(default_factory=list)


@dataclass 
class TechStackResult:
    """Complete technology stack detection result."""
    
    # Primary framework
    primary_framework: str | None = None
    
    # Meta frameworks (Next.js, Nuxt, etc.)
    meta_framework: str | None = None
    
    # CSS approach
    css_approach: str | None = None  # tailwind, css-modules, styled-components, etc.
    
    # All detected technologies
    frameworks: list[FrameworkInfo] = field(default_factory=list)
    
    # Raw detection data
    has_react: bool = False
    has_vue: bool = False
    has_angular: bool = False
    has_svelte: bool = False
    has_nextjs: bool = False
    has_nuxt: bool = False
    has_remix: bool = False
    has_astro: bool = False
    has_gatsby: bool = False
    has_vite: bool = False
    
    has_tailwind: bool = False
    has_bootstrap: bool = False
    has_material_ui: bool = False
    has_chakra_ui: bool = False
    has_shadcn: bool = False
    has_ant_design: bool = False
    has_bulma: bool = False
    has_foundation: bool = False
    
    has_vanilla_js: bool = False
    has_jquery: bool = False
    has_typescript: bool = False
    
    # CSS detection
    uses_css_modules: bool = False
    uses_styled_components: bool = False
    uses_emotion: bool = False
    uses_sass: bool = False
    uses_inline_styles: bool = False
    uses_css_variables: bool = False
    
    # Build/bundler hints
    bundler_hints: list[str] = field(default_factory=list)
    
    # Summary for AI assistants
    summary: str = ""
    
    # Framework-specific fix recommendations
    fix_approach: str = ""


# Detection patterns for frameworks
FRAMEWORK_PATTERNS = {
    # React detection
    "react": {
        "scripts": ["react", "react-dom", "react.production", "react.development"],
        "globals": ["React", "ReactDOM", "__REACT_DEVTOOLS_GLOBAL_HOOK__"],
        "attributes": ["data-reactroot", "data-reactid"],
        "patterns": ["_reactRootContainer", "__reactFiber", "__reactProps"],
        "class_patterns": [],
    },
    
    # Vue detection
    "vue": {
        "scripts": ["vue.js", "vue.min.js", "vue.global", "vue.esm"],
        "globals": ["Vue", "__VUE__", "__VUE_DEVTOOLS_GLOBAL_HOOK__"],
        "attributes": ["data-v-", "v-cloak", "v-if", "v-for", "v-bind", "v-on"],
        "patterns": ["__vue_app__", "_vnode"],
        "class_patterns": [],
    },
    
    # Angular detection  
    "angular": {
        "scripts": ["angular", "zone.js", "@angular/core"],
        "globals": ["ng", "getAllAngularRootElements", "Zone"],
        "attributes": ["ng-version", "_ngcontent", "_nghost", "ng-reflect"],
        "patterns": ["__ngContext__"],
        "class_patterns": [],
    },
    
    # Svelte detection
    "svelte": {
        "scripts": ["svelte"],
        "globals": [],
        "attributes": ["class*='svelte-'"],
        "patterns": ["__svelte"],
        "class_patterns": ["svelte-"],
    },
    
    # Next.js detection
    "nextjs": {
        "scripts": ["_next/static", "next/dist", "__NEXT_DATA__"],
        "globals": ["__NEXT_DATA__", "__NEXT_LOADED_PAGES__", "next"],
        "attributes": ["data-nscript", "data-next-font"],
        "patterns": ["_next/", "__next"],
        "class_patterns": ["__className_"],
    },
    
    # Nuxt detection
    "nuxt": {
        "scripts": ["_nuxt/", "nuxt"],
        "globals": ["__NUXT__", "$nuxt"],
        "attributes": ["data-n-head", "data-nuxt"],
        "patterns": ["_nuxt/"],
        "class_patterns": [],
    },
    
    # Remix detection
    "remix": {
        "scripts": ["remix", "@remix-run"],
        "globals": ["__remixContext", "__remixManifest"],
        "attributes": [],
        "patterns": ["__remix"],
        "class_patterns": [],
    },
    
    # Astro detection
    "astro": {
        "scripts": ["astro"],
        "globals": [],
        "attributes": ["data-astro-cid", "astro-island"],
        "patterns": ["astro:"],
        "class_patterns": ["astro-"],
    },
    
    # Gatsby detection
    "gatsby": {
        "scripts": ["gatsby"],
        "globals": ["___gatsby", "___loader"],
        "attributes": ["data-gatsby"],
        "patterns": ["gatsby-"],
        "class_patterns": [],
    },
    
    # Vite detection
    "vite": {
        "scripts": ["@vite", "vite/client"],
        "globals": ["__vite__"],
        "attributes": [],
        "patterns": ["/@vite/", "?v="],
        "class_patterns": [],
    },
    
    # jQuery detection
    "jquery": {
        "scripts": ["jquery", "jquery.min"],
        "globals": ["jQuery", "$"],
        "attributes": [],
        "patterns": [],
        "class_patterns": [],
    },
}


CSS_FRAMEWORK_PATTERNS = {
    # Tailwind CSS detection
    "tailwind": {
        "class_patterns": [
            "flex", "grid", "hidden", "block", "inline",
            "p-", "m-", "px-", "py-", "mx-", "my-", "pt-", "pb-", "pl-", "pr-",
            "w-", "h-", "min-w-", "min-h-", "max-w-", "max-h-",
            "text-", "font-", "leading-", "tracking-",
            "bg-", "border-", "rounded-", "shadow-",
            "hover:", "focus:", "active:", "disabled:",
            "sm:", "md:", "lg:", "xl:", "2xl:",
            "dark:", "group-", "peer-",
            "space-x-", "space-y-", "gap-",
            "justify-", "items-", "content-",
            "absolute", "relative", "fixed", "sticky",
            "top-", "bottom-", "left-", "right-",
            "z-", "opacity-", "transition-",
        ],
        "meta_content": ["tailwindcss", "tailwind"],
    },
    
    # Bootstrap detection
    "bootstrap": {
        "class_patterns": [
            "container", "container-fluid", "row", "col-",
            "btn", "btn-primary", "btn-secondary", "btn-success",
            "navbar", "nav-link", "nav-item",
            "card", "card-body", "card-header", "card-footer",
            "modal", "modal-dialog", "modal-content",
            "form-control", "form-group", "form-check",
            "table", "table-striped", "table-bordered",
            "alert", "alert-primary", "alert-danger",
            "badge", "dropdown", "carousel",
            "d-flex", "d-none", "d-block",
            "justify-content-", "align-items-",
            "mb-", "mt-", "ms-", "me-", "p-",
        ],
        "scripts": ["bootstrap", "bootstrap.min", "bootstrap.bundle"],
    },
    
    # Material UI / MUI detection
    "material_ui": {
        "class_patterns": [
            "MuiButton", "MuiTypography", "MuiBox",
            "MuiContainer", "MuiGrid", "MuiPaper",
            "MuiAppBar", "MuiToolbar", "MuiDrawer",
            "MuiCard", "MuiCardContent", "MuiCardActions",
            "MuiTextField", "MuiInput", "MuiSelect",
            "MuiTable", "MuiTableCell", "MuiTableRow",
            "Mui", "css-",
        ],
        "attributes": ["data-mui"],
    },
    
    # Chakra UI detection
    "chakra_ui": {
        "class_patterns": [
            "chakra-", "css-",
        ],
        "attributes": ["data-chakra"],
        "globals": ["chakra"],
    },
    
    # shadcn/ui detection (uses Tailwind + Radix)
    "shadcn": {
        "class_patterns": [
            "rounded-md", "rounded-lg",
            "ring-offset-", "focus-visible:ring-",
            "data-[state=", "data-[side=",
        ],
        "attributes": ["data-state", "data-side", "data-radix"],
    },
    
    # Ant Design detection
    "ant_design": {
        "class_patterns": [
            "ant-", "anticon",
            "ant-btn", "ant-input", "ant-select",
            "ant-table", "ant-form", "ant-modal",
            "ant-layout", "ant-menu", "ant-card",
        ],
    },
    
    # Bulma detection
    "bulma": {
        "class_patterns": [
            "column", "columns", "is-", "has-",
            "button", "is-primary", "is-success",
            "navbar", "navbar-item", "navbar-menu",
            "card", "card-content", "card-header",
            "box", "hero", "section",
            "notification", "message", "tag",
        ],
    },
    
    # Foundation detection
    "foundation": {
        "class_patterns": [
            "grid-x", "grid-y", "cell",
            "button", "button-group",
            "top-bar", "menu", "dropdown",
            "callout", "card", "reveal",
            "small-", "medium-", "large-",
        ],
    },
}


async def detect_tech_stack(page: Page) -> TechStackResult:
    """Detect the complete technology stack of a webpage."""
    
    result = TechStackResult()
    
    # Run comprehensive detection script
    detection_data = await page.evaluate("""() => {
        const result = {
            // Script sources
            scripts: [],
            // Link hrefs (stylesheets)
            stylesheets: [],
            // Meta tags
            metas: [],
            // Global variables
            globals: {},
            // HTML attributes found
            attributes: [],
            // Class names sample
            classNames: [],
            // Data attributes
            dataAttributes: [],
            // Inline styles count
            inlineStylesCount: 0,
            // CSS custom properties
            cssVariables: [],
            // HTML structure hints
            htmlHints: [],
        };
        
        // Collect script sources
        document.querySelectorAll('script[src]').forEach(s => {
            result.scripts.push(s.src);
        });
        
        // Collect inline script content hints
        document.querySelectorAll('script:not([src])').forEach(s => {
            const content = s.textContent || '';
            if (content.includes('__NEXT_DATA__')) result.htmlHints.push('nextjs_data');
            if (content.includes('__NUXT__')) result.htmlHints.push('nuxt_data');
            if (content.includes('__GATSBY')) result.htmlHints.push('gatsby_data');
            if (content.includes('__remixContext')) result.htmlHints.push('remix_data');
        });
        
        // Collect stylesheet links
        document.querySelectorAll('link[rel="stylesheet"]').forEach(l => {
            result.stylesheets.push(l.href);
        });
        
        // Collect meta tags
        document.querySelectorAll('meta').forEach(m => {
            if (m.name || m.property) {
                result.metas.push({
                    name: m.name || m.property,
                    content: m.content
                });
            }
        });
        
        // Check global variables
        const globalsToCheck = [
            'React', 'ReactDOM', '__REACT_DEVTOOLS_GLOBAL_HOOK__',
            'Vue', '__VUE__', '__VUE_DEVTOOLS_GLOBAL_HOOK__',
            'ng', 'Zone', 'getAllAngularRootElements',
            '__NEXT_DATA__', '__NEXT_LOADED_PAGES__', 'next',
            '__NUXT__', '$nuxt',
            '__remixContext', '__remixManifest',
            '___gatsby', '___loader',
            '__vite__',
            'jQuery', '$',
            'Alpine', 'htmx', 'Stimulus',
            'Svelte',
        ];
        
        globalsToCheck.forEach(g => {
            try {
                if (window[g] !== undefined) {
                    result.globals[g] = true;
                }
            } catch (e) {}
        });
        
        // Sample class names from body
        const allClasses = new Set();
        document.querySelectorAll('*').forEach(el => {
            el.classList.forEach(c => allClasses.add(c));
        });
        result.classNames = Array.from(allClasses).slice(0, 500);
        
        // Collect data attributes
        const dataAttrs = new Set();
        document.querySelectorAll('*').forEach(el => {
            Array.from(el.attributes).forEach(attr => {
                if (attr.name.startsWith('data-')) {
                    dataAttrs.add(attr.name);
                }
                // Framework-specific attributes
                if (attr.name.startsWith('ng-') || 
                    attr.name.startsWith('v-') ||
                    attr.name.startsWith('_ng') ||
                    attr.name.includes('react') ||
                    attr.name.includes('svelte')) {
                    result.attributes.push(attr.name);
                }
            });
        });
        result.dataAttributes = Array.from(dataAttrs);
        
        // Count inline styles
        result.inlineStylesCount = document.querySelectorAll('[style]').length;
        
        // Check for CSS variables
        const rootStyles = getComputedStyle(document.documentElement);
        const customProps = [];
        for (let i = 0; i < rootStyles.length; i++) {
            const prop = rootStyles[i];
            if (prop.startsWith('--')) {
                customProps.push(prop);
            }
        }
        result.cssVariables = customProps.slice(0, 50);
        
        // Check for specific elements
        if (document.querySelector('[data-reactroot]')) result.htmlHints.push('react_root');
        if (document.querySelector('#__next')) result.htmlHints.push('nextjs_root');
        if (document.querySelector('#__nuxt')) result.htmlHints.push('nuxt_root');
        if (document.querySelector('[ng-version]')) result.htmlHints.push('angular_version');
        if (document.querySelector('astro-island')) result.htmlHints.push('astro_island');
        
        return result;
    }""")
    
    # Analyze detection data
    frameworks = []
    
    # Check for React
    if (detection_data["globals"].get("React") or 
        detection_data["globals"].get("ReactDOM") or
        detection_data["globals"].get("__REACT_DEVTOOLS_GLOBAL_HOOK__") or
        "react_root" in detection_data["htmlHints"] or
        any("react" in s.lower() for s in detection_data["scripts"])):
        result.has_react = True
        frameworks.append(FrameworkInfo(
            name="React",
            category="js_framework",
            confidence="high" if detection_data["globals"].get("React") else "medium",
            indicators=["Global React object found"] if detection_data["globals"].get("React") else ["React patterns detected"]
        ))
    
    # Check for Vue
    if (detection_data["globals"].get("Vue") or 
        detection_data["globals"].get("__VUE__") or
        any("v-" in attr for attr in detection_data["attributes"]) or
        any("vue" in s.lower() for s in detection_data["scripts"])):
        result.has_vue = True
        frameworks.append(FrameworkInfo(
            name="Vue.js",
            category="js_framework",
            confidence="high" if detection_data["globals"].get("Vue") else "medium",
            indicators=["Global Vue object found"] if detection_data["globals"].get("Vue") else ["Vue patterns detected"]
        ))
    
    # Check for Angular
    if (detection_data["globals"].get("ng") or 
        detection_data["globals"].get("Zone") or
        "angular_version" in detection_data["htmlHints"] or
        any("ng-" in attr or "_ng" in attr for attr in detection_data["attributes"])):
        result.has_angular = True
        frameworks.append(FrameworkInfo(
            name="Angular",
            category="js_framework",
            confidence="high" if "angular_version" in detection_data["htmlHints"] else "medium",
            indicators=["Angular attributes detected"]
        ))
    
    # Check for Svelte
    svelte_classes = [c for c in detection_data["classNames"] if c.startswith("svelte-")]
    if svelte_classes or detection_data["globals"].get("Svelte"):
        result.has_svelte = True
        frameworks.append(FrameworkInfo(
            name="Svelte",
            category="js_framework",
            confidence="high" if svelte_classes else "medium",
            indicators=[f"Found {len(svelte_classes)} Svelte-scoped classes"]
        ))
    
    # Check for Next.js
    if (detection_data["globals"].get("__NEXT_DATA__") or 
        "nextjs_data" in detection_data["htmlHints"] or
        "nextjs_root" in detection_data["htmlHints"] or
        any("_next/" in s for s in detection_data["scripts"])):
        result.has_nextjs = True
        result.has_react = True  # Next.js uses React
        frameworks.append(FrameworkInfo(
            name="Next.js",
            category="meta_framework",
            confidence="high",
            indicators=["__NEXT_DATA__ found", "_next/ assets detected"]
        ))
    
    # Check for Nuxt
    if (detection_data["globals"].get("__NUXT__") or 
        detection_data["globals"].get("$nuxt") or
        "nuxt_data" in detection_data["htmlHints"] or
        "nuxt_root" in detection_data["htmlHints"]):
        result.has_nuxt = True
        result.has_vue = True  # Nuxt uses Vue
        frameworks.append(FrameworkInfo(
            name="Nuxt",
            category="meta_framework",
            confidence="high",
            indicators=["__NUXT__ global found"]
        ))
    
    # Check for Remix
    if (detection_data["globals"].get("__remixContext") or 
        "remix_data" in detection_data["htmlHints"]):
        result.has_remix = True
        result.has_react = True  # Remix uses React
        frameworks.append(FrameworkInfo(
            name="Remix",
            category="meta_framework",
            confidence="high",
            indicators=["Remix context found"]
        ))
    
    # Check for Astro
    if ("astro_island" in detection_data["htmlHints"] or
        any("data-astro" in attr for attr in detection_data["dataAttributes"])):
        result.has_astro = True
        frameworks.append(FrameworkInfo(
            name="Astro",
            category="meta_framework",
            confidence="high",
            indicators=["Astro islands detected"]
        ))
    
    # Check for Gatsby
    if (detection_data["globals"].get("___gatsby") or 
        "gatsby_data" in detection_data["htmlHints"]):
        result.has_gatsby = True
        result.has_react = True  # Gatsby uses React
        frameworks.append(FrameworkInfo(
            name="Gatsby",
            category="meta_framework",
            confidence="high",
            indicators=["Gatsby globals found"]
        ))
    
    # Check for Vite
    if detection_data["globals"].get("__vite__"):
        result.has_vite = True
        result.bundler_hints.append("Vite")
    
    # Check for jQuery
    if detection_data["globals"].get("jQuery") or detection_data["globals"].get("$"):
        result.has_jquery = True
        frameworks.append(FrameworkInfo(
            name="jQuery",
            category="js_framework",
            confidence="high",
            indicators=["jQuery global found"]
        ))
    
    # CSS Framework Detection
    class_names = set(detection_data["classNames"])
    
    # Tailwind detection
    tailwind_indicators = 0
    tailwind_patterns = ["flex", "grid", "hidden", "block", "inline-flex", "items-center",
                         "justify-center", "space-x-", "space-y-", "gap-", "rounded-",
                         "bg-", "text-", "font-", "p-", "m-", "px-", "py-", "mx-", "my-",
                         "w-", "h-", "min-", "max-", "border-", "shadow-", "hover:",
                         "focus:", "sm:", "md:", "lg:", "xl:", "dark:"]
    
    for pattern in tailwind_patterns:
        if any(pattern in c for c in class_names):
            tailwind_indicators += 1
    
    if tailwind_indicators >= 10:
        result.has_tailwind = True
        frameworks.append(FrameworkInfo(
            name="Tailwind CSS",
            category="css_framework",
            confidence="high" if tailwind_indicators >= 15 else "medium",
            indicators=[f"Found {tailwind_indicators} Tailwind utility class patterns"]
        ))
    
    # Bootstrap detection
    bootstrap_classes = ["container", "container-fluid", "row", "col-", "btn", "btn-", 
                        "navbar", "nav-", "card", "modal", "form-control", "table-"]
    bootstrap_count = sum(1 for bc in bootstrap_classes if any(bc in c for c in class_names))
    
    if bootstrap_count >= 5 or any("bootstrap" in s.lower() for s in detection_data["scripts"] + detection_data["stylesheets"]):
        result.has_bootstrap = True
        frameworks.append(FrameworkInfo(
            name="Bootstrap",
            category="css_framework",
            confidence="high" if bootstrap_count >= 8 else "medium",
            indicators=[f"Found {bootstrap_count} Bootstrap class patterns"]
        ))
    
    # Material UI detection
    mui_classes = [c for c in class_names if c.startswith("Mui") or c.startswith("css-")]
    if len(mui_classes) >= 5:
        result.has_material_ui = True
        frameworks.append(FrameworkInfo(
            name="Material UI",
            category="ui_library",
            confidence="high",
            indicators=[f"Found {len(mui_classes)} MUI classes"]
        ))
    
    # Chakra UI detection
    chakra_classes = [c for c in class_names if c.startswith("chakra-")]
    if chakra_classes or any("data-chakra" in attr for attr in detection_data["dataAttributes"]):
        result.has_chakra_ui = True
        frameworks.append(FrameworkInfo(
            name="Chakra UI",
            category="ui_library",
            confidence="high",
            indicators=["Chakra UI classes detected"]
        ))
    
    # shadcn/ui detection (Tailwind + Radix primitives)
    radix_attrs = [attr for attr in detection_data["dataAttributes"] 
                   if "data-state" in attr or "data-radix" in attr or "data-side" in attr]
    if radix_attrs and result.has_tailwind:
        result.has_shadcn = True
        frameworks.append(FrameworkInfo(
            name="shadcn/ui",
            category="ui_library",
            confidence="medium",
            indicators=["Radix UI primitives + Tailwind detected"]
        ))
    
    # Ant Design detection
    ant_classes = [c for c in class_names if c.startswith("ant-") or c.startswith("anticon")]
    if len(ant_classes) >= 3:
        result.has_ant_design = True
        frameworks.append(FrameworkInfo(
            name="Ant Design",
            category="ui_library",
            confidence="high",
            indicators=[f"Found {len(ant_classes)} Ant Design classes"]
        ))
    
    # Bulma detection
    bulma_patterns = ["column", "columns", "is-", "has-text-", "has-background-"]
    bulma_count = sum(1 for bp in bulma_patterns if any(bp in c for c in class_names))
    if bulma_count >= 3:
        result.has_bulma = True
        frameworks.append(FrameworkInfo(
            name="Bulma",
            category="css_framework",
            confidence="medium",
            indicators=["Bulma class patterns detected"]
        ))
    
    # Foundation detection
    foundation_patterns = ["grid-x", "grid-y", "cell", "small-", "medium-", "large-"]
    foundation_count = sum(1 for fp in foundation_patterns if any(fp in c for c in class_names))
    if foundation_count >= 3:
        result.has_foundation = True
        frameworks.append(FrameworkInfo(
            name="Foundation",
            category="css_framework",
            confidence="medium",
            indicators=["Foundation class patterns detected"]
        ))
    
    # CSS approach detection
    if result.has_tailwind:
        result.css_approach = "tailwind"
    elif result.has_bootstrap:
        result.css_approach = "bootstrap"
    elif result.has_material_ui or result.has_chakra_ui or result.has_ant_design:
        result.css_approach = "component-library"
    elif any("css-" in c for c in class_names):
        result.uses_css_modules = True
        result.css_approach = "css-modules"
    elif detection_data["inlineStylesCount"] > 20:
        result.uses_inline_styles = True
        result.css_approach = "inline-styles"
    else:
        result.css_approach = "traditional-css"
    
    # Check for CSS variables
    if len(detection_data["cssVariables"]) > 5:
        result.uses_css_variables = True
    
    # Vanilla JS detection (no framework)
    if not any([result.has_react, result.has_vue, result.has_angular, 
                result.has_svelte, result.has_jquery]):
        result.has_vanilla_js = True
        frameworks.append(FrameworkInfo(
            name="Vanilla JavaScript",
            category="js_framework",
            confidence="low",
            indicators=["No major JS framework detected"]
        ))
    
    result.frameworks = frameworks
    
    # Determine primary framework
    if result.has_nextjs:
        result.primary_framework = "Next.js"
        result.meta_framework = "Next.js"
    elif result.has_nuxt:
        result.primary_framework = "Nuxt"
        result.meta_framework = "Nuxt"
    elif result.has_remix:
        result.primary_framework = "Remix"
        result.meta_framework = "Remix"
    elif result.has_gatsby:
        result.primary_framework = "Gatsby"
        result.meta_framework = "Gatsby"
    elif result.has_astro:
        result.primary_framework = "Astro"
        result.meta_framework = "Astro"
    elif result.has_react:
        result.primary_framework = "React"
    elif result.has_vue:
        result.primary_framework = "Vue.js"
    elif result.has_angular:
        result.primary_framework = "Angular"
    elif result.has_svelte:
        result.primary_framework = "Svelte"
    else:
        result.primary_framework = "Vanilla JS/HTML"
    
    # Generate summary
    result.summary = generate_tech_summary(result)
    result.fix_approach = generate_fix_approach(result)
    
    return result


def generate_tech_summary(result: TechStackResult) -> str:
    """Generate a human-readable summary of the tech stack."""
    parts = []
    
    if result.meta_framework:
        parts.append(f"Meta Framework: {result.meta_framework}")
    elif result.primary_framework:
        parts.append(f"JS Framework: {result.primary_framework}")
    
    if result.css_approach:
        css_name = {
            "tailwind": "Tailwind CSS",
            "bootstrap": "Bootstrap",
            "component-library": "Component Library CSS",
            "css-modules": "CSS Modules",
            "inline-styles": "Inline Styles",
            "traditional-css": "Traditional CSS",
        }.get(result.css_approach, result.css_approach)
        parts.append(f"CSS: {css_name}")
    
    ui_libs = []
    if result.has_shadcn:
        ui_libs.append("shadcn/ui")
    if result.has_material_ui:
        ui_libs.append("Material UI")
    if result.has_chakra_ui:
        ui_libs.append("Chakra UI")
    if result.has_ant_design:
        ui_libs.append("Ant Design")
    
    if ui_libs:
        parts.append(f"UI Library: {', '.join(ui_libs)}")
    
    if result.uses_css_variables:
        parts.append("Uses CSS Variables")
    
    return " | ".join(parts) if parts else "Standard HTML/CSS/JS"


def generate_fix_approach(result: TechStackResult) -> str:
    """Generate framework-specific fix approach guidance."""
    
    approaches = []
    
    # Framework-specific guidance
    if result.has_nextjs:
        approaches.append(
            "Next.js: Use className prop for styling. Check globals.css for base styles. "
            "Component files are typically in /components or /app directories. "
            "For Tailwind issues, check tailwind.config.js for theme customization."
        )
    elif result.has_nuxt:
        approaches.append(
            "Nuxt: Check <style scoped> sections in .vue files. "
            "Global styles in assets/css or nuxt.config styles array. "
            "Use Nuxt DevTools to inspect component hierarchy."
        )
    elif result.has_react:
        approaches.append(
            "React: Styles can be in CSS files, CSS modules (.module.css), "
            "styled-components, or inline style objects. Check the component file imports."
        )
    elif result.has_vue:
        approaches.append(
            "Vue: Check <style> or <style scoped> in .vue files. "
            "Scoped styles only affect current component."
        )
    elif result.has_angular:
        approaches.append(
            "Angular: Check component.css/scss files alongside component.ts. "
            "Use ::ng-deep for child component styling (deprecated but common)."
        )
    elif result.has_svelte:
        approaches.append(
            "Svelte: Styles are scoped by default in <style> tags. "
            "Use :global() for unscoped styles."
        )
    
    # CSS framework guidance
    if result.has_tailwind:
        approaches.append(
            "Tailwind: Modify classes directly in JSX/HTML. "
            "For custom values, use arbitrary values like w-[200px] or "
            "extend theme in tailwind.config.js. "
            "Use @apply in CSS for reusable class combinations."
        )
    elif result.has_bootstrap:
        approaches.append(
            "Bootstrap: Use Bootstrap utility classes for quick fixes. "
            "Override in custom CSS with higher specificity. "
            "Check Bootstrap version for available classes."
        )
    
    # UI library guidance
    if result.has_shadcn:
        approaches.append(
            "shadcn/ui: Components are in /components/ui. "
            "Modify the component source directly or override with className. "
            "Theme colors defined in globals.css CSS variables."
        )
    elif result.has_material_ui:
        approaches.append(
            "Material UI: Use sx prop for inline styles or styled() API. "
            "Theme customization in ThemeProvider. "
            "Use MUI system props like m, p, display."
        )
    elif result.has_chakra_ui:
        approaches.append(
            "Chakra UI: Use style props directly on components. "
            "Theme in ChakraProvider. Supports responsive arrays."
        )
    
    return " ".join(approaches) if approaches else (
        "Standard CSS: Edit stylesheets directly. "
        "Use browser DevTools to identify the exact CSS rules to modify. "
        "Check for !important rules that might override changes."
    )


async def get_tech_stack_summary(page: Page) -> dict:
    """Get a simplified tech stack summary for API response."""
    result = await detect_tech_stack(page)
    
    return {
        "primary_framework": result.primary_framework,
        "meta_framework": result.meta_framework,
        "css_approach": result.css_approach,
        "ui_library": next((f.name for f in result.frameworks if f.category == "ui_library"), None),
        "frameworks": [
            {
                "name": f.name,
                "category": f.category,
                "confidence": f.confidence,
            }
            for f in result.frameworks
        ],
        "summary": result.summary,
        "fix_approach": result.fix_approach,
        "details": {
            "has_tailwind": result.has_tailwind,
            "has_bootstrap": result.has_bootstrap,
            "uses_css_modules": result.uses_css_modules,
            "uses_css_variables": result.uses_css_variables,
            "uses_inline_styles": result.uses_inline_styles,
        }
    }
