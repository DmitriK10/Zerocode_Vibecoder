import pytest
from app.services.behavior_metrics_service import BehaviorMetricsService
from app.schemas import BehaviorMetricsCreate


@pytest.mark.asyncio
async def test_create_behavior_metric(db_session):
    service = BehaviorMetricsService(db_session)
    data = BehaviorMetricsCreate(
        lead_id=1,
        page_load_time=1.5,
        session_duration=2.3,
        clicks=10,
        scroll_depth=50,
        other_metrics={"test": True}
    )
    metric = await service.create(data)
    assert metric.id is not None
    assert metric.lead_id == 1
    assert metric.clicks == 10


@pytest.mark.asyncio
async def test_get_behavior_metrics_by_lead(db_session):
    service = BehaviorMetricsService(db_session)
    await service.create(BehaviorMetricsCreate(lead_id=1, clicks=5))
    metric = await service.get_by_lead_id(1)
    assert metric is not None
    assert metric.clicks == 5