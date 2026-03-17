"""Controller for GET /bid — return a paced bid recommendation."""

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from budget_pacing.schemas.bid_schema import BidRequest, BidResponse

bid_bp = Blueprint("bids", __name__)


@bid_bp.route("/bid", methods=["GET"])
def get_bid():
    """Return an optimised bid for a campaign adjusted by time-of-day pacing.
    ---
    tags:
      - Bids
    parameters:
      - in: query
        name: campaign_id
        type: string
        required: true
        description: Campaign identifier
        example: "campaign_1"
      - in: query
        name: geo
        type: string
        required: false
        description: Geographic context (optional, accepted but not used in v1)
        example: "US"
    responses:
      200:
        description: Paced bid recommendation
        schema:
          type: object
          properties:
            bid:
              type: number
              format: float
              example: 1.50
              description: Recommended bid amount in dollars
            campaign_id:
              type: string
              example: "campaign_1"
      422:
        description: Validation error (missing campaign_id)
    """
    # Validate query params with Pydantic
    try:
        params = BidRequest.model_validate(dict(request.args))
    except ValidationError as exc:
        return jsonify({"detail": exc.errors()}), 422

    # Business logic
    service = current_app.config["SERVICE"]
    bid = service.get_bid(
        campaign_id=params.campaign_id,
        geo=params.geo,
    )

    response = BidResponse(bid=bid, campaign_id=params.campaign_id)
    return jsonify(response.model_dump()), 200
