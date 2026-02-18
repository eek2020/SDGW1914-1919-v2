"""Tests for Phase C: Flask web application."""

import pytest
from src.web_app import app


@pytest.fixture
def client():
    """Flask test client using the real database."""
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


# ── Home Page ────────────────────────────────────────────────────────────

class TestHomePage:
    def test_home_loads(self, client):
        r = client.get('/')
        assert r.status_code == 200

    def test_home_has_search_form(self, client):
        r = client.get('/')
        assert b'surname' in r.data
        assert b'christian_names' in r.data
        assert b'Search' in r.data

    def test_home_has_dropdowns(self, client):
        r = client.get('/')
        assert b'rank_name' in r.data
        assert b'battalion_id' in r.data
        assert b'death_location' in r.data

    def test_home_has_new_fields(self, client):
        """Enlistment location and decoration fields present on home page."""
        r = client.get('/')
        assert b'enlistment_loc' in r.data
        assert b'decoration' in r.data

    def test_home_has_accessibility_features(self, client):
        r = client.get('/')
        assert b'skip-to-main' in r.data
        assert b'role="banner"' in r.data
        assert b'role="main"' in r.data
        assert b'role="contentinfo"' in r.data
        assert b'role="search"' in r.data


# ── Search Results ───────────────────────────────────────────────────────

class TestSearchResults:
    def test_search_by_surname(self, client):
        r = client.get('/search?surname=SMITH&record_type=soldiers')
        assert r.status_code == 200
        assert b'SMITH' in r.data
        assert b'records found' in r.data

    def test_search_all_record_types(self, client):
        r = client.get('/search?surname=SMITH&record_type=all')
        assert r.status_code == 200

    def test_search_officers_only(self, client):
        r = client.get('/search?surname=SMITH&record_type=officers')
        assert r.status_code == 200

    def test_search_no_results(self, client):
        r = client.get('/search?surname=XYZNONEXISTENT')
        assert r.status_code == 200
        assert b'No Results Found' in r.data

    def test_search_has_filter_pills(self, client):
        r = client.get('/search?surname=SMITH&record_type=soldiers')
        assert b'filter-pill' in r.data
        assert b'Surname' in r.data

    def test_search_has_sort_control(self, client):
        r = client.get('/search?surname=SMITH&record_type=soldiers')
        assert b'sort-select' in r.data

    def test_search_sort_by_date(self, client):
        r = client.get('/search?surname=SMITH&record_type=soldiers&sort=date_desc')
        assert r.status_code == 200

    def test_search_sort_by_rank(self, client):
        r = client.get('/search?surname=SMITH&record_type=soldiers&sort=rank')
        assert r.status_code == 200

    def test_search_has_table_view(self, client):
        r = client.get('/search?surname=SMITH&record_type=soldiers')
        assert b'table-view' in r.data
        assert b'card-view' in r.data

    def test_search_pagination(self, client):
        r = client.get('/search?surname=SMITH&record_type=soldiers&page=2')
        assert r.status_code == 200
        assert b'Page 2 of' in r.data
        assert b'First' in r.data
        assert b'Last' in r.data
        assert b'Previous' in r.data

    def test_search_first_page_no_first_link(self, client):
        """First page should not have a 'First' pagination link."""
        r = client.get('/search?surname=XYZRARE_SINGLE&record_type=soldiers')
        # With no results or single page, no First link
        assert b'&laquo; First' not in r.data

    def test_search_position_tracking(self, client):
        """Result links should include pos= parameter."""
        r = client.get('/search?surname=SMITH&record_type=soldiers')
        assert b'pos=0' in r.data

    def test_search_multi_param(self, client):
        """Multi-parameter search with surname + death date range."""
        r = client.get('/search?surname=SMITH&record_type=soldiers&death_date_from=1916-01-01&death_date_to=1916-12-31')
        assert r.status_code == 200
        assert b'filter-pill' in r.data

    def test_search_by_battalion(self, client):
        r = client.get('/search?battalion_id=1&record_type=soldiers')
        assert r.status_code == 200

    def test_search_by_enlistment_loc(self, client):
        r = client.get('/search?enlistment_loc=LONDON&record_type=soldiers')
        assert r.status_code == 200

    def test_search_by_decoration(self, client):
        r = client.get('/search?decoration=DSO&record_type=officers')
        assert r.status_code == 200

    def test_search_enlistment_filter_pill(self, client):
        r = client.get('/search?enlistment_loc=LONDON&record_type=soldiers')
        assert b'Enlistment' in r.data

    def test_search_decoration_filter_pill(self, client):
        r = client.get('/search?decoration=MC&record_type=officers')
        assert b'Decoration' in r.data

    def test_search_has_accessibility_landmarks(self, client):
        r = client.get('/search?surname=SMITH')
        assert b'role="banner"' in r.data
        assert b'role="main"' in r.data
        assert b'skip-to-main' in r.data


# ── Detail View ──────────────────────────────────────────────────────────

class TestDetailView:
    def test_soldier_detail(self, client):
        r = client.get('/record/soldier/1')
        assert r.status_code == 200
        assert b'Personnel Record' in r.data

    def test_officer_detail(self, client):
        r = client.get('/record/officer/1')
        assert r.status_code == 200
        assert b'Personnel Record' in r.data

    def test_detail_404(self, client):
        r = client.get('/record/soldier/999999999')
        assert r.status_code == 404
        assert b'Page Not Found' in r.data
        assert b'Go to Search' in r.data

    def test_detail_has_sections(self, client):
        r = client.get('/record/soldier/1')
        assert b'Personal Information' in r.data
        assert b'Military Service' in r.data
        assert b'Casualty Information' in r.data

    def test_detail_has_related_records(self, client):
        r = client.get('/record/soldier/1')
        assert b'Explore Related Records' in r.data or b'related' in r.data

    def test_detail_no_nav_without_search(self, client):
        """Without search context, no prev/next navigation bar."""
        r = client.get('/record/soldier/1')
        assert b'record-nav' not in r.data

    def test_detail_nav_with_search(self, client):
        """With search context and pos, prev/next navigation appears."""
        r = client.get('/record/soldier/1?surname=SMITH&search_type=soldiers&pos=5')
        assert r.status_code == 200
        assert b'record-nav' in r.data
        assert b'Record 6 of' in r.data  # pos=5 -> 1-based display

    def test_detail_back_to_results(self, client):
        """Back to Results link preserves search and calculates correct page."""
        r = client.get('/record/soldier/1?surname=SMITH&search_type=soldiers&pos=55')
        assert r.status_code == 200
        assert b'Back to Results' in r.data

    def test_detail_accessibility(self, client):
        r = client.get('/record/soldier/1')
        assert b'skip-to-main' in r.data
        assert b'role="banner"' in r.data
        assert b'role="main"' in r.data

    def test_detail_print_button(self, client):
        r = client.get('/record/soldier/1')
        assert b'Print Record' in r.data


# ── API: Surname Autocomplete ────────────────────────────────────────────

class TestSurnameAutocomplete:
    def test_autocomplete_returns_results(self, client):
        r = client.get('/api/surname-suggest?q=SM')
        assert r.status_code == 200
        data = r.get_json()
        assert len(data) > 0
        assert all(s.startswith('SM') for s in data)

    def test_autocomplete_short_query(self, client):
        r = client.get('/api/surname-suggest?q=S')
        assert r.status_code == 200
        assert r.get_json() == []

    def test_autocomplete_empty_query(self, client):
        r = client.get('/api/surname-suggest?q=')
        assert r.status_code == 200
        assert r.get_json() == []

    def test_autocomplete_no_match(self, client):
        r = client.get('/api/surname-suggest?q=XYZNONEXISTENT')
        assert r.status_code == 200
        assert r.get_json() == []

    def test_autocomplete_limit(self, client):
        r = client.get('/api/surname-suggest?q=SM')
        data = r.get_json()
        assert len(data) <= 50

    def test_autocomplete_with_active_filters(self, client):
        r = client.get('/api/surname-suggest?q=SM&record_type=soldiers&rank_name=Private')
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)


# ── API: Filter Options ─────────────────────────────────────────────────

class TestFilterOptions:
    def test_unfiltered_returns_flag(self, client):
        r = client.get('/api/filter-options')
        assert r.status_code == 200
        data = r.get_json()
        assert data['unfiltered'] is True
        assert 'text_suggestions' in data
        assert 'death_date_bounds' in data

    def test_filtered_by_surname(self, client):
        r = client.get('/api/filter-options?surname=SMITH')
        assert r.status_code == 200
        data = r.get_json()
        assert data['unfiltered'] is False
        assert 'ranks' in data
        assert 'battalions' in data
        assert 'death_locations' in data
        assert 'text_suggestions' in data
        assert 'death_date_bounds' in data

    def test_unfocused_returns_empty_text_suggestions(self, client):
        """Unfocused requests return empty text suggestions for performance."""
        r = client.get('/api/filter-options?surname=SMITH')
        assert r.status_code == 200
        data = r.get_json()
        ts = data['text_suggestions']

        expected_fields = {
            'christian_names',
            'initials',
            'service_number',
            'birth_town',
            'enlistment_loc',
            'decoration',
        }
        assert expected_fields.issubset(set(ts.keys()))
        # Without focused_text_field, all lists should be empty (perf optimization)
        assert all(len(ts[field]) == 0 for field in expected_fields)

    def test_filtered_by_dropdown_only(self, client):
        r = client.get('/api/filter-options?rank_name=Private')
        assert r.status_code == 200
        data = r.get_json()
        assert data['unfiltered'] is False

    def test_filtered_by_record_type(self, client):
        r = client.get('/api/filter-options?surname=SMITH&record_type=officers')
        assert r.status_code == 200

    def test_focused_text_field_limits_text_suggestions(self, client):
        r = client.get('/api/filter-options?surname=SMITH&focused_text_field=initials')
        assert r.status_code == 200
        data = r.get_json()
        assert data['unfiltered'] is False
        assert 'text_suggestions' in data
        ts = data['text_suggestions']
        assert 'initials' in ts
        for key, values in ts.items():
            if key != 'initials':
                assert values == []
