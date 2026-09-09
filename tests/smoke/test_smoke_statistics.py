from models.statistics import Statistics


def _seed_statistics(**kwargs):
    year, month = Statistics.current_year_month()
    payload = {
        "id": Statistics.build_id(
            year=year, month=month, membership=kwargs.get("membership", "weekly")
        ),
        "year": year,
        "month": month,
        "membership": kwargs.get("membership", "weekly"),
        "sold_memberships": kwargs.get("sold_memberships", 2),
        "amount": kwargs.get("amount", 60.0),
    }
    Statistics(**payload).save()
    return payload


def test_get_all_statistics_success(admin_max_client):
    _seed_statistics(membership="weekly", sold_memberships=3, amount=90.0)
    _seed_statistics(membership="student", sold_memberships=2, amount=70.0)

    response = admin_max_client.get(
        "/statistics",
        params={
            "year": Statistics.current_year_month()[0],
            "month": Statistics.current_year_month()[1],
        },
    )

    assert response.status_code == 200, f"Failed to get statistics: {response.json()}"
    payload = response.json()
    assert isinstance(payload, list), "Expected a list of statistics"
    assert any(item.get("membership") == "weekly" for item in payload)
    assert any(item.get("membership") == "student" for item in payload)


def test_get_statistics_by_membership_success(admin_max_client):
    _seed_statistics(membership="weekly", sold_memberships=4, amount=120.0)

    response = admin_max_client.get("/statistics", params={"membership": "weekly"})

    assert response.status_code == 200, (
        f"Failed to get filtered statistics: {response.json()}"
    )
    payload = response.json()
    assert isinstance(payload, list), "Expected a list of statistics"
    assert all(item.get("membership") == "weekly" for item in payload)


def test_get_current_month_statistics_success(admin_max_client):
    _seed_statistics(membership="weekly", sold_memberships=5, amount=150.0)
    _seed_statistics(membership="normal", sold_memberships=1, amount=50.0)

    response = admin_max_client.get("/statistics/current")

    assert response.status_code == 200, (
        f"Failed to get current month statistics: {response.json()}"
    )
    payload = response.json()
    assert isinstance(payload, list), "Expected a list of current month statistics"
    assert any(item.get("membership") == "weekly" for item in payload)
    assert any(item.get("membership") == "normal" for item in payload)


def test_get_current_month_statistics_by_membership_success(admin_max_client):
    _seed_statistics(membership="weekly", sold_memberships=6, amount=180.0)

    response = admin_max_client.get(
        "/statistics/current", params={"membership": "weekly"}
    )

    assert response.status_code == 200, (
        f"Failed to get specific current month statistic: {response.json()}"
    )
    payload = response.json()
    assert payload.get("membership") == "weekly"
    assert payload.get("sold_memberships") == 6


def test_statistics_no_data_returns_404(admin_max_client):
    Statistics.drop_collection()

    response = admin_max_client.get("/statistics", params={"year": 2099, "month": 1})

    assert response.status_code == 404
    assert (
        response.json().get("message")
        == "No statistics found for the specified filters."
    )


def test_current_statistics_no_data_returns_404(admin_max_client):
    Statistics.drop_collection()

    response = admin_max_client.get("/statistics/current")

    assert response.status_code == 404
    assert (
        response.json().get("message") == "No statistics found for the current month."
    )


def test_statistics_reject_unknown_membership(admin_max_client):
    response = admin_max_client.get(
        "/statistics", params={"membership": "unknown_plan"}
    )

    assert response.status_code == 404
    assert response.json().get("message") == "Membership not found."


def test_current_statistics_reject_unknown_membership(admin_max_client):
    response = admin_max_client.get(
        "/statistics/current", params={"membership": "unknown_plan"}
    )

    assert response.status_code == 404
    assert response.json().get("message") == "Membership not found."


def test_statistics_requires_max_admin(admin_min_client):
    response = admin_min_client.get("/statistics")

    assert response.status_code == 403, (
        f"Statistics should have been forbidden: {response.json()}"
    )
    assert response.json().get("message") == "Forbidden: Unauthorized request"
