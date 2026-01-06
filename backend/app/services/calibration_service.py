import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DecisionNode, DecisionOutcome, CalibrationModel
from app.models.decision import DecisionStatus
from app.services.decision_service import DecisionService


class CalibrationService:
    """Service for calibration and outcome tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.decision_service = DecisionService(db)

    @staticmethod
    def compute_brier_score(predicted_prob: float, actual_outcome: bool) -> float:
        """
        Compute Brier score for a prediction.

        Args:
            predicted_prob: Predicted probability of success (0.0-1.0)
            actual_outcome: Whether progress was made

        Returns:
            Brier score (0.0-1.0, lower is better)
        """
        actual = 1.0 if actual_outcome else 0.0
        return (predicted_prob - actual) ** 2

    async def record_outcome(
        self,
        node_id: uuid.UUID,
        progress_yesno: bool,
        sentiment_2h: int | None = None,
        sentiment_24h: int | None = None,
        notes: str | None = None,
    ) -> DecisionOutcome:
        """
        Record outcome for a decision and compute Brier score.

        Args:
            node_id: ID of the decision node
            progress_yesno: Whether progress was made
            sentiment_2h: Sentiment after 2 hours (-2 to +2)
            sentiment_24h: Sentiment after 24 hours (-2 to +2)
            notes: Optional notes

        Returns:
            Created outcome record
        """
        # Get the node to find predicted probability
        node = await self.decision_service.get_node(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        if not node.chosen_move_id or not node.moves_json:
            raise ValueError("No move was chosen for this node")

        # Find the chosen move and its predicted probability
        moves = node.moves_json.get("moves", [])
        chosen_move = next(
            (m for m in moves if m["move_id"] == node.chosen_move_id), None
        )
        if not chosen_move:
            raise ValueError("Chosen move not found in moves")

        # Compute Brier score
        predicted_prob = chosen_move.get("p_calibrated_progress", 0.5)
        brier = self.compute_brier_score(predicted_prob, progress_yesno)

        # Create outcome record
        outcome = DecisionOutcome(
            node_id=node_id,
            progress_yesno=progress_yesno,
            sentiment_2h=sentiment_2h,
            sentiment_24h=sentiment_24h,
            brier_score=Decimal(str(round(brier, 4))),
            notes=notes,
        )
        self.db.add(outcome)

        # Update decision status to resolved
        decision = await self.decision_service.get_decision(node.decision_id)
        if decision:
            decision.status = DecisionStatus.RESOLVED.value
            await self.db.commit()

        # Log event
        await self.decision_service.log_event(
            decision_id=node.decision_id,
            node_id=node_id,
            event_type="resolved",
            payload={
                "progress_yesno": progress_yesno,
                "brier_score": float(brier),
                "predicted_prob": predicted_prob,
            },
        )

        await self.db.refresh(outcome)
        return outcome

    async def get_calibration_model(
        self, situation_type: str | None = None
    ) -> CalibrationModel | None:
        """Get active calibration model for a situation type."""
        query = select(CalibrationModel).where(CalibrationModel.is_active == True)
        if situation_type:
            query = query.where(CalibrationModel.situation_type == situation_type)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def calibrate_probability(
        self, raw_prob: float, situation_type: str | None = None
    ) -> float:
        """
        Apply calibration to a raw probability.

        For v1, this returns the raw probability unchanged.
        Future versions will apply binning calibration based on historical outcomes.
        """
        # Stub for v1 - no calibration applied
        model = await self.get_calibration_model(situation_type)
        if not model or not model.parameters_json:
            return raw_prob

        # Future: Apply calibration based on model parameters
        # For now, just return raw probability
        return raw_prob

    async def update_calibration(self, situation_type: str | None = None) -> None:
        """
        Update calibration model based on outcomes.

        This is a stub for the scheduled job that will update calibration.
        """
        # TODO: Implement binning calibration update
        # 1. Query all outcomes for the situation type
        # 2. Bin by predicted probability
        # 3. Compute actual success rate per bin
        # 4. Update calibration model parameters
        pass
