"""
main.py
--------
Entry point for the RemoteOK Ethical Web Scraping Project.

Pipeline: scrape -> clean in memory -> save CSV -> visualize (matplotlib/Tableau)

Run:
    python main.py
"""

from gui import launch_app

if __name__ == "__main__":
    launch_app()
