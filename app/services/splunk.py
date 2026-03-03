import splunklib.client as client
import splunklib.results as results
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

class SplunkClient:
    def __init__(self):
        self.host = settings.SPLUNK_HOST
        self.port = settings.SPLUNK_PORT
        self.username = settings.SPLUNK_USERNAME
        self.password = settings.SPLUNK_PASSWORD
        self.app = settings.SPLUNK_APP
        
    def _connect(self):
        # Allow connecting with insecure SSL for local dummy setups
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # When integrating with local splunk, often need to ignore SSL
        from splunklib.client import connect
        try:
            # Attempt to connect normally first
            return connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                app=self.app,
                autologin=True
            )
        except Exception as e:
            logger.warning(f"Normal Splunk connection failed ({str(e)}), trying without SSL verification...")
            import splunklib.binding as binding
            config = {
                "host": self.host,
                "port": self.port,
                "username": self.username,
                "password": self.password,
                "app": self.app,
                "scheme": "https",
                "verify": False
            }
            context = binding.Context(**config)
            context._http.disable_ssl_certificate_validation = True
            context.login()
            return client.Service(context=context)


    def search(self, spl_query: str, start_time: datetime, end_time: datetime, padding_minutes: int = 5) -> Dict[str, Any]:
        """
        Executes a Splunk search between start and end time with padding.
        """
        try:
            # Add padding to allow for logging delays
            earliest_time = (start_time - timedelta(minutes=padding_minutes)).isoformat()
            latest_time = (end_time + timedelta(minutes=padding_minutes)).isoformat()
            
            # Splunk SDK requires searches to start with 'search ' usually, but user rules might already have it.
            if not spl_query.strip().startswith("search") and not spl_query.strip().startswith("|"):
                spl_query = "search " + spl_query
                
            service = self._connect()
            
            kwargs_oneshot = {
                "earliest_time": earliest_time,
                "latest_time": latest_time,
                "output_mode": "json"
            }
            
            logger.info(f"Executing Splunk query: {spl_query} from {earliest_time} to {latest_time}")
            
            import json
            oneshotsearch_results = service.jobs.oneshot(spl_query, **kwargs_oneshot)
            reader = results.JSONResultsReader(oneshotsearch_results)
            
            events = []
            for result in reader:
                if isinstance(result, dict):
                    events.append(result)
            
            return {
                "status": "SUCCESS",
                "events": events,
                "count": len(events)
            }
        except Exception as e:
            logger.error(f"Splunk query failed: {str(e)}")
            return {
                "status": "ERROR",
                "error": str(e),
                "events": [],
                "count": 0
            }

splunk_service = SplunkClient()
