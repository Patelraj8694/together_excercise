"""Controller for POST /event — record an auction win."""

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from budget_pacing.schemas.event_schema import EventRequest
from budget_pacing.services import BudgetExceededError

event_bp = Blueprint("events", __name__)


@event_bp.route("/event", methods=["POST"])
def record_event():
    """Record an auction win and attribute its cost to the campaign's daily spend.
    ---
    tags:
      - Events
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - campaign_id
            - cost
            - timestamp
          properties:
            campaign_id:
              type: string
              example: "campaign_1"
              description: Campaign identifier
            cost:
              type: number
              format: float
              example: 2.50
              description: Auction win cost in dollars (must be > 0)
            timestamp:
              type: string
              format: date-time
              example: "2026-03-18T10:00:00Z"
              description: ISO 8601 timestamp of the auction win
    responses:
      201:
        description: Event recorded successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: "recorded"
            campaign_id:
              type: string
              example: "campaign_1"
            daily_spend:
              type: number
              example: 2.50
            daily_limit:
              type: number
              example: 1000.0
      400:
        description: Request body is not valid JSON
      409:
        description: Budget exceeded — recording this event would breach the daily limit
        schema:
          type: object
          properties:
            detail:
              type: string
              example: "Recording this event would exceed the daily limit."
      422:
        description: Validation error (missing/invalid fields)
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"detail": "Request body must be valid JSON."}), 400

    # Validate with Pydantic
    try:
        payload = EventRequest.model_validate(data)
    except ValidationError as exc:
        return jsonify({"detail": exc.errors()}), 422

    # Business logic
    service = current_app.config["SERVICE"]
    try:
        result = service.record_event(payload)
    except BudgetExceededError as exc:
        return jsonify({"detail": str(exc)}), 409

    return jsonify(result.model_dump()), 201
