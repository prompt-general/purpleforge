from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Integration, Ticket
from app.services.integrations import integration_service
from app.schemas.schemas import (
    IntegrationCreate, IntegrationResponse,
    IntegrationEventResponse,
    TicketCreate, TicketResponse,
    TriggerIntegrationRequest
)

router = APIRouter()

# --- Integration management endpoints ---
@router.post("/integrations", response_model=IntegrationResponse, status_code=201)
def create_integration(
    *,
    db: Session = Depends(get_db),
    integration_in: IntegrationCreate
) -> Any:
    """Register a new security stack integration (webhook, Jira, ServiceNow, SOAR, Splunk, etc.)."""
    integration = integration_service.create_integration(
        db,
        integration_in.name,
        integration_in.integration_type,
        integration_in.config
    )
    return integration

@router.get("/integrations", response_model=List[IntegrationResponse])
def list_integrations(db: Session = Depends(get_db)) -> Any:
    """List all registered integrations."""
    integrations = db.query(Integration).all()
    return integrations

@router.get("/integrations/{integration_id}", response_model=IntegrationResponse)
def get_integration(integration_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a specific integration by ID."""
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration

@router.patch("/integrations/{integration_id}", response_model=IntegrationResponse)
def toggle_integration(integration_id: int, is_active: bool, db: Session = Depends(get_db)) -> Any:
    """Enable or disable an integration."""
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integration.is_active = is_active
    db.commit()
    db.refresh(integration)
    return integration

# --- Event dispatch endpoints ---
@router.post("/integrations/{integration_id}/dispatch", response_model=IntegrationEventResponse, status_code=201)
def dispatch_to_integration(
    integration_id: int,
    *,
    db: Session = Depends(get_db),
    request: TriggerIntegrationRequest
) -> Any:
    """Send an event to a specific integration."""
    try:
        event = integration_service.dispatch_event(
            db,
            integration_id,
            request.event_type,
            request.payload
        )
        return event
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/integrations/broadcast", response_model=List[IntegrationEventResponse], status_code=201)
def broadcast_event(
    *,
    db: Session = Depends(get_db),
    request: TriggerIntegrationRequest
) -> Any:
    """Broadcast an event to all active integrations."""
    events = integration_service.broadcast_event(
        db,
        request.event_type,
        request.payload
    )
    return events

# --- Ticket management endpoints ---
@router.post("/integrations/{integration_id}/tickets", response_model=TicketResponse, status_code=201)
def create_ticket(
    integration_id: int,
    *,
    db: Session = Depends(get_db),
    ticket_in: TicketCreate
) -> Any:
    """Create a ticket for a given integration."""
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    ticket = Ticket(
        integration_id=integration_id,
        title=ticket_in.title,
        description=ticket_in.description,
        mitre_id=ticket_in.mitre_id,
        ticket_type=ticket_in.ticket_type
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("/integrations/{integration_id}/tickets", response_model=List[TicketResponse])
def list_tickets(integration_id: int, db: Session = Depends(get_db)) -> Any:
    """List all tickets for an integration."""
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    tickets = db.query(Ticket).filter(Ticket.integration_id == integration_id).all()
    return tickets

@router.get("/tickets", response_model=List[TicketResponse])
def list_all_tickets(db: Session = Depends(get_db)) -> Any:
    """List all tickets across all integrations."""
    tickets = db.query(Ticket).all()
    return tickets

@router.patch("/tickets/{ticket_id}/close", response_model=TicketResponse)
def close_ticket(ticket_id: int, db: Session = Depends(get_db)) -> Any:
    """Close a ticket."""
    from datetime import datetime
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.closed_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket
