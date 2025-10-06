"""
WARPCORE GitHub Discovery System
Infer contexts from git repo topics and codeowner identity
"""

import asyncio
import subprocess
import json
import os
from typing import Dict, Any, List, Optional

class GitHubDiscovery:
    """Discover contexts from GitHub repos and topics"""
    
    def __init__(self):
        self.current_user = None
        self.repos = []
        self.topics = set()
        self.contexts = {}
    
    async def discover_contexts(self) -> Dict[str, Any]:
        """Discover operational contexts from git and GitHub"""
        
        # Get current user identity
        self.current_user = await self._get_current_git_user()
        
        # Get associated repositories
        repos = await self._discover_user_repositories()
        
        # Extract topics from repositories
        all_topics = await self._extract_topics_from_repos(repos)
        
        # Infer operational contexts from topics
        contexts = self._infer_contexts_from_topics(all_topics)
        
        return {
            "user": self.current_user,
            "repositories": len(repos),
            "topics": list(all_topics),
            "inferred_contexts": contexts
        }
    
    async def _get_current_git_user(self) -> Dict[str, str]:
        """Get current git user identity"""
        try:
            # Get git user email
            email_result = await self._run_command(["git", "config", "user.email"])
            email = email_result.get("stdout", "").strip()
            
            # Get git user name
            name_result = await self._run_command(["git", "config", "user.name"])
            name = name_result.get("stdout", "").strip()
            
            return {
                "email": email,
                "name": name,
                "username": email.split("@")[0] if email else "unknown"
            }
        except Exception:
            return {"email": "unknown", "name": "unknown", "username": "unknown"}
    
    async def _discover_user_repositories(self) -> List[Dict[str, Any]]:
        """Discover repositories associated with current user"""
        repos = []
        
        try:
            # Try to use gh CLI if available
            gh_result = await self._run_command(["gh", "repo", "list", "--json", "name,owner,topics", "--limit", "100"])
            
            if gh_result.get("exit_code") == 0:
                repos_data = json.loads(gh_result.get("stdout", "[]"))
                for repo in repos_data:
                    repos.append({
                        "name": repo.get("name"),
                        "owner": repo.get("owner", {}).get("login"),
                        "topics": repo.get("topics", [])
                    })
            
        except Exception:
            pass
        
        # Fallback: get current repo info
        if not repos:
            current_repo = await self._get_current_repository_info()
            if current_repo:
                repos.append(current_repo)
        
        return repos
    
    async def _get_current_repository_info(self) -> Optional[Dict[str, Any]]:
        """Get information about current git repository"""
        try:
            # Get remote origin URL
            remote_result = await self._run_command(["git", "remote", "get-url", "origin"])
            if remote_result.get("exit_code") != 0:
                return None
            
            remote_url = remote_result.get("stdout", "").strip()
            
            # Parse repository name from URL
            if "github.com" in remote_url:
                # Extract owner/repo from URL
                if remote_url.endswith(".git"):
                    remote_url = remote_url[:-4]
                
                parts = remote_url.split("/")
                if len(parts) >= 2:
                    owner = parts[-2].split(":")[-1] if ":" in parts[-2] else parts[-2]
                    repo_name = parts[-1]
                    
                    return {
                        "name": repo_name,
                        "owner": owner,
                        "topics": await self._get_repo_topics_from_readme()
                    }
            
            return None
            
        except Exception:
            return None
    
    async def _get_repo_topics_from_readme(self) -> List[str]:
        """Extract topics/keywords from README files"""
        topics = []
        
        readme_files = ["README.md", "readme.md", "README.txt", "README"]
        
        for readme_file in readme_files:
            if os.path.exists(readme_file):
                try:
                    with open(readme_file, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        
                    # Look for common technology keywords
                    keywords = [
                        "kubernetes", "k8s", "docker", "terraform", "ansible",
                        "aws", "gcp", "azure", "cloud", "microservices",
                        "production", "staging", "development", "testing",
                        "monitoring", "logging", "observability", "devops",
                        "ci/cd", "jenkins", "github-actions", "gitlab-ci"
                    ]
                    
                    for keyword in keywords:
                        if keyword in content:
                            topics.append(keyword)
                    
                    break
                    
                except Exception:
                    continue
        
        return topics
    
    async def _extract_topics_from_repos(self, repos: List[Dict[str, Any]]) -> set:
        """Extract all topics from discovered repositories"""
        all_topics = set()
        
        for repo in repos:
            topics = repo.get("topics", [])
            all_topics.update(topics)
        
        return all_topics
    
    def _infer_contexts_from_topics(self, topics: set) -> Dict[str, Any]:
        """Infer operational contexts from repository topics"""
        
        contexts = {
            "environments": [],
            "technologies": [],
            "deployment_targets": [],
            "practices": []
        }
        
        # Map topics to context categories
        topic_mapping = {
            "environments": ["production", "staging", "development", "dev", "prod", "stage", "test"],
            "technologies": ["kubernetes", "k8s", "docker", "terraform", "ansible", "aws", "gcp", "azure"],
            "deployment_targets": ["cloud", "on-premise", "hybrid", "multi-cloud"],
            "practices": ["devops", "ci-cd", "monitoring", "logging", "observability", "microservices"]
        }
        
        for category, keywords in topic_mapping.items():
            for topic in topics:
                if topic.lower() in keywords:
                    contexts[category].append(topic)
        
        # Infer specific contexts
        contexts["has_production"] = any("prod" in env.lower() for env in contexts["environments"])
        contexts["is_cloud_native"] = bool(set(contexts["technologies"]) & {"kubernetes", "k8s", "docker"})
        contexts["multi_cloud"] = len([tech for tech in contexts["technologies"] if tech in ["aws", "gcp", "azure"]]) > 1
        
        return contexts
    
    async def _run_command(self, command: List[str]) -> Dict[str, Any]:
        """Run shell command and return result"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            }