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


# ─── ADR-007: Chemical Family Expansion Steps ─────────────────────────────────


def _get_nested_meta(body: dict, dotted_path: str):
    """Helper to traverse nested meta paths like 'search_expansion.expanded'."""
    meta = body.get("meta", {})
    query = meta.get("query", {})
    # Try both meta and meta.query for nested paths
    parts = dotted_path.split(".")
    # Start from search_expansion which can be in meta or meta.query
    obj = query.get(parts[0]) or meta.get(parts[0])
    for part in parts[1:]:
        if obj is None:
            return None
        obj = obj.get(part) if isinstance(obj, dict) else None
    return obj


@when(
    parsers.parse(
        'I search for facilities near lat {lat:f} lon {lon:f} within {radius:g} miles for year {year:d} with chemical "{chemical}"'
    ),
    target_fixture="http_response",
)
def step_search_facilities_chemical(lat, lon, radius, year, chemical, api_client, step_context):
    response = api_client.get(
        "/api/v1/facilities",
        params={"lat": lat, "lon": lon, "radius_miles": radius, "year": year, "chemical": chemical},
    )
    step_context["response"] = response
    return response


@when(
    parsers.parse(
        'I search for facilities near lat {lat:f} lon {lon:f} within {radius:g} miles for year {year:d} with chemical "{chemical}" and exact_match true'
    ),
    target_fixture="http_response",
)
def step_search_facilities_chemical_exact(lat, lon, radius, year, chemical, api_client, step_context):
    response = api_client.get(
        "/api/v1/facilities",
        params={
            "lat": lat,
            "lon": lon,
            "radius_miles": radius,
            "year": year,
            "chemical": chemical,
            "exact_match": "true",
        },
    )
    step_context["response"] = response
    return response


@then(parsers.parse('the response meta has "{dotted_path}" = true'))
def step_meta_nested_true(dotted_path, step_context):
    body = step_context["response"].json()
    actual = _get_nested_meta(body, dotted_path)
    assert actual is True, f"Expected meta.{dotted_path}=true, got {actual!r}"


@then(parsers.parse('the response meta has "{dotted_path}" = "{expected}"'))
def step_meta_nested_str(dotted_path, expected, step_context):
    body = step_context["response"].json()
    actual = _get_nested_meta(body, dotted_path)
    assert str(actual) == expected, f"Expected meta.{dotted_path}={expected!r}, got {actual!r}"


@then(parsers.parse('the response meta "{dotted_path}" contains "{value}"'))
def step_meta_nested_contains(dotted_path, value, step_context):
    body = step_context["response"].json()
    actual = _get_nested_meta(body, dotted_path)
    assert isinstance(actual, list), f"Expected meta.{dotted_path} to be a list, got {type(actual)}"
    assert value in actual, f"Expected {value!r} in meta.{dotted_path}, got {actual}"


@then(parsers.parse('the response meta does not have "{dotted_path}"'))
def step_meta_nested_absent(dotted_path, step_context):
    body = step_context["response"].json()
    actual = _get_nested_meta(body, dotted_path)
    assert actual is None, f"Expected meta.{dotted_path} to be absent, got {actual!r}"


@then(parsers.parse('I save the result count as "{label}"'))
def step_save_result_count(label, step_context):
    body = step_context["response"].json()
    count = len(body.get("features", []))
    step_context[label] = count


@then(parsers.parse('the result count is less than "{label}"'))
def step_result_count_less_than(label, step_context):
    body = step_context["response"].json()
    current_count = len(body.get("features", []))
    saved_count = step_context.get(label)
    assert saved_count is not None, f"No saved count for {label!r}"
    assert current_count < saved_count, (
        f"Expected fewer results than {label}={saved_count}, got {current_count}"
    )


# ─── Regression: 7.BUG.15 — Chemical family list length ───────────────────────


@then(parsers.parse('the response meta "{dotted_path}" has at least {count:d} items'))
def step_meta_list_min_length(dotted_path, count, step_context):
    """Verify that a list in the response meta has at least N items."""
    body = step_context["response"].json()
    actual = _get_nested_meta(body, dotted_path)
    assert isinstance(actual, list), f"Expected meta.{dotted_path} to be a list, got {type(actual)}"
    assert len(actual) >= count, (
        f"Expected meta.{dotted_path} to have at least {count} items, got {len(actual)}: {actual}"
    )


# ─── Regression: 7.BUG.17–7.BUG.19 — Superfund contaminant CAS/ATSDR ──────────


def _find_contaminant(body: dict, name: str) -> dict | None:
    """Find a contaminant by name in Superfund site response."""
    contaminants = body.get("contaminants", [])
    name_upper = name.upper()
    for c in contaminants:
        if c.get("name", "").upper() == name_upper:
            return c
    return None


@then(parsers.parse('contaminant "{name}" has atsdr_url containing "{substring}"'))
def step_contaminant_atsdr_contains(name, substring, step_context):
    """Verify a contaminant's ATSDR URL contains the expected substring (e.g., toxid=23)."""
    body = step_context["response"].json()
    contaminant = _find_contaminant(body, name)
    assert contaminant is not None, (
        f"Contaminant {name!r} not found. Available: {[c['name'] for c in body.get('contaminants', [])]}"
    )
    atsdr_url = contaminant.get("atsdr_url")
    assert atsdr_url is not None, f"Contaminant {name!r} has no atsdr_url"
    assert substring in atsdr_url, (
        f"Expected {name!r} atsdr_url to contain {substring!r}, got {atsdr_url!r}"
    )


@then(parsers.parse('contaminant "{name}" atsdr_url does NOT contain "{substring}"'))
def step_contaminant_atsdr_not_contains(name, substring, step_context):
    """Verify a contaminant's ATSDR URL does NOT contain a substring (regression for wrong toxid)."""
    body = step_context["response"].json()
    contaminant = _find_contaminant(body, name)
    assert contaminant is not None, (
        f"Contaminant {name!r} not found. Available: {[c['name'] for c in body.get('contaminants', [])]}"
    )
    atsdr_url = contaminant.get("atsdr_url") or ""
    assert substring not in atsdr_url, (
        f"REGRESSION: {name!r} atsdr_url should NOT contain {substring!r}, but got {atsdr_url!r}"
    )


@then(parsers.parse('contaminant "{name}" has cas_number "{expected_cas}"'))
def step_contaminant_cas_number(name, expected_cas, step_context):
    """Verify a contaminant has the correct CAS number from lookup."""
    body = step_context["response"].json()
    contaminant = _find_contaminant(body, name)
    assert contaminant is not None, (
        f"Contaminant {name!r} not found. Available: {[c['name'] for c in body.get('contaminants', [])]}"
    )
    actual_cas = contaminant.get("cas_number")
    assert actual_cas == expected_cas, (
        f"Expected {name!r} cas_number={expected_cas!r}, got {actual_cas!r}"
    )
