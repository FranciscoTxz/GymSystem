from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist

from services import statistics_service as statistics_module
from services.statistics_service import StatisticsService


def _statistic():
    return SimpleNamespace(
        id="2026-09-basic",
        year=2026,
        month=9,
        membership="basic",
        sold_memberships=4,
        amount=1200.0,
    )


def test_to_schema_copies_statistic_fields():
    result = StatisticsService._to_schema(_statistic())

    assert result.model_dump() == {
        "id": "2026-09-basic",
        "year": 2026,
        "month": 9,
        "membership": "basic",
        "sold_memberships": 4,
        "amount": 1200.0,
    }


def test_add_membership_sale_upserts_and_returns_statistic(monkeypatch):
    statistic = _statistic()
    objects = MagicMock()
    objects.return_value.update_one.return_value = None
    objects.get.return_value = statistic
    statistics = SimpleNamespace(
        objects=objects,
        current_year_month=lambda: (2026, 9),
        build_id=lambda year, month, membership: f"{year}-{month:02d}-{membership}",
    )
    monkeypatch.setattr(statistics_module, "Statistics", statistics)

    result = StatisticsService.add_membership_sale("basic", 300.0)

    assert result is statistic
    objects.return_value.update_one.assert_called_once_with(
        upsert=True,
        inc__sold_memberships=1,
        inc__amount=300.0,
        set_on_insert__year=2026,
        set_on_insert__month=9,
        set_on_insert__membership="basic",
    )


def test_get_current_month_returns_selected_membership(monkeypatch):
    statistic = _statistic()
    objects = MagicMock()
    objects.get.return_value = statistic
    statistics = SimpleNamespace(
        objects=objects,
        current_year_month=lambda: (2026, 9),
        build_id=lambda year, month, membership: f"{year}-{month:02d}-{membership}",
    )
    monkeypatch.setattr(statistics_module, "Statistics", statistics)
    membership_lookup = MagicMock()
    monkeypatch.setattr(
        statistics_module.MembershipService, "get_membership", membership_lookup
    )

    result = StatisticsService.get_current_month("basic")

    assert result.id == "2026-09-basic"
    membership_lookup.assert_called_once_with("basic")


def test_get_current_month_rejects_missing_selected_statistic(monkeypatch):
    objects = MagicMock()
    objects.get.side_effect = DoesNotExist
    statistics = SimpleNamespace(
        objects=objects,
        current_year_month=lambda: (2026, 9),
        build_id=lambda **kwargs: "statistic-id",
    )
    monkeypatch.setattr(statistics_module, "Statistics", statistics)
    monkeypatch.setattr(
        statistics_module.MembershipService, "get_membership", MagicMock()
    )

    with pytest.raises(HTTPException, match="Statistic not found") as error:
        StatisticsService.get_current_month("basic")

    assert error.value.status_code == 404


def test_get_current_month_returns_all_statistics(monkeypatch):
    objects = MagicMock()
    objects.return_value.order_by.return_value = [_statistic()]
    statistics = SimpleNamespace(objects=objects, current_year_month=lambda: (2026, 9))
    monkeypatch.setattr(statistics_module, "Statistics", statistics)

    result = StatisticsService.get_current_month()

    assert [statistic.membership for statistic in result] == ["basic"]


def test_get_current_month_rejects_empty_statistics(monkeypatch):
    objects = MagicMock()
    objects.return_value.order_by.return_value = []
    statistics = SimpleNamespace(objects=objects, current_year_month=lambda: (2026, 9))
    monkeypatch.setattr(statistics_module, "Statistics", statistics)

    with pytest.raises(HTTPException, match="No statistics found") as error:
        StatisticsService.get_current_month()

    assert error.value.status_code == 404


def test_get_all_statistics_applies_all_filters(monkeypatch):
    statistic = _statistic()
    query = MagicMock()
    query.filter.return_value = query
    query.order_by.return_value = [statistic]
    membership_lookup = MagicMock()
    monkeypatch.setattr(statistics_module, "Statistics", SimpleNamespace(objects=query))
    monkeypatch.setattr(
        statistics_module.MembershipService, "get_membership", membership_lookup
    )

    result = StatisticsService.get_all_statistics(2026, 9, "basic")

    assert [item.id for item in result] == ["2026-09-basic"]
    assert query.filter.call_args_list[0].kwargs == {"year": 2026}
    assert query.filter.call_args_list[1].kwargs == {"month": 9}
    assert query.filter.call_args_list[2].kwargs == {"membership": "basic"}
    membership_lookup.assert_called_once_with("basic")


def test_get_all_statistics_rejects_empty_result(monkeypatch):
    query = MagicMock()
    query.order_by.return_value = []
    monkeypatch.setattr(statistics_module, "Statistics", SimpleNamespace(objects=query))

    with pytest.raises(HTTPException, match="No statistics found") as error:
        StatisticsService.get_all_statistics()

    assert error.value.status_code == 404
