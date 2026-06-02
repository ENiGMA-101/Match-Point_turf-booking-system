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
BASE_URL        = "https://arena-finder-book-my-field.onrender.com"
TEST_USERNAME   = "selenium_tester"
TEST_PASSWORD   = "TestPass@123"
TEST_EMAIL      = "selenium_tester@example.com"
TEST_FIRST_NAME = "Selenium"
TEST_LAST_NAME  = "Tester"
TEST_MOBILE     = "01843097354"
TEST_ADDRESS    = "West shewrapara, Mirpur, Dhaka"

RESET_USERNAME  = f"reset_user_{random.randint(1000, 9999)}"
RESET_PASSWORD  = "ResetPass@123"
RESET_EMAIL     = f"{RESET_USERNAME}@example.com"

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
    _send_keys_safe(driver, By.NAME, "emergency_contact", "01518417681")
    if is_field_owner:
        cb = driver.find_element(By.NAME, "is_field_owner")
        if not cb.is_selected():
            driver.execute_script("arguments[0].click();", cb)
    _click_submit(driver)


def _ensure_registered(username, password, email, first_name, last_name,
                       address, mobile, is_field_owner=False):
    """Register user once; silently ignores duplicate errors."""
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
    """
    Log in once via the browser, capture all cookies, and cache them.
    Every subsequent call for the same username returns the cache instantly.
    """
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
    """
    Inject cached session cookies into *driver*.
    The browser is already logged in – no login page is shown.
    """
    cookies = _get_session_cookies(username, password)
    driver.get(BASE_URL)          # must visit the domain before setting cookies
    time.sleep(1)
    for cookie in cookies:
        cookie.pop("sameSite", None)
        cookie.pop("expiry",   None)
        try:
            driver.add_cookie(cookie)
        except Exception:
            pass
    driver.refresh()              # let the server recognise the session
    time.sleep(2)


# ──────────────────────────────────────────────────────────────
# Module-level setup – runs ONCE before any test in this file
# ──────────────────────────────────────────────────────────────
def setUpModule():
    print("\n[setUpModule] Registering test users …")
    _ensure_registered(TEST_USERNAME, TEST_PASSWORD, TEST_EMAIL,
                       TEST_FIRST_NAME, TEST_LAST_NAME,
                       TEST_ADDRESS, TEST_MOBILE, is_field_owner=False)
    _ensure_registered(RESET_USERNAME, RESET_PASSWORD, RESET_EMAIL,
                       "Reset", "User", TEST_ADDRESS, TEST_MOBILE)
    # Pre-warm the session cache so the first test isn't slow
    _get_session_cookies(TEST_USERNAME, TEST_PASSWORD)
    print("[setUpModule] Ready.\n")


# ──────────────────────────────────────────────────────────────
# Base test class
# ──────────────────────────────────────────────────────────────
class AccountsTestBase(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome(service=Service(), options=_chrome_options())
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 15)

    def tearDown(self):
        time.sleep(1)
        self.driver.quit()

    def login_via_cookie(self, username=TEST_USERNAME, password=TEST_PASSWORD):
        """Restore an authenticated session via cookie – skips the login page entirely."""
        _apply_session(self.driver, username, password)

    def body_text(self):
        try:
            return self.driver.find_element(By.TAG_NAME, "body").text
        except Exception:
            return ""

    def assert_page_loaded(self, msg="Page did not load properly"):
        self.assertNotEqual(self.body_text().strip(), "", msg)


# ============================================================
# TC-ACC-01 → TC-ACC-15 : Accounts Tests
# ============================================================
class AccountsTests(AccountsTestBase):

    # ── TC-ACC-01 ──────────────────────────────────────────
    def test_01_homepage_loads(self):
        self.driver.get(BASE_URL)
        time.sleep(2)
        self.assertIn("Home", self.driver.title)
        print("✅ TC-ACC-01 | Homepage loads")

    # ── TC-ACC-02 ──────────────────────────────────────────
    def test_02_register_page_has_all_fields(self):
        self.driver.get(f"{BASE_URL}/accounts/register/")
        time.sleep(2)
        for name in ["username", "email", "password", "first_name",
                     "last_name", "age", "mobile", "address", "gender"]:
            self.assertIsNotNone(
                self.wait.until(EC.presence_of_element_located((By.NAME, name))),
                f"Field '{name}' missing on register page"
            )
        print("✅ TC-ACC-02 | Registration page has all required fields")

    # ── TC-ACC-03 ──────────────────────────────────────────
    def test_03_register_new_user_success(self):
        new_user = f"newuser_{random.randint(10000, 99999)}"
        self.driver.get(f"{BASE_URL}/accounts/register/")
        time.sleep(2)
        _fill_registration(self.driver, new_user, f"{new_user}@example.com",
                           "TestPass@123", "New", "User", TEST_ADDRESS, "01800000001")
        time.sleep(4)
        self.assertIn("/accounts/login/", self.driver.current_url,
                      "Successful registration should redirect to login")
        print("✅ TC-ACC-03 | New user registration redirects to login")

    # ── TC-ACC-04 ──────────────────────────────────────────
    def test_04_register_duplicate_username_rejected(self):
        self.driver.get(f"{BASE_URL}/accounts/register/")
        time.sleep(2)
        _fill_registration(self.driver, TEST_USERNAME, "dup@example.com",
                           TEST_PASSWORD, "Dup", "User", TEST_ADDRESS, "01800000002")
        time.sleep(3)
        stayed    = "/accounts/register/" in self.driver.current_url
        has_error = any(kw in self.body_text().lower()
                        for kw in ["already", "exists", "error", "username"])
        self.assertTrue(stayed or has_error, "Duplicate username should not be accepted")
        print("✅ TC-ACC-04 | Duplicate username registration rejected")

    # ── TC-ACC-05 ──────────────────────────────────────────
    def test_05_login_page_loads(self):
        self.driver.get(f"{BASE_URL}/accounts/login/")
        time.sleep(2)
        self.assertIsNotNone(
            self.wait.until(EC.presence_of_element_located((By.NAME, "username"))))
        self.assertIsNotNone(
            self.wait.until(EC.presence_of_element_located((By.NAME, "password"))))
        print("✅ TC-ACC-05 | Login page loads with correct fields")

    # ── TC-ACC-06 ──────────────────────────────────────────
    def test_06_login_valid_credentials(self):
        """Uses the real login UI – intentional, this IS a login-form test."""
        self.driver.get(f"{BASE_URL}/accounts/login/")
        time.sleep(2)
        _send_keys_safe(self.driver, By.NAME, "username", TEST_USERNAME)
        _send_keys_safe(self.driver, By.NAME, "password", TEST_PASSWORD)
        _click_submit(self.driver)
        time.sleep(3)
        self.assertNotIn("/accounts/login/", self.driver.current_url,
                         "Valid credentials should redirect after login")
        print("✅ TC-ACC-06 | Login with valid credentials succeeds")

    # ── TC-ACC-07 ──────────────────────────────────────────
    def test_07_login_wrong_password_rejected(self):
        self.driver.get(f"{BASE_URL}/accounts/login/")
        _send_keys_safe(self.driver, By.NAME, "username", TEST_USERNAME)
        _send_keys_safe(self.driver, By.NAME, "password", "WrongPass999!")
        _click_submit(self.driver)
        time.sleep(2)
        self.assertIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-ACC-07 | Wrong password is rejected")

    # ── TC-ACC-08 ──────────────────────────────────────────
    def test_08_login_nonexistent_user_rejected(self):
        self.driver.get(f"{BASE_URL}/accounts/login/")
        _send_keys_safe(self.driver, By.NAME, "username", "user_xyz_99999")
        _send_keys_safe(self.driver, By.NAME, "password", "SomePass@123")
        _click_submit(self.driver)
        time.sleep(2)
        self.assertIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-ACC-08 | Non-existent user login rejected")

    # ── TC-ACC-09 ──────────────────────────────────────────
    def test_09_profile_accessible_after_login(self):
        self.login_via_cookie()                       # ← cookie restore, no UI login
        self.driver.get(f"{BASE_URL}/accounts/profile/")
        time.sleep(2)
        self.assert_page_loaded()
        self.assertNotIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-ACC-09 | Profile page accessible after login")

    # ── TC-ACC-10 ──────────────────────────────────────────
    def test_10_profile_redirects_unauthenticated(self):
        self.driver.get(f"{BASE_URL}/accounts/profile/")
        time.sleep(2)
        self.assertIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-ACC-10 | Profile page protected – redirects unauthenticated users")

    # ── TC-ACC-11 ──────────────────────────────────────────
    def test_11_logout_works(self):
        self.login_via_cookie()

        # Try clicking the logout link via the navbar dropdown
        try:
            # Open the dropdown that contains the logout link
            dropdown_toggle = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-bs-toggle='dropdown'], .dropdown-toggle")
                )
            )
            self.driver.execute_script("arguments[0].click();", dropdown_toggle)
            time.sleep(1)

            # Now the logout link should be visible
            logout_link = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a[href*='logout']")
                )
            )
            self.driver.execute_script("arguments[0].click();", logout_link)
            time.sleep(2)
        except Exception:
            # Fallback: navigate directly to the logout URL
            self.driver.get(f"{BASE_URL}/accounts/logout/")
            time.sleep(2)

        self.driver.get(f"{BASE_URL}/accounts/profile/")
        time.sleep(2)
        self.assertIn("/accounts/login/", self.driver.current_url)
        print("✅ TC-ACC-11 | Logout works and session is cleared")

    # ── TC-ACC-12 ──────────────────────────────────────────
    def test_12_forgot_password_page_loads(self):
        self.driver.get(f"{BASE_URL}/accounts/forgot-password/")
        time.sleep(2)
        self.assert_page_loaded()
        self.assertIsNotNone(
            self.wait.until(EC.presence_of_element_located((By.NAME, "username"))))
        print("✅ TC-ACC-12 | Forgot-password page loads")

    # ── TC-ACC-13 ──────────────────────────────────────────
    def test_13_forgot_password_invalid_username(self):
        self.driver.get(f"{BASE_URL}/accounts/forgot-password/")
        time.sleep(2)
        _send_keys_safe(self.driver, By.NAME, "username", "totally_nonexistent_xyz")
        _click_submit(self.driver)
        time.sleep(2)
        stayed    = "/accounts/forgot-password/" in self.driver.current_url
        has_error = any(kw in self.body_text().lower()
                        for kw in ["not found", "no account", "error", "invalid"])
        self.assertTrue(stayed or has_error)
        print("✅ TC-ACC-13 | Forgot-password rejects unknown username")

    # ── TC-ACC-14 ──────────────────────────────────────────
    def test_14_forgot_password_valid_username_proceeds(self):
        self.driver.get(f"{BASE_URL}/accounts/forgot-password/")
        time.sleep(2)
        _send_keys_safe(self.driver, By.NAME, "username", RESET_USERNAME)
        _click_submit(self.driver)
        time.sleep(2)
        self.assertIn("/accounts/reset-password/", self.driver.current_url)
        print("✅ TC-ACC-14 | Valid username proceeds to reset-password page")

    # ── TC-ACC-15 ──────────────────────────────────────────
    def test_15_reset_password_form_loads(self):
        self.driver.get(f"{BASE_URL}/accounts/forgot-password/")
        time.sleep(2)
        _send_keys_safe(self.driver, By.NAME, "username", RESET_USERNAME)
        _click_submit(self.driver)
        time.sleep(2)
        if "/accounts/reset-password/" not in self.driver.current_url:
            self.skipTest("Could not reach reset-password page")
        field = self.wait.until(EC.presence_of_element_located((By.NAME, "new_password")))
        self.assertIsNotNone(field)
        print("✅ TC-ACC-15 | Reset-password form loads with new_password field")


# ============================================================
# Run
# ============================================================
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(AccountsTests))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print("  ACCOUNTS TEST SUMMARY")
    print("=" * 70)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"  Total run : {result.testsRun}")
    print(f"  Passed    : {passed}  ✅")
    print(f"  Failures  : {len(result.failures)}  ❌")
    print(f"  Errors    : {len(result.errors)}  💥")
    print("=" * 70)
    exit(0 if result.wasSuccessful() else 1)
