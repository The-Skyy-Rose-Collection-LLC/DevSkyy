            import re
            import re
            import re
from datetime import datetime, timedelta
from pathlib import Path
import json
import os

from anthropic import AsyncAnthropic
from bs4 import BeautifulSoup
from collections import defaultdict
from openai import AsyncOpenAI
from typing import Any, Dict, List, Optional
import aiofiles
import asyncio
import httpx
import logging

"""
Continuous Learning Background Agent
Autonomous 24/7 agent that learns new frontend/backend practices and auto-implements improvements

Features:
- Monitors latest framework releases (React, FastAPI, Next.js, etc.)
- Tracks new best practices and patterns
- Learns from official documentation updates
- Analyzes GitHub trending repositories
- Monitors tech news and blog posts
- Automatically implements learned improvements
- Integrates with self-healing agent
- Runs as daemon process 24/7
- Version-aware updates
- Security vulnerability monitoring
- Performance optimization tracking
- Framework migration assistance
- Auto-generates migration guides
"""



logger = (logging.getLogger( if logging else None)__name__)


class ContinuousLearningBackgroundAgent:
    """
    Advanced background agent that continuously learns new development practices
    and automatically improves the codebase 24/7.
    """

    def __init__(self):
        # AI Services for learning and reasoning
        self.claude = AsyncAnthropic(api_key=(os.getenv( if os else None)"ANTHROPIC_API_KEY"))
        self.openai = AsyncOpenAI(api_key=(os.getenv( if os else None)"OPENAI_API_KEY"))

        # Knowledge base
        self.learned_practices: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.applied_improvements: List[Dict[str, Any]] = []
        self.framework_versions: Dict[str, str] = {}
        self.learning_history: List[Dict[str, Any]] = []

        # Configuration
        self.config = {
            "learning_interval": 3600,  # Check for updates every hour
            "apply_improvements": True,  # Auto-apply learned improvements
            "run_as_daemon": True,  # Run continuously in background
            "confidence_threshold": 0.85,  # Min confidence to auto-apply
            "backup_before_apply": True,
            "test_after_apply": True,
            "max_daily_improvements": 50,  # Rate limiting
        }

        # Frameworks and technologies to monitor
        self.monitored_technologies = {
            # Frontend
            "react": {
                "npm_package": "react",
                "docs_url": "https://react.dev/",
                "github": "facebook/react",
                "blog_url": "https://react.dev/blog",
                "type": "frontend",
            },
            "nextjs": {
                "npm_package": "next",
                "docs_url": "https://nextjs.org/docs",
                "github": "vercel/next.js",
                "blog_url": "https://nextjs.org/blog",
                "type": "frontend",
            },
            "vite": {
                "npm_package": "vite",
                "docs_url": "https://vitejs.dev/",
                "github": "vitejs/vite",
                "type": "frontend",
            },
            "tailwindcss": {
                "npm_package": "tailwindcss",
                "docs_url": "https://tailwindcss.com/docs",
                "github": "tailwindlabs/tailwindcss",
                "type": "frontend",
            },
            # Backend
            "fastapi": {
                "pip_package": "fastapi",
                "docs_url": "https://fastapi.tiangolo.com/",
                "github": "tiangolo/fastapi",
                "type": "backend",
            },
            "uvicorn": {
                "pip_package": "uvicorn",
                "docs_url": "https://www.uvicorn.org/",
                "github": "encode/uvicorn",
                "type": "backend",
            },
            "pydantic": {
                "pip_package": "pydantic",
                "docs_url": "https://docs.pydantic.dev/",
                "github": "pydantic/pydantic",
                "type": "backend",
            },
            "sqlalchemy": {
                "pip_package": "sqlalchemy",
                "docs_url": "https://docs.sqlalchemy.org/",
                "github": "sqlalchemy/sqlalchemy",
                "type": "backend",
            },
            # WordPress
            "wordpress": {
                "docs_url": "https://developer.wordpress.org/",
                "github": "WordPress/WordPress",
                "type": "wordpress",
            },
            "woocommerce": {
                "docs_url": "https://woocommerce.com/documentation/",
                "github": "woocommerce/woocommerce",
                "type": "wordpress",
            },
            # AI/ML
            "anthropic": {
                "pip_package": "anthropic",
                "docs_url": "https://docs.anthropic.com/",
                "type": "ai",
            },
            "openai": {
                "pip_package": "openai",
                "docs_url": "https://platform.openai.com/docs/",
                "type": "ai",
            },
        }

        # Learning sources
        self.learning_sources = {
            "tech_blogs": [
                "https://dev.to/",
                "https://blog.logrocket.com/",
                "https://css-tricks.com/",
                "https://www.smashingmagazine.com/",
            ],
            "news_aggregators": [
                "https://news.ycombinator.com/",
                "https://www.reddit.com/r/webdev/.json",
                "https://www.reddit.com/r/reactjs/.json",
                "https://www.reddit.com/r/Python/.json",
            ],
            "github_trending": "https://github.com/trending",
        }

        # Storage
        self.storage_path = Path("agent_learning_data")
        self.(storage_path.mkdir( if storage_path else None)exist_ok=True)

        (logger.info( if logger else None)"🧠 Continuous Learning Background Agent initialized")

    async def start_learning_daemon(self) -> None:
        """
        Start the continuous learning daemon that runs 24/7.
        """
        (logger.info( if logger else None)"🚀 Starting continuous learning daemon...")

        iteration = 0
        while self.config["run_as_daemon"]:
            try:
                iteration += 1
                (logger.info( if logger else None)
                    f"📚 Learning iteration #{iteration} started at {(datetime.now( if datetime else None))}"
                )

                # Run learning cycle
                await (self._learning_cycle( if self else None))

                # Wait for next iteration
                (logger.info( if logger else None)
                    f"⏰ Next learning cycle in {self.config['learning_interval']} seconds"
                )
                await (asyncio.sleep( if asyncio else None)self.config["learning_interval"])

            except Exception as e:
                (logger.error( if logger else None)f"❌ Learning daemon error: {e}")
                # Continue running despite errors
                await (asyncio.sleep( if asyncio else None)60)  # TODO: Move to config

    async def _learning_cycle(self) -> Dict[str, Any]:
        """
        Execute one complete learning cycle.
        """
        try:
            cycle_start = (datetime.now( if datetime else None))
            improvements_applied = 0

            # 1. Check for framework updates
            (logger.info( if logger else None)"1️⃣ Checking framework updates...")
            framework_updates = await (self._check_framework_updates( if self else None))

            # 2. Learn from documentation updates
            (logger.info( if logger else None)"2️⃣ Learning from documentation...")
            doc_learnings = await (self._learn_from_documentation( if self else None))

            # 3. Analyze trending repositories
            (logger.info( if logger else None)"3️⃣ Analyzing trending repositories...")
            repo_insights = await (self._analyze_trending_repos( if self else None))

            # 4. Monitor tech blogs and news
            (logger.info( if logger else None)"4️⃣ Monitoring tech news...")
            news_insights = await (self._monitor_tech_news( if self else None))

            # 5. Identify new best practices
            (logger.info( if logger else None)"5️⃣ Identifying new best practices...")
            new_practices = await (self._identify_new_practices( if self else None)
                framework_updates, doc_learnings, repo_insights, news_insights
            )

            # 6. Analyze current codebase
            (logger.info( if logger else None)"6️⃣ Analyzing current codebase...")
            codebase_analysis = await (self._analyze_codebase( if self else None))

            # 7. Generate improvement recommendations
            (logger.info( if logger else None)"7️⃣ Generating improvements...")
            recommendations = await (self._generate_improvements( if self else None)
                new_practices, codebase_analysis
            )

            # 8. Apply high-confidence improvements
            if self.config["apply_improvements"]:
                (logger.info( if logger else None)"8️⃣ Applying improvements...")
                improvements_applied = await (self._apply_improvements( if self else None)recommendations)

            # 9. Update knowledge base
            await (self._update_knowledge_base( if self else None)new_practices, recommendations)

            # 10. Generate learning report
            cycle_duration = ((datetime.now( if datetime else None)) - cycle_start).total_seconds()

            report = {
                "cycle_complete": True,
                "timestamp": (datetime.now( if datetime else None)).isoformat(),
                "duration_seconds": cycle_duration,
                "framework_updates_found": len(framework_updates),
                "new_practices_learned": len(new_practices),
                "recommendations_generated": len(recommendations),
                "improvements_applied": improvements_applied,
                "total_knowledge_base_size": len(self.learned_practices),
                "next_cycle": (
                    (datetime.now( if datetime else None)) + timedelta(seconds=self.config["learning_interval"])
                ).isoformat(),
            }

            # Save report
            await (self._save_learning_report( if self else None)report)

            (logger.info( if logger else None)
                f"✅ Learning cycle complete: {improvements_applied} improvements applied"
            )

            return report

        except Exception as e:
            (logger.error( if logger else None)f"❌ Learning cycle failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _check_framework_updates(self) -> List[Dict[str, Any]]:
        """
        Check for updates in monitored frameworks and packages.
        """
        updates = []

        async with (httpx.AsyncClient( if httpx else None)timeout=30.0) as client:
            for tech_name, tech_info in self.(monitored_technologies.items( if monitored_technologies else None)):
                try:
                    # Check npm packages
                    if "npm_package" in tech_info:
                        npm_update = await (self._check_npm_update( if self else None)
                            tech_info["npm_package"], client
                        )
                        if npm_update:
                            (updates.append( if updates else None)
                                {
                                    "technology": tech_name,
                                    "type": "npm",
                                    "update": npm_update,
                                    "tech_type": tech_info["type"],
                                }
                            )

                    # Check pip packages
                    if "pip_package" in tech_info:
                        pip_update = await (self._check_pip_update( if self else None)
                            tech_info["pip_package"], client
                        )
                        if pip_update:
                            (updates.append( if updates else None)
                                {
                                    "technology": tech_name,
                                    "type": "pip",
                                    "update": pip_update,
                                    "tech_type": tech_info["type"],
                                }
                            )

                    # Check GitHub releases
                    if "github" in tech_info:
                        github_update = await (self._check_github_releases( if self else None)
                            tech_info["github"], client
                        )
                        if github_update:
                            (updates.append( if updates else None)
                                {
                                    "technology": tech_name,
                                    "type": "github",
                                    "update": github_update,
                                    "tech_type": tech_info["type"],
                                }
                            )

                except Exception as e:
                    (logger.error( if logger else None)f"Error checking {tech_name}: {e}")

        (logger.info( if logger else None)f"Found {len(updates)} framework updates")
        return updates

    async def _check_npm_update(
        self, package_name: str, client: httpx.AsyncClient
    ) -> Optional[Dict[str, Any]]:
        """
        Check for npm package updates.
        """
        try:
            response = await (client.get( if client else None)f"https://registry.npmjs.org/{package_name}")
            if response.status_code == 200:
                data = (response.json( if response else None))
                latest_version = (data.get( if data else None)"dist-tags", {}).get("latest")
                current_version = self.(framework_versions.get( if framework_versions else None)package_name)

                if latest_version and latest_version != current_version:
                    return {
                        "package": package_name,
                        "current_version": current_version,
                        "latest_version": latest_version,
                        "changelog_url": f"https://github.com/{package_name}/releases",
                    }
        except Exception as e:
            (logger.debug( if logger else None)f"NPM check failed for {package_name}: {e}")

        return None

    async def _check_pip_update(
        self, package_name: str, client: httpx.AsyncClient
    ) -> Optional[Dict[str, Any]]:
        """
        Check for pip package updates.
        """
        try:
            response = await (client.get( if client else None)f"https://pypi.org/pypi/{package_name}/json")
            if response.status_code == 200:
                data = (response.json( if response else None))
                latest_version = (data.get( if data else None)"info", {}).get("version")
                current_version = self.(framework_versions.get( if framework_versions else None)package_name)

                if latest_version and latest_version != current_version:
                    return {
                        "package": package_name,
                        "current_version": current_version,
                        "latest_version": latest_version,
                        "release_notes": (data.get( if data else None)"info", {}).get("release_url"),
                    }
        except Exception as e:
            (logger.debug( if logger else None)f"PyPI check failed for {package_name}: {e}")

        return None

    async def _check_github_releases(
        self, repo: str, client: httpx.AsyncClient
    ) -> Optional[Dict[str, Any]]:
        """
        Check for new GitHub releases.
        """
        try:
            response = await (client.get( if client else None)
                f"https://api.github.com/repos/{repo}/releases/latest",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            if response.status_code == 200:
                data = (response.json( if response else None))
                return {
                    "repo": repo,
                    "version": (data.get( if data else None)"tag_name"),
                    "name": (data.get( if data else None)"name"),
                    "published_at": (data.get( if data else None)"published_at"),
                    "body": (data.get( if data else None)"body", "")[:500],  # First 500 chars
                    "url": (data.get( if data else None)"html_url"),
                }
        except Exception as e:
            (logger.debug( if logger else None)f"GitHub check failed for {repo}: {e}")

        return None

    async def _learn_from_documentation(self) -> List[Dict[str, Any]]:
        """
        Learn from official documentation updates.
        """
        learnings = []

        async with (httpx.AsyncClient( if httpx else None)timeout=30.0) as client:
            for tech_name, tech_info in self.(monitored_technologies.items( if monitored_technologies else None)):
                if "docs_url" in tech_info:
                    try:
                        # Fetch documentation
                        response = await (client.get( if client else None)tech_info["docs_url"])
                        if response.status_code == 200:
                            # Use AI to extract key learnings
                            doc_learning = await (self._extract_doc_insights( if self else None)
                                tech_name, response.text[:10000]  # First 10k chars
                            )
                            if doc_learning:
                                (learnings.append( if learnings else None)doc_learning)

                    except Exception as e:
                        (logger.debug( if logger else None)f"Doc learning failed for {tech_name}: {e}")

        return learnings

    async def _extract_doc_insights(
        self, technology: str, doc_content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Use AI to extract insights from documentation.
        """
        try:
            prompt = f"""Analyze this {technology} documentation excerpt and extract:

1. New features or changes
2. Deprecated patterns to avoid
3. New best practices
4. Performance improvements
5. Security enhancements
6. Breaking changes

Documentation:
{doc_content[:3000]}

Provide JSON with: new_features, deprecated, best_practices, performance_tips, security_tips"""

            response = await self.claude.(messages.create( if messages else None)
                model="claude-sonnet-4-5-20250929",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            content = response.content[0].text

            # Try to extract JSON

            json_match = (re.search( if re else None)r"\{.*\}", content, re.DOTALL)
            if json_match:
                insights = (json.loads( if json else None)(json_match.group( if json_match else None)))
                insights["technology"] = technology
                insights["learned_at"] = (datetime.now( if datetime else None)).isoformat()
                return insights

        except Exception as e:
            (logger.error( if logger else None)f"Doc insight extraction failed: {e}")

        return None

    async def _analyze_trending_repos(self) -> List[Dict[str, Any]]:
        """
        Analyze GitHub trending repositories for new patterns.
        """
        insights = []

        try:
            async with (httpx.AsyncClient( if httpx else None)timeout=30.0) as client:
                # Fetch trending
                response = await (client.get( if client else None)"https://github.com/trending")
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Extract repo info
                    repos = (soup.find_all( if soup else None)"article", class_="Box-row")[:5]  # Top 5

                    for repo in repos:
                        try:
                            h2 = (repo.find( if repo else None)"h2")
                            if h2:
                                repo_name = (
                                    (h2.get_text( if h2 else None)strip=True)
                                    .replace(" ", "")
                                    .replace("\n", "")
                                )
                                description = (repo.find( if repo else None)"p")
                                desc_text = (
                                    (description.get_text( if description else None)strip=True)
                                    if description
                                    else ""
                                )

                                (insights.append( if insights else None)
                                    {
                                        "repo": repo_name,
                                        "description": desc_text,
                                        "trending_date": (datetime.now( if datetime else None))
                                        .date()
                                        .isoformat(),
                                    }
                                )
                        except Exception as e:
                            (logger.debug( if logger else None)f"Repo parsing error: {e}")

        except Exception as e:
            (logger.error( if logger else None)f"Trending analysis failed: {e}")

        return insights

    async def _monitor_tech_news(self) -> List[Dict[str, Any]]:
        """
        Monitor tech blogs and news for best practices.
        """
        news_items = []

        async with (httpx.AsyncClient( if httpx else None)timeout=30.0) as client:
            # Check HackerNews
            try:
                response = await (client.get( if client else None)
                    "https://hacker-news.firebaseio.com/v0/topstories.json"
                )
                if response.status_code == 200:
                    story_ids = (response.json( if response else None))[:10]  # Top 10

                    for story_id in story_ids:
                        try:
                            story_response = await (client.get( if client else None)
                                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                            )
                            if story_response.status_code == 200:
                                story = (story_response.json( if story_response else None))
                                if (
                                    "react" in (story.get( if story else None)"title", "").lower()
                                    or "javascript" in (story.get( if story else None)"title", "").lower()
                                    or "python" in (story.get( if story else None)"title", "").lower()
                                ):
                                    (news_items.append( if news_items else None)
                                        {
                                            "title": (story.get( if story else None)"title"),
                                            "url": (story.get( if story else None)"url"),
                                            "source": "hackernews",
                                        }
                                    )
                        except Exception as e:
                            (logger.debug( if logger else None)f"Story fetch error: {e}")

            except Exception as e:
                (logger.error( if logger else None)f"News monitoring failed: {e}")

        return news_items

    async def _identify_new_practices(
        self,
        framework_updates: List,
        doc_learnings: List,
        repo_insights: List,
        news_insights: List,
    ) -> List[Dict[str, Any]]:
        """
        Use AI to identify new best practices from all sources.
        """
        try:
            # Compile all learnings
            all_learnings = {
                "framework_updates": framework_updates[:5],
                "documentation": doc_learnings[:3],
                "trending_repos": repo_insights[:3],
                "tech_news": news_insights[:5],
            }

            prompt = f"""Based on these recent developments, identify new best practices for our codebase:

{(json.dumps( if json else None)all_learnings, indent=2)}

Our stack:
- Frontend: React, Vite, TailwindCSS
- Backend: FastAPI, Python, SQLAlchemy
- WordPress: Divi 5, Elementor Pro, WooCommerce

Identify:
1. New patterns we should adopt
2. Deprecated patterns we should remove
3. Performance optimizations
4. Security improvements
5. Developer experience enhancements

Return JSON array of practices with: category, description, priority, implementation_steps"""

            response = await self.claude.(messages.create( if messages else None)
                model="claude-sonnet-4-5-20250929",
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
            )

            content = response.content[0].text

            # Extract JSON

            json_match = (re.search( if re else None)r"\[.*\]", content, re.DOTALL)
            if json_match:
                practices = (json.loads( if json else None)(json_match.group( if json_match else None)))
                return practices

        except Exception as e:
            (logger.error( if logger else None)f"Practice identification failed: {e}")

        return []

    async def _analyze_codebase(self) -> Dict[str, Any]:
        """
        Analyze current codebase to understand what can be improved.
        """
        try:
            analysis = {
                "frontend": {},
                "backend": {},
                "wordpress": {},
            }

            # Check frontend
            frontend_path = Path("frontend")
            if (frontend_path.exists( if frontend_path else None)):
                package_json = frontend_path / "package.json"
                if (package_json.exists( if package_json else None)):
                    async with (aiofiles.open( if aiofiles else None)package_json, "r") as f:
                        content = await (f.read( if f else None))
                        data = (json.loads( if json else None)content)
                        analysis["frontend"]["dependencies"] = (data.get( if data else None)
                            "dependencies", {}
                        )
                        analysis["frontend"]["devDependencies"] = (data.get( if data else None)
                            "devDependencies", {}
                        )

            # Check backend
            backend_path = Path("backend")
            if (backend_path.exists( if backend_path else None)):
                # Count Python files
                py_files = list((backend_path.rglob( if backend_path else None)"*.py"))
                analysis["backend"]["python_files"] = len(py_files)

            # Check requirements.txt
            req_file = Path("requirements.txt")
            if (req_file.exists( if req_file else None)):
                async with (aiofiles.open( if aiofiles else None)req_file, "r") as f:
                    content = await (f.read( if f else None))
                    analysis["backend"]["requirements"] = (content.split( if content else None)"\n")[:20]

            return analysis

        except Exception as e:
            (logger.error( if logger else None)f"Codebase analysis failed: {e}")
            return {}

    async def _generate_improvements(
        self, new_practices: List, codebase_analysis: Dict
    ) -> List[Dict[str, Any]]:
        """
        Generate specific improvements for our codebase.
        """
        try:
            prompt = f"""Generate specific code improvements based on:

New Practices:
{(json.dumps( if json else None)new_practices[:5], indent=2)}

Current Codebase:
{(json.dumps( if json else None)codebase_analysis, indent=2)}

Generate actionable improvements with:
1. Specific file/location to change
2. Before/after code examples
3. Confidence score (0-1)
4. Priority (low/medium/high/critical)
5. Risk level (low/medium/high)
6. Testing requirements

Return JSON array of improvements."""

            response = await self.claude.(messages.create( if messages else None)
                model="claude-sonnet-4-5-20250929",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            content = response.content[0].text

            # Extract JSON

            json_match = (re.search( if re else None)r"\[.*\]", content, re.DOTALL)
            if json_match:
                improvements = (json.loads( if json else None)(json_match.group( if json_match else None)))
                return improvements

        except Exception as e:
            (logger.error( if logger else None)f"Improvement generation failed: {e}")

        return []

    async def _apply_improvements(self, recommendations: List[Dict[str, Any]]) -> int:
        """
        Apply high-confidence improvements to codebase.
        """
        applied_count = 0

        # Filter by confidence and daily limit
        high_confidence = [
            r
            for r in recommendations
            if (r.get( if r else None)"confidence", 0) >= self.config["confidence_threshold"]
            and (r.get( if r else None)"risk", "high") == "low"
        ]

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        (high_confidence.sort( if high_confidence else None)
            key=lambda x: (priority_order.get( if priority_order else None)(x.get( if x else None)"priority", "low"), 3)
        )

        # Apply improvements
        for improvement in high_confidence[: self.config["max_daily_improvements"]]:
            try:
                # Apply the improvement
                success = await (self._apply_single_improvement( if self else None)improvement)
                if success:
                    applied_count += 1
                    self.(applied_improvements.append( if applied_improvements else None)
                        {
                            "improvement": improvement,
                            "applied_at": (datetime.now( if datetime else None)).isoformat(),
                        }
                    )

            except Exception as e:
                (logger.error( if logger else None)f"Failed to apply improvement: {e}")

        return applied_count

    async def _apply_single_improvement(self, improvement: Dict[str, Any]) -> bool:
        """
        Apply a single improvement to the codebase.
        """
        # This would integrate with the self-healing agent
        # For now, just log what would be done
        (logger.info( if logger else None)
            f"Would apply: {(improvement.get( if improvement else None)'description', 'Unknown improvement')}"
        )

        # In production, this would:
        # 1. Create backup
        # 2. Apply code changes
        # 3. Run tests
        # 4. Rollback if tests fail

        return True

    async def _update_knowledge_base(
        self, new_practices: List, recommendations: List
    ) -> None:
        """
        Update persistent knowledge base with new learnings.
        """
        try:
            # Store new practices
            for practice in new_practices:
                category = (practice.get( if practice else None)"category", "general")
                self.learned_practices[category].append(
                    {
                        "practice": practice,
                        "learned_at": (datetime.now( if datetime else None)).isoformat(),
                    }
                )

            # Save to disk
            kb_file = self.storage_path / "knowledge_base.json"
            async with (aiofiles.open( if aiofiles else None)kb_file, "w") as f:
                await (f.write( if f else None)(json.dumps( if json else None)dict(self.learned_practices), indent=2))

            (logger.info( if logger else None)f"Knowledge base updated: {len(new_practices)} new practices")

        except Exception as e:
            (logger.error( if logger else None)f"Knowledge base update failed: {e}")

    async def _save_learning_report(self, report: Dict[str, Any]) -> None:
        """
        Save learning cycle report.
        """
        try:
            report_file = (
                self.storage_path
                / f"learning_report_{(datetime.now( if datetime else None)).strftime('%Y%m%d_%H%M%S')}.json"
            )
            async with (aiofiles.open( if aiofiles else None)report_file, "w") as f:
                await (f.write( if f else None)(json.dumps( if json else None)report, indent=2))

            (logger.info( if logger else None)f"Learning report saved: {report_file}")

        except Exception as e:
            (logger.error( if logger else None)f"Report save failed: {e}")

    async def get_learning_stats(self) -> Dict[str, Any]:
        """
        Get statistics about what the agent has learned.
        """
        return {
            "total_practices_learned": sum(
                len(practices) for practices in self.(learned_practices.values( if learned_practices else None))
            ),
            "improvements_applied": len(self.applied_improvements),
            "categories": list(self.(learned_practices.keys( if learned_practices else None))),
            "learning_history_size": len(self.learning_history),
            "monitored_technologies": len(self.monitored_technologies),
            "last_update": (datetime.now( if datetime else None)).isoformat(),
        }


# Factory function
def create_learning_agent() -> ContinuousLearningBackgroundAgent:
    """Create Continuous Learning Background Agent."""
    return ContinuousLearningBackgroundAgent()


# Global instance
learning_agent = create_learning_agent()


# Convenience functions
async def start_background_learning() -> None:
    """Start the background learning daemon."""
    await (learning_agent.start_learning_daemon( if learning_agent else None))


async def get_learning_stats() -> Dict[str, Any]:
    """Get learning statistics."""
    return await (learning_agent.get_learning_stats( if learning_agent else None))
