"""Step definitions for Phase 2 API Gherkin scenarios.

Stories: 2.QA.1 (F1 — facility_search), 2.QA.2 (F2–F6), 2.QA.3 (F7 — metadata)
"""

import pytest
from pytest_bdd import given, when, then, parsers

# ─── Background steps ─────────────────────────────────────────────────────────


@given("the seed database is loaded", target_fixture="seed_db_loaded")
def step_seed_db_loaded(seed_db):
    """Delegate to the conftest seed_db fixture."""
    return seed_db


# ─── When: direct GET calls ────────────────────────────────────────────────────


@when(parsers.parse('I GET "{path}"'), target_fixture="http_response")
def step_get_path(path, api_client, step_context):
    response = api_client.get(path)
    step_context["response"] = response
    return response


# ─── When: facility search with parameters ─────────────────────────────────────


@when(
    parsers.parse(
        "I search for facilities near lat {lat:f} lon {lon:f} within {radius:g} miles for year {year:d}"
    ),
    target_fixture="http_response",
)
def step_search_facilities(lat, lon, radius, year, api_client, step_context):
    response = api_client.get(
        "/api/v1/facilities",
        params={"lat": lat, "lon": lon, "radius_miles": radius, "year": year},
    )
    step_context["response"] = response
    return response


@when(
    parsers.parse(
        'I search for facilities near lat {lat:f} lon {lon:f} within {radius:g} miles for year {year:d} with chemical "{chemical}" and medium "{medium}"'
    ),
    target_fixture="http_response",
)
def step_search_facilities_filtered(lat, lon, radius, year, chemical, medium, api_client, step_context):
    response = api_client.get(
        "/api/v1/facilities",
        params={
            "lat": lat,
            "lon": lon,
            "radius_miles": radius,
            "year": year,
            "chemical": chemical,
            "medium": medium,
        },
    )
    step_context["response"] = response
    return response


# ─── Then: generic assertions ──────────────────────────────────────────────────


@then(parsers.parse("the response status is {status_code:d}"))
def step_response_status(status_code, step_context):
    r = step_context["response"]
    assert r.status_code == status_code, (
        f"Expected {status_code}, got {r.status_code}: {r.text[:300]}"
    )


@then("the response is a GeoJSON FeatureCollection")
def step_geojson_feature_collection(step_context):
    body = step_context["response"].json()
    assert body.get("type") == "FeatureCollection", (
        f"Expected FeatureCollection, got: {body.get('type')}"
    )
    assert "features" in body


@then("the response is a JSON array")
def step_json_array(step_context):
    body = step_context["response"].json()
    assert isinstance(body, list), f"Expected list, got {type(body)}: {str(body)[:200]}"


# ─── Then: facility assertions ─────────────────────────────────────────────────


@then(parsers.parse('facility "{facility_id}" is in the results'))
def step_facility_in_results(facility_id, step_context):
    body = step_context["response"].json()
    ids = [f["properties"]["tri_facility_id"] for f in body.get("features", [])]
    assert facility_id in ids, f"Facility {facility_id} not in results: {ids}"


@then(parsers.parse('facility "{facility_id}" has total_release_lbs {expected:f}'))
def step_facility_lbs(facility_id, expected, step_context):
    body = step_context["response"].json()
    for f in body.get("features", []):
        if f["properties"]["tri_facility_id"] == facility_id:
            actual = float(f["properties"]["total_release_lbs"])
            assert abs(actual - expected) < 0.01, f"Expected {expected} lbs, got {actual}"
            return
    pytest.fail(f"Facility {facility_id} not found in response")


@then(parsers.parse('facility "{facility_id}" has color_band "{expected_band}"'))
def step_facility_color_band(facility_id, expected_band, step_context):
    body = step_context["response"].json()
    for f in body.get("features", []):
        if f["properties"]["tri_facility_id"] == facility_id:
            actual = f["properties"]["color_band"]
            assert actual == expected_band, f"Expected color_band={expected_band}, got {actual}"
            return
    pytest.fail(f"Facility {facility_id} not found in response")


# ─── Then: superfund assertions ────────────────────────────────────────────────


@then(parsers.parse('superfund site "{epa_id}" is in the results'))
def step_superfund_in_results(epa_id, step_context):
    body = step_context["response"].json()
    ids = [f["properties"]["epa_id"] for f in body.get("features", [])]
    assert epa_id in ids, f"Superfund {epa_id} not in results: {ids}"


# ─── Then: generic field assertions ───────────────────────────────────────────


@then(parsers.parse('the response field "{field}" equals "{expected}"'))
def step_field_equals_str(field, expected, step_context):
    body = step_context["response"].json()
    actual = body.get(field)
    assert str(actual) == expected, f"Expected {field}={expected!r}, got {actual!r}"


@then(parsers.parse('the response field "{field}" equals {expected:f}'))
def step_field_equals_float(field, expected, step_context):
    body = step_context["response"].json()
    actual = body.get(field)
    assert actual is not None, f"Field {field!r} not in response"
    assert abs(float(actual) - expected) < 0.01, f"Expected {field}={expected}, got {actual}"


@then(parsers.parse('the response field "{field}" is not null'))
def step_field_not_null(field, step_context):
    body = step_context["response"].json()
    assert body.get(field) is not None, f"Field {field!r} is null"


@then(parsers.parse('the response field "{field}" is a non-empty list'))
def step_field_non_empty_list(field, step_context):
    body = step_context["response"].json()
    val = body.get(field)
    assert isinstance(val, list) and len(val) > 0, (
        f"Field {field!r} = {val!r} is not a non-empty list"
    )


# ─── Then: chemical-specific assertions ───────────────────────────────────────


@then(parsers.parse('the response contains a chemical named "{name}"'))
def step_contains_chemical(name, step_context):
    body = step_context["response"].json()
    names = [c["name"] for c in body]
    assert name in names, f"{name!r} not in chemical names: {names}"


@then(parsers.parse('the first result name contains "{substring}"'))
def step_first_result_name_contains(substring, step_context):
    body = step_context["response"].json()
    assert len(body) > 0, "Response array is empty"
    name = body[0]["name"]
    assert substring.upper() in name.upper(), f"{substring!r} not in {name!r}"


@then(parsers.parse('the first result field "{field}" equals "{expected}"'))
def step_first_result_field_str(field, expected, step_context):
    body = step_context["response"].json()
    assert len(body) > 0, "Response array is empty"
    actual = body[0].get(field)
    assert str(actual) == expected, f"Expected first[{field}]={expected!r}, got {actual!r}"


# ─── Then: content type / body assertions ─────────────────────────────────────


@then(parsers.parse('the response content type is "{expected_mime}"'))
def step_content_type(expected_mime, step_context):
    ct = step_context["response"].headers.get("content-type", "")
    assert expected_mime in ct, (
        f"Expected content-type containing {expected_mime!r}, got {ct!r}"
    )


@then(parsers.parse('the response body contains "{substring}"'))
def step_body_contains(substring, step_context):
    body = step_context["response"].text
    assert substring in body, (
        f"{substring!r} not found in response body (first 300): {body[:300]}"
    )


@then('the response meta contains "units"')
def step_meta_contains_units(step_context):
    body = step_context["response"].json()
    meta = body.get("meta", {})
    assert "units" in meta, f"'units' not in meta: {meta}"


# ─── Then: meta field assertions ──────────────────────────────────────────────


@then(parsers.parse('the response meta has "{field}" = true'))
def step_meta_field_true(field, step_context):
    body = step_context["response"].json()
    meta = body.get("meta", {})
    query = meta.get("query", {})
    actual = query.get(field) or meta.get(field)
    assert actual is True, f"Expected meta.{field}=true, got {actual!r}"


@then(parsers.parse('the response meta has "{field}" = {expected:d}'))
def step_meta_field_int(field, expected, step_context):
    body = step_context["response"].json()
    meta = body.get("meta", {})
    query = meta.get("query", {})
    actual = query.get(field) or meta.get(field)
    assert actual == expected, f"Expected meta.{field}={expected}, got {actual!r}"


# ─── Then: feature count assertions ───────────────────────────────────────────


@then(parsers.parse("the FeatureCollection contains more than {count:d} features"))
def step_feature_count_more_than(count, step_context):
    body = step_context["response"].json()
    actual = len(body.get("features", []))
    assert actual > count, f"Expected more than {count} features, got {actual}"


@then(parsers.parse("the FeatureCollection contains at least {count:d} features"))
def step_feature_count_at_least(count, step_context):
    body = step_context["response"].json()
    actual = len(body.get("features", []))
    assert actual >= count, f"Expected at least {count} features, got {actual}"


@then(parsers.parse("the FeatureCollection contains exactly {count:d} features"))
def step_feature_count_exactly(count, step_context):
    body = step_context["response"].json()
    actual = len(body.get("features", []))
    assert actual == count, f"Expected exactly {count} features, got {actual}"


# ─── Then: every feature property assertions ──────────────────────────────────


@then(parsers.parse('every feature has property "{prop}" = "{expected}"'))
def step_every_feature_prop_equals(prop, expected, step_context):
    body = step_context["response"].json()
    features = body.get("features", [])
    for f in features:
        actual = f.get("properties", {}).get(prop)
        assert str(actual) == expected, (
            f"Feature has {prop}={actual!r}, expected {expected!r}"
        )
