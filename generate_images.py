#!/usr/bin/python3
import os
import re
import asyncio
import aiohttp
from jinja2 import Environment, FileSystemLoader

from github_stats import Stats
from themes import THEMES

def spaceless(value):
    return re.sub(r'>\s+<', '><', value)

# Setup Jinja2 environment
env = Environment(loader=FileSystemLoader("templates"))
env.globals['enumerate'] = enumerate
env.filters['spaceless'] = spaceless
output_dir = os.getenv("BUILD_DIR", "output")

################################################################################
# Helper Functions

"""
"title_color": "ffffff",
"text_color": "ffffff",
"icon_color": "ffffff",
"bg_color": "35,4158d0,c850c0,ffcc70",
"""
ROOT_CSS = """
svg {
	--svg-bg: #fff;
	--svg-color: #24292E;
	--blue: rgb(3, 102, 214);
	--octicon-color: #586069;
}

svg#gh-dark-mode-only:target {
	--svg-bg: #0d1117;
	--svg-color: #c9d1d9;
	--blue: #58a6ff;
	--octicon-color: #8b949e;
}
"""
GRADIENT = """
<defs xmlns="http://www.w3.org/2000/svg">
    <linearGradient id="gradient" gradientTransform="rotate(35)" gradientUnits="userSpaceOnUse">
    <stop offset="0%" stop-color="#{}"/>,<stop offset="50%" stop-color="#{}"/>,<stop offset="100%" stop-color="#{}"/>
    </linearGradient>
</defs>
"""

def generate_output(template_name: str, context: dict) -> None:
    """
    Create the output folder if it does not already exist
    """
    if not os.path.isdir(output_dir): 
        os.mkdir(output_dir)
    theme = os.getenv('THEME', 'default')
    # Get light-theme
    light = THEMES.get(theme) or THEMES.get(f"{theme}-light")
    dark = THEMES.get(f"{theme}-dark") or THEMES.get("default-dark")
    
    base_css_file = os.getenv('BASE_CSS', 'statics/stats.min.css')
    with open(base_css_file, 'r') as css_file:
        base_css = css_file.read()
        context.update({'base_css': base_css})

    template = env.get_template(template_name)
    with open(os.path.join(output_dir, template_name), 'w') as f:
        f.write(template.render(context))


################################################################################
# Individual Image Generation Functions


async def generate_overview(s: Stats) -> None:
    """
    Generate an SVG badge with summary statistics
    :param s: Represents user's GitHub statistics
    """
    name = await s.name
    context = {
        "statistics_title": os.getenv("statistics_title", f"{ name }'s GitHub Statistics"),
        "stars": f"{await s.stargazers:,}",
        "forks": f"{await s.forks:,}",
        "contributions": f"{await s.total_contributions:,}",
        "lines_changed": f"{(await s.lines_changed)[0] + (await s.lines_changed)[1]:,}",
        "views": f"{await s.views:,}",
        "repos": f"{len(await s.repos):,}"
    }
    generate_output("overview.svg", context)
    


async def generate_languages(s: Stats) -> None:
    """
    Generate an SVG badge with summary languages used
    :param s: Represents user's GitHub statistics
    """
    sorted_languages = sorted(
        (await s.languages).items(), reverse=True, key=lambda t: t[1].get("size")
    )

    context = {
        "sorted_languages": [
            (lang, {"color": data.get("color"), "prop": data.get("prop", 0)})
            for lang, data in sorted_languages
        ],
        "lang_title": os.getenv("LANG_TITLE", "Languages Used (By File Size)")
    }
    
    generate_output("lang.svg", context)


################################################################################
# Main Function


async def main() -> None:
    """
    Generate all badges
    """
    access_token = os.getenv("GITHUB_TOKEN")
    if not access_token:
        raise Exception("A personal access token is required to proceed!")
    user = os.getenv("GITHUB_ACTOR")
    if user is None:
        raise RuntimeError("Environment variable GITHUB_ACTOR must be set.")
    exclude_repos = os.getenv("EXCLUDED")
    excluded_repos = (
        {x.strip() for x in exclude_repos.split(",")} if exclude_repos else None
    )
    exclude_langs = os.getenv("EXCLUDED_LANGS")
    excluded_langs = (
        {x.strip() for x in exclude_langs.split(",")} if exclude_langs else None
    )
    # Convert a truthy value to a Boolean
    raw_ignore_forked_repos = os.getenv("EXCLUDE_FORKED_REPOS")
    ignore_forked_repos = (
        not not raw_ignore_forked_repos
        and raw_ignore_forked_repos.strip().lower() != "false"
    )
    async with aiohttp.ClientSession() as session:
        if s := Stats(
            user,
            access_token,
            session,
            exclude_repos=excluded_repos,
            exclude_langs=excluded_langs,
            ignore_forked_repos=ignore_forked_repos,
        ):
            await asyncio.gather(generate_languages(s), generate_overview(s))
        else:
            raise Exception("Failed to generate stats.")


if __name__ == "__main__":
    asyncio.run(main())
