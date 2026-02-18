"""Tests for UI structure, templates, and accessibility (ENH-02).

Uses BeautifulSoup to parse HTML responses and verify:
- Template structure and content
- Pagination link correctness (search params preserved)
- Filter pill rendering
- Record navigation links
- Sort control rendering
- Card vs table view HTML
- Breadcrumb navigation
- Death date formatting (human-readable)
- CSV export button and route
- 404 page content
- Accessibility attributes (ARIA labels, skip-to-main)
"""

import pytest
from bs4 import BeautifulSoup
from src.web_app import app


@pytest.fixture
def client():
    """Flask test client using the real database."""
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def soup(response):
    """Parse response data into BeautifulSoup."""
    return BeautifulSoup(response.data, 'html.parser')


# ── Home Page Structure ─────────────────────────────────────────────────

class TestHomePageUI:
    def test_home_has_search_form_element(self, client):
        """Home page contains a <form> with role='search'."""
        s = soup(client.get('/'))
        form = s.find('form', attrs={'role': 'search'})
        assert form is not None

    def test_home_has_surname_input(self, client):
        """Surname text input exists with correct name attribute."""
        s = soup(client.get('/'))
        inp = s.find('input', attrs={'name': 'surname'})
        assert inp is not None
        assert inp.get('type') in ('text', None)

    def test_home_has_record_type_radios(self, client):
        """Record type radio buttons exist for all/officers/soldiers."""
        s = soup(client.get('/'))
        radios = s.find_all('input', attrs={'name': 'record_type', 'type': 'radio'})
        values = {r.get('value') for r in radios}
        assert 'all' in values
        assert 'officers' in values
        assert 'soldiers' in values

    def test_home_has_submit_button(self, client):
        """Search submit button exists."""
        s = soup(client.get('/'))
        btn = s.find('button', attrs={'type': 'submit'})
        assert btn is not None
        assert 'Search' in btn.get_text()


# ── Search Results Structure ────────────────────────────────────────────

class TestSearchResultsUI:
    def test_results_breadcrumb_present(self, client):
        """Results page has breadcrumb nav with Home and Results."""
        s = soup(client.get('/search?surname=SMITH&record_type=soldiers'))
        nav = s.find('nav', attrs={'aria-label': 'Breadcrumb'})
        assert nav is not None
        links = nav.find_all('a')
        assert any('Home' in a.get_text() for a in links)
        current = nav.find(attrs={'aria-current': 'page'})
        assert current is not None
        assert 'Results' in current.get_text()

    def test_results_card_view_structure(self, client):
        """Card view contains article elements with result-card class."""
        s = soup(client.get('/search?surname=SMITH&record_type=soldiers'))
        card_view = s.find('div', id='card-view')
        assert card_view is not None
        cards = card_view.find_all('article', class_='result-card')
        assert len(cards) > 0

    def test_results_table_view_structure(self, client):
        """Table view has proper thead/tbody with correct column headers."""
        s = soup(client.get('/search?surname=SMITH&record_type=soldiers'))
        table_view = s.find('div', id='table-view')
        assert table_view is not None
        table = table_view.find('table', class_='results-table')
        assert table is not None
        headers = [th.get_text(strip=True) for th in table.find('thead').find_all('th')]
        assert 'Name' in headers
        assert 'Rank' in headers
        assert 'Date of Death' in headers

    def test_results_filter_pills_show_active_filters(self, client):
        """Filter pills display for each active search parameter."""
        s = soup(client.get('/search?surname=SMITH&birth_town=LONDON&record_type=soldiers'))
        pills = s.find_all('span', class_='filter-pill')
        pill_texts = [p.get_text() for p in pills]
        assert any('Surname' in t and 'SMITH' in t for t in pill_texts)
        assert any('Birth Town' in t and 'LONDON' in t for t in pill_texts)

    def test_results_sort_dropdown_has_options(self, client):
        """Sort dropdown contains all 5 sort options."""
        s = soup(client.get('/search?surname=SMITH&record_type=soldiers'))
        select = s.find('select', id='sort-select')
        assert select is not None
        options = select.find_all('option')
        assert len(options) == 5
        values = {o.get('value') for o in options}
        assert 'name_asc' in values
        assert 'date_desc' in values
        assert 'rank' in values

    def test_results_sort_preserves_selection(self, client):
        """Selected sort option is marked as selected."""
        s = soup(client.get('/search?surname=SMITH&record_type=soldiers&sort=date_desc'))
        select = s.find('select', id='sort-select')
        selected = select.find('option', selected=True)
        assert selected is not None
        assert selected.get('value') == 'date_desc'

    def test_results_pagination_preserves_search_params(self, client):
        """Pagination links include search parameters."""
        s = soup(client.get('/search?surname=SMITH&record_type=soldiers&page=2'))
        pagination = s.find('nav', attrs={'aria-label': 'Pagination'})
        assert pagination is not None
        links = pagination.find_all('a')
        for link in links:
            href = link.get('href', '')
            assert 'surname=SMITH' in href or 'surname' in href

    def test_results_death_dates_human_readable(self, client):
        """Death dates in results use short human format (e.g. '5 Sep 1915')."""
        s = soup(client.get('/search?surname=SMITH&record_type=soldiers'))
        card_view = s.find('div', id='card-view')
        cards = card_view.find_all('article', class_='result-card')
        for card in cards[:5]:
            date_p = card.find('strong', string='Date of Death:')
            if date_p:
                date_text = date_p.parent.get_text()
                # Should NOT contain ISO format like 1916-07-01
                assert '-' not in date_text.replace('Date of Death:', '').strip() or \
                    len(date_text.replace('Date of Death:', '').strip()) > 10
                break

    def test_results_csv_export_button_present(self, client):
        """Export CSV button/link exists on results page."""
        s = soup(client.get('/search?surname=SMITH&record_type=soldiers'))
        export = s.find('a', id='export-csv-btn')
        assert export is not None
        assert 'Export CSV' in export.get_text()
        assert '/export-csv' in export.get('href', '')

    def test_results_position_tracking_in_detail_links(self, client):
        """Detail links include pos= parameter for record navigation."""
        s = soup(client.get('/search?surname=SMITH&record_type=soldiers'))
        card_view = s.find('div', id='card-view')
        first_link = card_view.find('a', class_='result-link')
        assert first_link is not None
        assert 'pos=0' in first_link.get('href', '')


# ── Detail Page Structure ───────────────────────────────────────────────

class TestDetailPageUI:
    def test_detail_breadcrumb_without_search(self, client):
        """Detail page breadcrumb shows Home > Record Name (no Results)."""
        s = soup(client.get('/record/soldier/1'))
        nav = s.find('nav', attrs={'aria-label': 'Breadcrumb'})
        assert nav is not None
        items = nav.find('ol').find_all('li')
        assert len(items) == 2  # Home, Record name
        assert 'Home' in items[0].get_text()

    def test_detail_breadcrumb_with_search(self, client):
        """Detail page breadcrumb shows Home > Results > Record Name."""
        s = soup(client.get('/record/soldier/1?surname=SMITH&search_type=soldiers&pos=5'))
        nav = s.find('nav', attrs={'aria-label': 'Breadcrumb'})
        items = nav.find('ol').find_all('li')
        assert len(items) == 3  # Home, Results, Record name
        assert 'Results' in items[1].get_text()

    def test_detail_personal_info_section(self, client):
        """Detail page has Personal Information section with name."""
        s = soup(client.get('/record/soldier/1'))
        sections = s.find_all('div', class_='record-section')
        section_titles = [sec.find('h3').get_text(strip=True) for sec in sections if sec.find('h3')]
        assert 'Personal Information' in section_titles

    def test_detail_military_service_section(self, client):
        """Detail page has Military Service section."""
        s = soup(client.get('/record/soldier/1'))
        sections = s.find_all('div', class_='record-section')
        section_titles = [sec.find('h3').get_text(strip=True) for sec in sections if sec.find('h3')]
        assert 'Military Service' in section_titles

    def test_detail_casualty_section(self, client):
        """Detail page has Casualty Information section."""
        s = soup(client.get('/record/soldier/1'))
        sections = s.find_all('div', class_='record-section')
        section_titles = [sec.find('h3').get_text(strip=True) for sec in sections if sec.find('h3')]
        assert 'Casualty Information' in section_titles

    def test_detail_death_date_human_readable(self, client):
        """Death date on detail page uses full human format (e.g. '5 September 1915')."""
        s = soup(client.get('/record/soldier/1'))
        dt_tags = s.find_all('dt')
        for dt in dt_tags:
            if 'Date of Death' in dt.get_text():
                dd = dt.find_next_sibling('dd')
                if dd:
                    date_text = dd.get_text(strip=True)
                    if date_text:
                        # Full month name should be present (not ISO format)
                        months = ['January', 'February', 'March', 'April', 'May', 'June',
                                  'July', 'August', 'September', 'October', 'November', 'December']
                        assert any(m in date_text for m in months), f"Expected human date, got: {date_text}"
                break

    def test_detail_record_navigation_with_search(self, client):
        """Record navigation bar appears with prev/next when search context exists."""
        s = soup(client.get('/record/soldier/1?surname=SMITH&search_type=soldiers&pos=5'))
        nav = s.find('nav', class_='record-nav')
        assert nav is not None
        position = nav.find('span', class_='record-position')
        assert position is not None
        assert 'Record 6 of' in position.get_text()

    def test_detail_no_nav_without_search_context(self, client):
        """Record navigation bar does NOT appear without search context."""
        s = soup(client.get('/record/soldier/1'))
        nav = s.find('nav', class_='record-nav')
        assert nav is None

    def test_detail_related_records_links(self, client):
        """Related records section contains clickable links."""
        s = soup(client.get('/record/soldier/1'))
        related = s.find('section', class_='related-records')
        if related:
            links = related.find_all('a')
            assert len(links) > 0
            for link in links:
                assert '/record/' in link.get('href', '')

    def test_detail_print_button(self, client):
        """Print button exists on detail page."""
        s = soup(client.get('/record/soldier/1'))
        btn = s.find('button', string=lambda t: t and 'Print' in t)
        assert btn is not None


# ── 404 Page ────────────────────────────────────────────────────────────

class TestErrorPageUI:
    def test_404_has_friendly_message(self, client):
        """404 page shows user-friendly message."""
        s = soup(client.get('/record/soldier/999999999'))
        assert 'Page Not Found' in s.get_text() or 'not found' in s.get_text().lower()

    def test_404_has_search_link(self, client):
        """404 page has a link back to search."""
        s = soup(client.get('/record/soldier/999999999'))
        links = s.find_all('a')
        assert any('search' in a.get('href', '').lower() or 'Search' in a.get_text() for a in links)


# ── Accessibility ───────────────────────────────────────────────────────

class TestAccessibilityUI:
    def test_skip_to_main_link_home(self, client):
        """Home page has skip-to-main-content link as first focusable element."""
        s = soup(client.get('/'))
        skip = s.find('a', class_='skip-to-main')
        assert skip is not None
        assert skip.get('href') == '#main-content'

    def test_skip_to_main_link_results(self, client):
        """Results page has skip-to-main-content link."""
        s = soup(client.get('/search?surname=SMITH'))
        skip = s.find('a', class_='skip-to-main')
        assert skip is not None

    def test_aria_landmarks_home(self, client):
        """Home page has banner, main, and contentinfo ARIA landmarks."""
        s = soup(client.get('/'))
        assert s.find(attrs={'role': 'banner'}) is not None
        assert s.find(attrs={'role': 'main'}) is not None
        assert s.find(attrs={'role': 'contentinfo'}) is not None

    def test_aria_landmarks_results(self, client):
        """Results page has banner, main, and contentinfo landmarks."""
        s = soup(client.get('/search?surname=SMITH'))
        assert s.find(attrs={'role': 'banner'}) is not None
        assert s.find(attrs={'role': 'main'}) is not None
        assert s.find(attrs={'role': 'contentinfo'}) is not None

    def test_aria_landmarks_detail(self, client):
        """Detail page has banner, main, and contentinfo landmarks."""
        s = soup(client.get('/record/soldier/1'))
        assert s.find(attrs={'role': 'banner'}) is not None
        assert s.find(attrs={'role': 'main'}) is not None
        assert s.find(attrs={'role': 'contentinfo'}) is not None

    def test_results_view_toggle_has_aria(self, client):
        """View toggle buttons have aria-pressed attributes."""
        s = soup(client.get('/search?surname=SMITH&record_type=soldiers'))
        toggles = s.find_all('button', class_='btn-toggle')
        assert len(toggles) == 2
        for btn in toggles:
            assert btn.get('aria-pressed') in ('true', 'false')

    def test_table_headers_have_scope(self, client):
        """Results table headers have scope='col' for accessibility."""
        s = soup(client.get('/search?surname=SMITH&record_type=soldiers'))
        table = s.find('table', class_='results-table')
        if table:
            headers = table.find('thead').find_all('th')
            for th in headers:
                assert th.get('scope') == 'col'

    def test_breadcrumb_has_aria_label(self, client):
        """Breadcrumb nav has aria-label='Breadcrumb'."""
        s = soup(client.get('/search?surname=SMITH'))
        nav = s.find('nav', attrs={'aria-label': 'Breadcrumb'})
        assert nav is not None


# ── CSV Export Route ────────────────────────────────────────────────────

class TestCSVExportUI:
    def test_csv_export_returns_csv(self, client):
        """CSV export route returns CSV content type."""
        r = client.get('/export-csv?surname=SMITH&record_type=soldiers')
        assert r.status_code == 200
        assert 'text/csv' in r.content_type

    def test_csv_export_has_headers(self, client):
        """CSV export includes column headers."""
        r = client.get('/export-csv?surname=SMITH&record_type=soldiers')
        content = r.data.decode('utf-8-sig')
        first_line = content.split('\n')[0]
        assert 'Surname' in first_line
        assert 'Christian Names' in first_line
        assert 'Date of Death' in first_line

    def test_csv_export_has_data_rows(self, client):
        """CSV export contains data rows."""
        r = client.get('/export-csv?surname=SMITH&record_type=soldiers')
        content = r.data.decode('utf-8-sig')
        lines = [l for l in content.strip().split('\n') if l.strip()]
        assert len(lines) > 1  # Header + at least one data row

    def test_csv_export_filename(self, client):
        """CSV export has correct filename in Content-Disposition."""
        r = client.get('/export-csv?surname=SMITH&record_type=soldiers')
        disposition = r.headers.get('Content-Disposition', '')
        assert 'sdgw_results_' in disposition
        assert '.csv' in disposition
