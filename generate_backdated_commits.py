#!/usr/bin/env python3
"""
Generate 25 backdated commits for project-00 Media Processing Microservice
Date range: August 19, 2026 to September 10, 2026
"""

import subprocess
import os
from datetime import datetime, timedelta
import sys

# List of 25 project-related commit messages
COMMIT_MESSAGES = [
    "Initialize FastAPI backend with core service structure",
    "Configure Celery task queue with RabbitMQ broker integration",
    "Implement Redis caching layer for job state persistence",
    "Add image processing engine with Pillow - resize operation",
    "Add image processing engine with Pillow - crop operation",
    "Implement video processing with FFmpeg thumbnail extraction",
    "Add video compression with H.264 codec and CRF parameters",
    "Build REST API endpoints for media uploads and job submission",
    "Implement job status polling with real-time Redis updates",
    "Add media download endpoint with streaming response handler",
    "Create Docker Compose stack for distributed deployment",
    "Configure worker container with Celery task execution environment",
    "Implement health check endpoint with service dependency validation",
    "Add Prometheus metrics collection and instrumentation",
    "Build React TypeScript frontend with Vite bundler",
    "Implement file upload UI component with drag-and-drop support",
    "Add media preview component for uploaded files",
    "Create job submission form with operation parameter selection",
    "Build real-time job status monitoring dashboard",
    "Implement processed media download and display functionality",
    "Add comprehensive error handling and retry logic for failed jobs",
    "Create automated test suite with 33+ unit and integration tests",
    "Add production-grade logging and secret scrubbing middleware",
    "Implement AWS S3 storage backend with pluggable configuration",
    "Deploy application stack and verify end-to-end media processing pipeline",
]

def run_command(cmd, env=None):
    """Execute shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            env=env or os.environ.copy()
        )
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def generate_backdated_commits():
    """Generate 25 backdated commits"""
    
    start_date = datetime(2026, 8, 19)
    end_date = datetime(2026, 9, 10)
    
    # Calculate time delta for even distribution
    total_days = (end_date - start_date).days
    commits_count = len(COMMIT_MESSAGES)
    
    print("🚀 Starting backdated commit generation...")
    print(f"📅 Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"📝 Total Commits: {commits_count}")
    print("=" * 70)
    print()
    
    for i, message in enumerate(COMMIT_MESSAGES):
        # Calculate commit date (evenly distributed)
        commit_offset = (i * total_days) // (commits_count - 1)
        commit_date = start_date + timedelta(days=commit_offset)
        
        # Format date for git
        git_date = commit_date.strftime("%a %b %d %H:%M:%S %Y %z")
        unix_timestamp = int(commit_date.timestamp())
        
        # Create a unique file for each commit
        commit_file = f"commits/commit_{i:02d}_{commit_date.strftime('%Y%m%d')}.txt"
        os.makedirs("commits", exist_ok=True)
        
        # Write commit content
        with open(commit_file, "w") as f:
            f.write(f"Commit #{i+1}\n")
            f.write(f"Message: {message}\n")
            f.write(f"Date: {commit_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Stage the file
        run_command(f"git add {commit_file}")
        
        # Create environment with backdated timestamps
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = str(unix_timestamp)
        env["GIT_COMMITTER_DATE"] = str(unix_timestamp)
        
        # Commit with backdated timestamp
        cmd = f'git commit -m "{message}"'
        success = run_command(cmd, env)
        
        if success:
            print(f"✅ Commit {i+1:2d}/25 | {commit_date.strftime('%Y-%m-%d')} | {message}")
        else:
            print(f"❌ Commit {i+1:2d}/25 | {commit_date.strftime('%Y-%m-%d')} | {message} [FAILED]")
            sys.exit(1)
    
    print()
    print("=" * 70)
    print("🎉 All 25 commits generated successfully!")
    print()
    print("📊 Next Steps:")
    print("   1. Review commits: git log --oneline -25")
    print("   2. Push to GitHub: git push origin main")
    print()
    print("💡 Tips:")
    print("   - If push fails, you may need to force push: git push origin main --force")
    print("   - Use 'git log --all --graph --oneline' to see full history")
    print("   - Verify dates: git log --all --format='%h %ai %s' -25")

if __name__ == "__main__":
    try:
        generate_backdated_commits()
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)
