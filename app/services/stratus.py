import subprocess
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

class StratusWrapper:
    """Wrapper for Stratus Red Team CLI"""
    
    def __init__(self, binary_path: str = settings.STRATUS_BINARY_PATH):
        self.binary_path = binary_path

    def detonate(self, technique_id: str) -> Dict[str, Any]:
        """
        Executes 'stratus detonate <technique_id>' and returns metadata.
        """
        start_time = datetime.utcnow()
        try:
            # Command: stratus detonate aws.defense-evasion.cloudtrail-stop
            # Using list for safer subprocess execution
            cmd = [self.binary_path, "detonate", technique_id]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True # Raise if command fails
            )
            
            end_time = datetime.utcnow()
            return {
                "status": "COMPLETED",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds()
            }
        except subprocess.CalledProcessError as e:
            end_time = datetime.utcnow()
            logger.error(f"Stratus execution failed: {e.stderr}")
            return {
                "status": "FAILED",
                "stdout": e.stdout,
                "stderr": e.stderr,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds()
            }
        except Exception as e:
            end_time = datetime.utcnow()
            logger.error(f"Unexpected error in Stratus wrapper: {str(e)}")
            return {
                "status": "FAILED",
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }

    def warmup(self, technique_id: str) -> Dict[str, Any]:
        """Ensures the technique's infra is warm before detonation"""
        try:
            cmd = [self.binary_path, "warmup", technique_id]
            subprocess.run(cmd, check=True)
            return {"status": "WARMED"}
        except Exception as e:
            return {"status": "WARM_FAILED", "error": str(e)}

    def cleanup(self, technique_id: str) -> Dict[str, Any]:
        """Cleans up the technique's infra after detonation and returns metadata."""
        start_time = datetime.utcnow()
        try:
            cmd = [self.binary_path, "cleanup", technique_id]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            end_time = datetime.utcnow()
            return {
                "status": "CLEANED",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds()
            }
        except subprocess.CalledProcessError as e:
            end_time = datetime.utcnow()
            logger.error(f"Stratus cleanup failed: {e.stderr}")
            return {
                "status": "CLEANUP_FAILED",
                "stdout": e.stdout,
                "stderr": e.stderr,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds()
            }
        except Exception as e:
            end_time = datetime.utcnow()
            logger.error(f"Unexpected error in Stratus cleanup wrapper: {str(e)}")
            return {
                "status": "CLEANUP_FAILED",
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }

stratus_service = StratusWrapper()
