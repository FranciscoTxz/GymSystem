from typing import cast

from fastapi import HTTPException
from mongoengine import DoesNotExist

from models.statistics import Statistics
from schemas.statistics_schema import StatisticInfo
from services.membership_service import MembershipService


class StatisticsService:
    @staticmethod
    def _to_schema(statistic: Statistics) -> StatisticInfo:
        return StatisticInfo(
            id=cast(str, statistic.id),
            year=cast(int, statistic.year),
            month=cast(int, statistic.month),
            membership=cast(str, statistic.membership),
            sold_memberships=cast(int, statistic.sold_memberships),
            amount=cast(float, statistic.amount),
        )

    @staticmethod
    def add_membership_sale(membership: str, amount: float) -> Statistics:
        year, month = Statistics.current_year_month()
        statistic_id = Statistics.build_id(
            year=year,
            month=month,
            membership=membership,
        )

        Statistics.objects(id=statistic_id).update_one(
            upsert=True,
            inc__sold_memberships=1,
            inc__amount=amount,
            set_on_insert__year=year,
            set_on_insert__month=month,
            set_on_insert__membership=membership,
        )

        return Statistics.objects.get(id=statistic_id)

    @staticmethod
    def get_current_month(membership: str | None = None):
        year, month = Statistics.current_year_month()

        if membership is not None:
            MembershipService.get_membership(membership)

            id = Statistics.build_id(year=year, month=month, membership=membership)
            try:
                statistic = Statistics.objects.get(id=id)
            except DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Statistic not found for the current month and specified membership.",
                )

            return StatisticsService._to_schema(statistic)

        statistics = Statistics.objects(year=year, month=month).order_by("membership")

        if not statistics:
            raise HTTPException(
                status_code=404, detail="No statistics found for the current month."
            )

        return [StatisticsService._to_schema(statistic) for statistic in statistics]

    @staticmethod
    def get_all_statistics(
        year: int | None = None, month: int | None = None, membership: str | None = None
    ):
        query = Statistics.objects

        if year is not None:
            query = query.filter(year=year)
        if month is not None:
            query = query.filter(month=month)
        if membership is not None:
            MembershipService.get_membership(membership)
            query = query.filter(membership=membership)

        statistics = query.order_by("year", "month", "membership")

        if not statistics:
            raise HTTPException(
                status_code=404, detail="No statistics found for the specified filters."
            )

        return [StatisticsService._to_schema(statistic) for statistic in statistics]
