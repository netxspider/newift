"""
Newift Native Scheduler Daemon
Runs Pipeline A every 6 hours and Pipeline B daily, or on customizable intervals.
"""
import time
import signal
import sys
from datetime import datetime, timezone
from pipeline.orchestrator import NewiftOrchestrator
from pipeline.config import settings

running = True


def handle_shutdown(signum, frame):
    global running
    print("\n🛑 Received termination signal. Shutting down Newift scheduler gracefully...")
    running = False


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


def run_scheduler(
    discovery_interval_hours: int = 6,
    publish_interval_hours: int = 24,
    dry_run: bool = False,
):
    orchestrator = NewiftOrchestrator()
    print("===================================================================")
    print("  Newift Automated News Daemon Scheduler Started")
    print(f"  • Pipeline A (Discovery & Clustering): Every {discovery_interval_hours} hours")
    print(f"  • Pipeline B (Editorial & Publishing): Every {publish_interval_hours} hours")
    print(f"  • Dry Run: {dry_run}")
    print("===================================================================\n")

    last_discovery = 0.0
    last_publish = 0.0

    discovery_interval_sec = discovery_interval_hours * 3600
    publish_interval_sec = publish_interval_hours * 3600

    while running:
        now = time.time()

        # Run discovery if due
        if now - last_discovery >= discovery_interval_sec:
            print(f"⏰ [{datetime.now(timezone.utc).isoformat()}] Triggering scheduled Pipeline A...")
            try:
                orchestrator.run_pipeline_a(save_to_db=True)
                last_discovery = now
            except Exception as e:
                print(f"❌ Error during scheduled discovery: {e}")

        # Run publishing if due
        if now - last_publish >= publish_interval_sec:
            print(f"⏰ [{datetime.now(timezone.utc).isoformat()}] Triggering scheduled Pipeline B...")
            try:
                orchestrator.run_daily_pipeline(max_stories=settings.max_stories_per_run, dry_run=dry_run)
                last_publish = now
            except Exception as e:
                print(f"❌ Error during scheduled publishing: {e}")

        # Sleep in 10-second increments to remain responsive to SIGINT
        for _ in range(6):
            if not running:
                break
            time.sleep(10)

    print("Newift scheduler stopped.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Newift Automation Scheduler")
    parser.add_argument("--discovery-hours", type=int, default=6, help="Hours between trend discovery runs")
    parser.add_argument("--publish-hours", type=int, default=24, help="Hours between editorial publishing runs")
    parser.add_argument("--dry-run", action="store_true", help="Run without mutating Sanity")
    args = parser.parse_args()

    run_scheduler(
        discovery_interval_hours=args.discovery_hours,
        publish_interval_hours=args.publish_hours,
        dry_run=args.dry_run,
    )
