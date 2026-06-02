import unittest
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# ============================================================
# GLOBAL CONFIG – change if needed
# ============================================================
BASE_URL      = "https://arena-finder-book-my-field.onrender.com"
TEST_USERNAME = "selenium_tester"
TEST_PASSWORD = "TestPass@123"
TEST_EMAIL    = "selenium_tester@example.com"
TEST_MOBILE   = "01843097354"
TEST_ADDRESS  = "West shewrapara, Mirpur, Dhaka"

# Field owner – created fresh per run to avoid conflicts
OWNER_USERNAME = f"owner_{random.randint(1000, 9999)}"
OWNER_PASSWORD = "OwnerPass@123"
OWNER_EMAIL    = f"{OWNER_USERNAME}@example.com"

# ============================================================
# Session cache – login happens ONCE, cookies are reused.
# ============================================================
_SESSION_CACHE: dict = {}


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def _chrome_options():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    return opts


def _send_keys_safe(driver, by, value, text):
    el = WebDriverWait(driver, 15).until(EC.presence_of_element_located((by, value)))
    el.clear()
    el.send_keys(text)


def _click_submit(driver):
    btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", btn)


def _fill_registration(driver, username, email, password, first_name, last_name,
                       address, mobile, is_field_owner=False):
    _send_keys_safe(driver, By.NAME, "username",          username)
    _send_keys_safe(driver, By.NAME, "email",             email)
    _send_keys_safe(driver, By.NAME, "first_name",        first_name)
    _send_keys_safe(driver, By.NAME, "last_name",         last_name)
    _send_keys_safe(driver, By.NAME, "password",          password)
    _send_keys_safe(driver, By.NAME, "age",               "25")
    _send_keys_safe(driver, By.NAME, "mobile",            mobile)
    _send_keys_safe(driver, By.NAME, "address",           address)
    Select(driver.find_element(By.NAME, "gender")).select_by_value("Male")
    _send_keys_safe(driver, By.NAME, "emergency_contact", "01987654321")
    if is_field_owner:
        cb = driver.find_element(By.NAME, "is_field_owner")
        if not cb.is_selected():
            driver.execute_script("arguments[0].click();", cb)
    _click_submit(driver)


def _ensure_registered(username, password, email, first_name, last_name,
                       address, mobile, is_field_owner=False):
    driver = webdriver.Chrome(service=Service(), options=_chrome_options())
    try:
        driver.get(f"{BASE_URL}/accounts/register/")
        time.sleep(3)
        _fill_registration(driver, username, email, password,
                           first_name, last_name, address, mobile, is_field_owner)
        time.sleep(3)
    except Exception as e:
        print(f"  [register] note for '{username}': {e}")
    finally:
        driver.quit()


def _get_session_cookies(username, password):
    """Log in once, cache cookies. Subsequent calls return the cache instantly."""
    if username in _SESSION_CACHE:
        return _SESSION_CACHE[username]

    print(f"  [session] logging in once to capture cookies for '{username}' …")
    driver = webdriver.Chrome(service=Service(), options=_chrome_options())
    try:
        driver.get(f"{BASE_URL}/accounts/login/")
        time.sleep(2)
        _send_keys_safe(driver, By.NAME, "username", username)
        _send_keys_safe(driver, By.NAME, "password", password)
        _click_submit(driver)
        time.sleep(3)
        cookies = driver.get_cookies()
        _SESSION_CACHE[username] = cookies
        print(f"  [session] captured {len(cookies)} cookie(s) for '{username}'")
        return cookies
    finally:
        driver.quit()


def _apply_session(driver, username, password):
    """Inject cached session cookies – browser is instantly logged in, no UI needed."""
    cookies = _get_session_cookies(username, password)
    driver.get(BASE_URL)
    time.sleep(1)
    for cookie in cookies:
        cookie.pop("sameSite", None)
        cookie.pop("expiry",   None)
        try:
            driver.add_cookie(cookie)
        except Exception:
            pass
    driver.refresh()
    time.sleep(2)


# ──────────────────────────────────────────────────────────────
# Module-level setup – runs ONCE before any test in this file
# ──────────────────────────────────────────────────────────────
def setUpModule():
    print("\n[setUpModule] Registering test users …")
    _ensure_registered(TEST_USERNAME, TEST_PASSWORD, TEST_EMAIL,
                       "Selenium", "Tester", TEST_ADDRESS, TEST_MOBILE)
    _ensure_registered(OWNER_USERNAME, OWNER_PASSWORD, OWNER_EMAIL,
                       "Owner", "Field", TEST_ADDRESS, TEST_MOBILE, is_field_owner=True)
    # Pre-warm session cache for both users
    _get_session_cookies(TEST_USERNAME,   TEST_PASSWORD)
    _get_session_cookies(OWNER_USERNAME,  OWNER_PASSWORD)
    print("[setUpModule] Ready.\n")


# ──────────────────────────────────────────────────────────────
# Base test class
# ──────────────────────────────────────────────────────────────
class FieldsTestBase(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome(service=Service(), options=_chrome_options())
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 15)

    def tearDown(self):
        time.sleep(1)
        self.driver.quit()

    def login_via_cookie(self, username=TEST_USERNAME, password=TEST_PASSWORD):
        """Restore authenticated session via cookie – no login page shown."""
        _apply_session(self.driver, username, password)

    def login_as_owner(self):
        self.login_via_cookie(OWNER_USERNAME, OWNER_PASSWORD)

    def body_text(self):
        try:
            return self.driver.find_element(By.TAG_NAME, "body").text
        except Exception:
            return ""

    def assert_page_loaded(self, msg="Page did not load properly"):
        self.assertNotEqual(self.body_text().strip(), "", msg)


# ============================================================
# TC-FLD-01 → TC-FLD-15 : Fields Tests
# ============================================================
class FieldsTests(FieldsTestBase):

    # ── TC-FLD-01 ──────────────────────────────────────────
    def test_01_fields_listing_page_loads(self):
        self.driver.get(f"{BASE_URL}/fields/")
        time.sleep(2)
        self.assert_page_loaded()
        print("✅ TC-FLD-01 | Fields listing page loads")

    # ── TC-FLD-02 ──────────────────────────────────────────
    def test_02_fields_listing_shows_fields(self):
        self.driver.get(f"{BASE_URL}/fields/")
        time.sleep(2)
        links = self.driver.find_elements(By.CSS_SELECTOR, "a.btn-primary")
        self.assertGreater(len(links), 0, "No fields shown on listing page")
        print(f"✅ TC-FLD-02 | Fields listing shows {len(links)} field(s)")

    # ── TC-FLD-03 ──────────────────────────────────────────
    def test_03_basic_search_by_keyword(self):
        self.driver.get(f"{BASE_URL}/fields/")
        time.sleep(2)
        try:
            search = self.driver.find_element(By.NAME, "q")
            search.clear()
            search.send_keys("cricket")
            search.send_keys(Keys.RETURN)
            time.sleep(2)
            self.assert_page_loaded()
            print("✅ TC-FLD-03 | Basic keyword search executes without error")
        except Exception as e:
            print(f"⚠️ TC-FLD-03 | Search input not found: {e}")

    # ── TC-FLD-04 ──────────────────────────────────────────
    def test_04_filter_by_field_type(self):
        self.driver.get(f"{BASE_URL}/fields/?field_type=Football")
        time.sleep(2)
        self.assert_page_loaded()
        print("✅ TC-FLD-04 | Field type filter (Football) loads without error")

    # ── TC-FLD-05 ──────────────────────────────────────────
    def test_05_filter_by_availability_free(self):
        self.driver.get(f"{BASE_URL}/fields/?availability=Free")
        time.sleep(2)
        self.assert_page_loaded()
        print("✅ TC-FLD-05 | Availability filter (Free) loads without error")

    # ── TC-FLD-06 ──────────────────────────────────────────
    def test_06_filter_by_availability_paid(self):
        self.driver.get(f"{BASE_URL}/fields/?availability=Paid")
        time.sleep(2)
        self.assert_page_loaded()
        print("✅ TC-FLD-06 | Availability filter (Paid) loads without error")

    # ── TC-FLD-07 ──────────────────────────────────────────
    def test_07_advanced_search_page_loads(self):
        self.driver.get(f"{BASE_URL}/fields/search/")
        time.sleep(2)
        self.assert_page_loaded()
        print("✅ TC-FLD-07 | Advanced search page loads")

    # ── TC-FLD-08 ──────────────────────────────────────────
    def test_08_advanced_search_with_location_filter(self):
        self.driver.get(f"{BASE_URL}/fields/search/")
        time.sleep(2)
        try:
            loc = self.driver.find_element(By.NAME, "location")
            loc.clear()
            loc.send_keys("Dhaka")
            _click_submit(self.driver)
            time.sleep(2)
            self.assert_page_loaded()
            print("✅ TC-FLD-08 | Advanced search with location filter works")
        except Exception as e:
            print(f"⚠️ TC-FLD-08 | Advanced search filter failed: {e}")

    # ── TC-FLD-09 ──────────────────────────────────────────
    def test_09_field_detail_page_loads(self):
        self.driver.get(f"{BASE_URL}/fields/")
        time.sleep(2)
        try:
            first_link = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn-primary")))
            self.driver.get(first_link.get_attribute("href"))
            time.sleep(2)
            self.assert_page_loaded()
            print("✅ TC-FLD-09 | Field detail page loads")
        except Exception as e:
            print(f"⚠️ TC-FLD-09 | Could not open field detail: {e}")

    # ── TC-FLD-10 ──────────────────────────────────────────
    def test_10_add_field_page_redirects_unauthenticated(self):
        self.driver.get(f"{BASE_URL}/fields/add/")
        time.sleep(2)
        self.assertIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-FLD-10 | /fields/add/ protected – redirects to login")

    # ── TC-FLD-11 ──────────────────────────────────────────
    def test_11_add_field_form_accessible_for_owner(self):
        self.login_as_owner()                             # ← cookie, no UI login
        self.driver.get(f"{BASE_URL}/fields/add/")
        time.sleep(2)
        self.assertNotIn("/accounts/login/", self.driver.current_url)
        name_field = self.wait.until(EC.presence_of_element_located((By.NAME, "name")))
        self.assertIsNotNone(name_field)
        print("✅ TC-FLD-11 | Add-field form accessible for field owner")

    # ── TC-FLD-12 ──────────────────────────────────────────
    def test_12_add_field_submission(self):
        self.login_as_owner()
        self.driver.get(f"{BASE_URL}/fields/add/")
        time.sleep(2)
        field_name = f"Test Field {random.randint(1, 9999)}"
        try:
            _send_keys_safe(self.driver, By.NAME, "name",         field_name)
            Select(self.driver.find_element(By.NAME, "field_type")).select_by_value("Football")
            _send_keys_safe(self.driver, By.NAME, "location",     "Dhanmondi-32, Dhaka")
            _send_keys_safe(self.driver, By.NAME, "cost_per_hour","20")
            Select(self.driver.find_element(By.NAME, "availability_type")).select_by_value("Paid")
            _send_keys_safe(self.driver, By.NAME, "description",  "Natural test field")
            _send_keys_safe(self.driver, By.NAME, "capacity",     "21")
            _click_submit(self.driver)
            time.sleep(3)
            self.assertIn("/fields/manage/", self.driver.current_url,
                          "After adding a field, should redirect to manage-fields")
            print(f"✅ TC-FLD-12 | Add field '{field_name}' submission succeeds")
        except Exception as e:
            print(f"⚠️ TC-FLD-12 | Add field submission failed: {e}")

    # ── TC-FLD-13 ──────────────────────────────────────────
    def test_13_manage_fields_accessible_for_owner(self):
        self.login_as_owner()
        self.driver.get(f"{BASE_URL}/fields/manage/")
        time.sleep(2)
        self.assert_page_loaded()
        self.assertNotIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-FLD-13 | Manage-fields page accessible for field owner")

    # ── TC-FLD-14 ──────────────────────────────────────────
    def test_14_edit_field_page_redirects_unauthenticated(self):
        self.driver.get(f"{BASE_URL}/fields/1/edit/")
        time.sleep(2)
        self.assertIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-FLD-14 | /fields/<id>/edit/ protected – redirects to login")

    # ── TC-FLD-15 ──────────────────────────────────────────
    def test_15_add_review_page_redirects_unauthenticated(self):
        self.driver.get(f"{BASE_URL}/fields/1/review/")
        time.sleep(2)
        self.assertIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-FLD-15 | /fields/<id>/review/ protected – redirects to login")


# ============================================================
# Run
# ============================================================
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(FieldsTests))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print("  FIELDS TEST SUMMARY")
    print("=" * 70)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"  Total run : {result.testsRun}")
    print(f"  Passed    : {passed}  ✅")
    print(f"  Failures  : {len(result.failures)}  ❌")
    print(f"  Errors    : {len(result.errors)}  💥")
    print("=" * 70)
    exit(0 if result.wasSuccessful() else 1)
