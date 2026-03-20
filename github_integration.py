#!/usr/bin/env python3
"""
GitHub Integration - Version Control Backup
Backs up validated changes to GitHub, creates branches for features
"""
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path("/workspace/project/clawbot")

class GitHubIntegration:
    def __init__(self):
        self.repo_path = PROJECT_DIR
        self.branch = "main"
        
    def run_git(self, args, capture=True):
        """Run a git command"""
        cmd = ["git"] + args
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=capture,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip() if capture else True
            else:
                print(f"Git error: {result.stderr}")
                return None
        except Exception as e:
            print(f"Git exception: {e}")
            return None
    
    def get_status(self):
        """Get git status"""
        return self.run_git(["status", "--porcelain"])
    
    def has_changes(self):
        """Check if there are uncommitted changes"""
        status = self.get_status()
        return bool(status)
    
    def get_changed_files(self):
        """Get list of changed files"""
        status = self.get_status()
        if not status:
            return []
        
        files = []
        for line in status.split("\n"):
            if line.strip():
                # Format: XY filename
                parts = line.strip().split()
                if len(parts) >= 2:
                    files.append(parts[1])
        return files
    
    def commit_changes(self, message=None):
        """Commit all changes with a message"""
        if not message:
            message = f"Auto-commit: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Add all files
        self.run_git(["add", "-A"], capture=False)
        
        # Check if there are changes to commit
        result = self.run_git(["status", "--porcelain"])
        if not result:
            print("No changes to commit")
            return False
        
        # Commit
        commit = self.run_git(["commit", "-m", message])
        if commit is not None:
            print(f"✅ Committed: {message}")
            return True
        return False
    
    def push(self):
        """Push to remote"""
        result = self.run_git(["push", "origin", self.branch])
        if result is not None:
            print("✅ Pushed to GitHub")
            return True
        return False
    
    def create_branch(self, branch_name):
        """Create a new branch"""
        result = self.run_git(["checkout", "-b", branch_name])
        if result is not None:
            print(f"✅ Created branch: {branch_name}")
            return True
        return False
    
    def switch_branch(self, branch_name):
        """Switch to existing branch"""
        result = self.run_git(["checkout", branch_name])
        if result is not None:
            print(f"✅ Switched to: {branch_name}")
            return True
        return False
    
    def get_recent_commits(self, count=5):
        """Get recent commit messages"""
        result = self.run_git([ "--no-pager", "log", f"-{count}", "--oneline"])
        if result:
            return result.split("\n")
        return []
    
    def backup(self, message=None):
        """Complete backup: commit and push"""
        if not self.has_changes():
            print("No changes to backup")
            return False
        
        if not message:
            message = f"Backup: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        if self.commit_changes(message):
            if self.push():
                print("✅ Full backup complete")
                return True
        
        return False
    
    def restore_file(self, file_path):
        """Restore a file to last committed state"""
        result = self.run_git(["checkout", "--", file_path])
        if result is not None:
            print(f"✅ Restored: {file_path}")
            return True
        return False
    
    def get_diff(self, file_path=None):
        """Get diff of changes"""
        if file_path:
            return self.run_git(["diff", file_path])
        return self.run_git(["diff"])
    
    def get_current_branch(self):
        """Get current branch name"""
        return self.run_git(["branch", "--show-current"])


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GitHub Integration")
    parser.add_argument("--status", action="store_true", help="Show git status")
    parser.add_argument("--backup", action="store_true", help="Commit and push all changes")
    parser.add_argument("--message", type=str, help="Commit message")
    parser.add_argument("--commits", action="store_true", help="Show recent commits")
    parser.add_argument("--files", action="store_true", help="Show changed files")
    
    args = parser.parse_args()
    
    github = GitHubIntegration()
    
    if args.status:
        print(f"Branch: {github.get_current_branch()}")
        print(f"Has changes: {github.has_changes()}")
        print(f"\n{github.get_status()}")
    
    elif args.backup:
        github.backup(args.message)
    
    elif args.commits:
        for commit in github.get_recent_commits():
            print(commit)
    
    elif args.files:
        for f in github.get_changed_files():
            print(f)
    
    else:
        print("GitHub Integration Tool")
        print("  --status    Show git status")
        print("  --backup    Commit and push all changes")
        print("  --commits   Show recent commits")
        print("  --files     Show changed files")


if __name__ == "__main__":
    main()
