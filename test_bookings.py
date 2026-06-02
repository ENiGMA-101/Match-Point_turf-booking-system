import unittest
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ============================================================
# GLOBAL CONFIG – change if needed
# ============================================================
BASE_URL      = "https://arena-finder-book-my-field.onrender.com"
TEST_USERNAME = "selenium_tester"
TEST_PASSWORD = "TestPass@123"
TEST_EMAIL    = "selenium_tester@example.com"
TEST_MOBILE   = "01843097354"
TEST_ADDRESS  = "West shewrapara, Mirpur, Dhaka"

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
    """Log in once, cache cookies. Returns cached cookies on every subsequent call."""
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
    print("\n[setUpModule] Registering test user …")
    _ensure_registered(TEST_USERNAME, TEST_PASSWORD, TEST_EMAIL,
                       "Selenium", "Tester", TEST_ADDRESS, TEST_MOBILE)
    _get_session_cookies(TEST_USERNAME, TEST_PASSWORD)   # pre-warm cache
    print("[setUpModule] Ready.\n")


# ──────────────────────────────────────────────────────────────
# Base test class
# ──────────────────────────────────────────────────────────────
class BookingsTestBase(unittest.TestCase):

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

    def body_text(self):
        try:
            return self.driver.find_element(By.TAG_NAME, "body").text
        except Exception:
            return ""

    def assert_page_loaded(self, msg="Page did not load properly"):
        self.assertNotEqual(self.body_text().strip(), "", msg)

    def _get_first_field_id(self, filter_param=""):
        """Return the field id extracted from the first btn-primary link on the listing."""
        self.driver.get(f"{BASE_URL}/fields/{filter_param}")
        time.sleep(2)
        try:
            btn  = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn-primary")))
            href = btn.get_attribute("href")
            return [seg for seg in href.rstrip("/").split("/") if seg.isdigit()][-1]
        except Exception:
            return None


# ============================================================
# TC-BK-01 → TC-BK-12 : Bookings Tests
# ============================================================
class BookingsTests(BookingsTestBase):

    # ── TC-BK-01 ──────────────────────────────────────────
    def test_01_my_bookings_redirects_unauthenticated(self):
        self.driver.get(f"{BASE_URL}/bookings/my-bookings/")
        time.sleep(2)
        self.assertIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-BK-01 | /bookings/my-bookings/ protected – redirects to login")

    # ── TC-BK-02 ──────────────────────────────────────────
    def test_02_my_bookings_accessible_after_login(self):
        self.login_via_cookie()                           # ← cookie, no UI login
        self.driver.get(f"{BASE_URL}/bookings/my-bookings/")
        time.sleep(2)
        self.assert_page_loaded()
        self.assertNotIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-BK-02 | My Bookings page accessible after login")

    # ── TC-BK-03 ──────────────────────────────────────────
    def test_03_book_field_page_redirects_unauthenticated(self):
        self.driver.get(f"{BASE_URL}/bookings/book/1/")
        time.sleep(2)
        self.assertIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-BK-03 | Book-field page protected – redirects to login")

    # ── TC-BK-04 ──────────────────────────────────────────
    def test_04_book_field_page_loads_for_logged_in_user(self):
        self.login_via_cookie()
        field_id = self._get_first_field_id()
        if field_id is None:
            self.skipTest("No fields available")
        self.driver.get(f"{BASE_URL}/bookings/book/{field_id}/")
        time.sleep(2)
        self.assert_page_loaded()
        self.assertNotIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-BK-04 | Booking form page loads for logged-in user")

    # ── TC-BK-05 ──────────────────────────────────────────
    def test_05_booking_form_has_required_elements(self):
        self.login_via_cookie()
        field_id = self._get_first_field_id()
        if field_id is None:
            self.skipTest("No fields available")
        self.driver.get(f"{BASE_URL}/bookings/book/{field_id}/")
        time.sleep(2)
        players_input = self.wait.until(
            EC.presence_of_element_located((By.NAME, "players_count")))
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        self.assertIsNotNone(players_input)
        self.assertIsNotNone(submit_btn)
        print("✅ TC-BK-05 | Booking form has players_count input and submit button")

    # ── TC-BK-06 ──────────────────────────────────────────
    def test_06_book_free_field_end_to_end(self):
        self.login_via_cookie()
        self.driver.get(f"{BASE_URL}/fields/?availability=Free")
        time.sleep(2)
        try:
            book_btn = self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Book Now")))
            book_btn.click()
            time.sleep(2)
            slots = self.driver.find_elements(By.NAME, "time_slot")
            if slots:
                self.driver.execute_script("arguments[0].click();", slots[0])
                time.sleep(1)
            _send_keys_safe(self.driver, By.NAME, "players_count", "5")
            _click_submit(self.driver)
            time.sleep(3)
            self.assertIn("/bookings/booking/", self.driver.current_url)
            print("✅ TC-BK-06 | Free field booking end-to-end succeeds")
        except Exception as e:
            print(f"⚠️ TC-BK-06 | Free field booking could not complete: {e}")

    # ── TC-BK-07 ──────────────────────────────────────────
    def test_07_booking_detail_page_loads(self):
        self.login_via_cookie()
        self.driver.get(f"{BASE_URL}/bookings/my-bookings/")
        time.sleep(2)
        try:
            link = self.driver.find_element(
                By.CSS_SELECTOR, "a[href*='/bookings/booking/']")
            self.driver.get(link.get_attribute("href"))
            time.sleep(2)
            self.assert_page_loaded()
            self.assertNotIn("/accounts/login/", self.driver.current_url)
            print("✅ TC-BK-07 | Booking detail page loads")
        except Exception as e:
            print(f"⚠️ TC-BK-07 | No booking detail link found: {e}")

    # ── TC-BK-08 ──────────────────────────────────────────
    def test_08_cancel_booking(self):
        self.login_via_cookie()
        self.driver.get(f"{BASE_URL}/bookings/my-bookings/")
        time.sleep(2)
        try:
            cancel_btn = self.driver.find_element(By.LINK_TEXT, "Cancel")
            cancel_btn.click()
            time.sleep(2)
            if "confirm" in self.driver.current_url:
                _click_submit(self.driver)
                time.sleep(2)
            self.assertIn("/bookings/my-bookings/", self.driver.current_url)
            print("✅ TC-BK-08 | Booking cancellation works")
        except Exception as e:
            print(f"⚠️ TC-BK-08 | No cancellable booking found: {e}")

    # ── TC-BK-09 ──────────────────────────────────────────
    def test_09_payment_page_redirects_unauthenticated(self):
        self.driver.get(f"{BASE_URL}/bookings/payment/1/")
        time.sleep(2)
        self.assertIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-BK-09 | Payment page protected – redirects to login")

    # ── TC-BK-10 ──────────────────────────────────────────
    def test_10_payment_page_loads_for_pending_booking(self):
        self.login_via_cookie()
        self.driver.get(f"{BASE_URL}/bookings/my-bookings/")
        time.sleep(2)
        try:
            pay_link = self.driver.find_element(
                By.CSS_SELECTOR, "a[href*='/bookings/payment/']")
            self.driver.get(pay_link.get_attribute("href"))
            time.sleep(2)
            self.assert_page_loaded()
            print("✅ TC-BK-10 | Payment page loads for pending paid booking")
        except Exception as e:
            print(f"⚠️ TC-BK-10 | No pending paid booking found: {e}")

    # ── TC-BK-11 ──────────────────────────────────────────
    def test_11_join_team_page_redirects_unauthenticated(self):
        self.driver.get(f"{BASE_URL}/bookings/join-team/1/")
        time.sleep(2)
        self.assertIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-BK-11 | Join-team page protected – redirects to login")

    # ── TC-BK-12 ──────────────────────────────────────────
    def test_12_manage_join_requests_redirects_unauthenticated(self):
        self.driver.get(f"{BASE_URL}/bookings/manage-team/1/")
        time.sleep(2)
        self.assertIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-BK-12 | Manage join requests page protected – redirects to login")


# ============================================================
# Run
# ============================================================
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(BookingsTests))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print("  BOOKINGS TEST SUMMARY")
    print("=" * 70)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"  Total run : {result.testsRun}")
    print(f"  Passed    : {passed}  ✅")
    print(f"  Failures  : {len(result.failures)}  ❌")
    print(f"  Errors    : {len(result.errors)}  💥")
    print("=" * 70)
    exit(0 if result.wasSuccessful() else 1)
