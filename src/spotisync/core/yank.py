import logging
import os
import subprocess
import sys

def check_and_setup_yank():
    """
    Check if Yank_src directory exists and download it if not present.
    """
    yank_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Yank_src")
    
    if os.path.exists(yank_dir):
        logging.debug("Yank_src directory already exists")
        return
    
    logging.info("Yank_src directory not found, downloading from GitHub...")
    try:
        # Check if git is installed
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        
        # Clone the repository
        subprocess.run(
            ["git", "clone", "https://github.com/Sabdot33/Yank_Configfile.git", "Yank_src"],
            check=True,
            cwd=os.path.dirname(yank_dir)
        )
        logging.info("Successfully downloaded Yank_src")
    except subprocess.CalledProcessError as e:
        error_msg = "Git is not installed or repository clone failed"
        logging.error(f"{error_msg}: {e}")
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = "Failed to download Yank_src"
        logging.error(f"{error_msg}: {e}")
        raise RuntimeError(error_msg)