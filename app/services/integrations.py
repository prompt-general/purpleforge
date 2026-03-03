import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Integration, IntegrationEvent, Ticket

logger = logging.getLogger(__name__)

class IntegrationService:
    """Service to manage security stack integrations.
    
    Supports:
    - Webhook dispatch (generic HTTP POST)
    - Ticket creation (Jira, ServiceNow, etc.)
    - SOAR trigger calls
    - SIEM log injection (via webhooks)
    """

    def create_integration(
        self,
        db: Session,
        name: str,
        integration_type: str,
        config: Dict[str, Any]
    ) -> Integration:
        """Register a new integration."""
        integration = Integration(
            name=name,
            integration_type=integration_type,
            config=config
        )
        db.add(integration)
        db.commit()
        db.refresh(integration)
        logger.info(f"Created integration: {name} ({integration_type})")
        return integration

    def dispatch_event(
        self,
        db: Session,
        integration_id: int,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> IntegrationEvent:
        """Send an event to an integration."""
        integration = db.query(Integration).filter(Integration.id == integration_id).first()
        if not integration:
            raise ValueError("Integration not found")
        
        if not integration.is_active:
            raise ValueError("Integration is inactive")
        
        success = False
        error_message = None
        
        try:
            if integration.integration_type == "webhook":
                success, error_message = self._dispatch_webhook(integration, event_type, payload)
            elif integration.integration_type in ["jira", "servicenow"]:
                success, error_message = self._create_ticket(db, integration, event_type, payload)
            elif integration.integration_type == "soar":
                success, error_message = self._trigger_soar(integration, event_type, payload)
            elif integration.integration_type == "splunk":
                success, error_message = self._send_splunk_event(integration, event_type, payload)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error dispatching event to {integration.name}: {error_message}")
        
        event = IntegrationEvent(
            integration_id=integration_id,
            event_type=event_type,
            payload=payload,
            success=success,
            error_message=error_message
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        
        return event

    def _dispatch_webhook(
        self,
        integration: Integration,
        event_type: str,
        payload: Dict[str, Any]
    ) -> tuple:
        """Send a POST request to a webhook URL."""
        url = integration.config.get("webhook_url")
        if not url:
            return False, "webhook_url not configured"
        
        headers = {
            "Content-Type": "application/json",
            "X-Event-Type": event_type
        }
        
        auth_header = integration.config.get("auth_header")
        if auth_header:
            headers["Authorization"] = auth_header
        
        body = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload or {}
        }
        
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(url, json=body, headers=headers)
                if response.status_code >= 200 and response.status_code < 300:
                    logger.info(f"Webhook dispatch successful: {response.status_code}")
                    return True, None
                else:
                    return False, f"HTTP {response.status_code}: {response.text[:100]}"
        except httpx.TimeoutException:
            return False, "Webhook timeout"
        except Exception as e:
            return False, str(e)

    def _create_ticket(
        self,
        db: Session,
        integration: Integration,
        event_type: str,
        payload: Dict[str, Any]
    ) -> tuple:
        """Create a ticket in Jira or ServiceNow."""
        # For now, we'll simulate ticket creation and persist locally.
        # In production, this would call Jira/ServiceNow APIs.
        
        mitre_id = payload.get("mitre_id") if payload else None
        title = payload.get("title", f"Security Alert: {event_type}") if payload else f"Security Alert: {event_type}"
        description = payload.get("description") if payload else None
        
        ticket = Ticket(
            integration_id=integration.id,
            title=title,
            description=description,
            mitre_id=mitre_id,
            ticket_type=event_type
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        # Simulate external ticket creation
        external_id = f"{integration.integration_type.upper()}-{ticket.id}"
        ticket.external_ticket_id = external_id
        db.commit()
        
        logger.info(f"Created ticket {external_id} in {integration.name}")
        return True, None

    def _trigger_soar(
        self,
        integration: Integration,
        event_type: str,
        payload: Dict[str, Any]
    ) -> tuple:
        """Trigger a SOAR playbook via webhook."""
        url = integration.config.get("webhook_url")
        if not url:
            return False, "webhook_url not configured for SOAR"
        
        body = {
            "event": event_type,
            "data": payload or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(url, json=body)
                if response.status_code >= 200 and response.status_code < 300:
                    logger.info(f"SOAR trigger successful: {response.status_code}")
                    return True, None
                else:
                    return False, f"SOAR trigger failed: {response.status_code}"
        except Exception as e:
            return False, str(e)

    def _send_splunk_event(
        self,
        integration: Integration,
        event_type: str,
        payload: Dict[str, Any]
    ) -> tuple:
        """Send an event to Splunk via HTTP Event Collector (HEC)."""
        hec_url = integration.config.get("webhook_url")
        hec_token = integration.config.get("api_key")
        
        if not hec_url or not hec_token:
            return False, "webhook_url and api_key required for Splunk"
        
        event_data = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload or {}
        }
        
        headers = {
            "Authorization": f"Splunk {hec_token}",
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client(timeout=10, verify=False) as client:  # verify=False for self-signed certs
                response = client.post(hec_url, json={"event": event_data}, headers=headers)
                if response.status_code >= 200 and response.status_code < 300:
                    logger.info(f"Splunk event sent successfully")
                    return True, None
                else:
                    return False, f"Splunk returned {response.status_code}"
        except Exception as e:
            return False, str(e)

    def broadcast_event(
        self,
        db: Session,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> List[IntegrationEvent]:
        """Broadcast an event to all active integrations."""
        integrations = db.query(Integration).filter(Integration.is_active == True).all()
        
        events = []
        for integration in integrations:
            try:
                event = self.dispatch_event(db, integration.id, event_type, payload)
                events.append(event)
            except Exception as e:
                logger.error(f"Error broadcasting to {integration.name}: {e}")
        
        return events

integration_service = IntegrationService()
