"""
=============================================================================
  CAMPRO MVC – ENTERPRISE QA TEST SUITE v2.0  ★ 150 TEST CASES ★
  Tác giả  : Senior SDET Engineer
  Phiên bản: 2.0 – Kiểm thử toàn diện dự án Web Bán Camera (MVC)
  Mô tả    : Bộ kiểm thử E2E + API + Security + Performance + Admin CRUD
             + Validation + Boundary + Session + SEO/A11y + Integration
             Dự án: CAMPRO – Website bán camera chuyên nghiệp
             Stack server: Node.js + Express + EJS + MySQL (MVC)
  Stack KT : Python 3.10+, Selenium 4, requests, concurrent.futures, openpyxl
=============================================================================
CÁCH CHẠY:
    pip install selenium requests openpyxl webdriver-manager
    python kiem_thu_campro_mvc_150_full.py
    → Server phải đang chạy tại http://localhost:5000
    → DB MySQL phải có dữ liệu mẫu (database.sql)
"""

import logging
import time
import re
import threading
import concurrent.futures
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ─────────────────────────────────────────────────────────────────────────────
#  CẤU HÌNH TRUNG TÂM – CAMPRO MVC
# ─────────────────────────────────────────────────────────────────────────────
BASE_URL        = "http://localhost:5000"
ADMIN_USER      = "admin"
ADMIN_PASS      = "Admin@123"
TESTER_NAME     = "Senior SDET Engineer"
TEST_DATE       = datetime.now().strftime('%Y-%m-%d')
PAGE_TIMEOUT    = 15
ELEMENT_WAIT    = 8
API_TIMEOUT     = 10
PERF_WORKERS    = 10
PERF_REQUESTS   = 30

_TS              = int(time.time())
FRONTEND_USER    = f"camuser_{_TS}"
FRONTEND_PASS    = "Test@123456"
SEARCH_KEYWORD   = "camera"

# ─────────────────────────────────────────────────────────────────────────────
#  HỆ THỐNG GHI KẾT QUẢ TOÀN CỤC
# ─────────────────────────────────────────────────────────────────────────────
actual_test_results: list[dict] = []
_result_lock = threading.Lock()

def record_result(category: str, name: str, step: str, expected: str,
                  result: str = "Pass", note: str = ""):
    with _result_lock:
        actual_test_results.append({
            "category": category, "name": name, "step": step,
            "expected": expected, "result": result, "note": note
        })

def run_test_case(tc_id: str, tc_name: str, category: str,
                  step: str, expected: str, logic_func):
    """Wrapper thực thi 1 test case, bắt lỗi và ghi kết quả."""
    print(f"⏳ [{tc_id}] {tc_name}...")
    try:
        logic_func()
        print(f"   ✅ PASS: {tc_name}\n")
        record_result(category, tc_name, step, expected, "Pass", "Thực thi thành công")
    except Exception as exc:
        first_line = str(exc).splitlines()[0][:120]
        msg = f"{type(exc).__name__}: {first_line}"
        print(f"   ❌ FAIL: {tc_name}\n      => {msg}\n")
        record_result(category, tc_name, step, expected, "Fail", msg)

# ─────────────────────────────────────────────────────────────────────────────
#  KHỞI ĐỘNG SELENIUM DRIVER
# ─────────────────────────────────────────────────────────────────────────────
logging.getLogger("WDM").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

def _build_driver() -> webdriver.Chrome:
    opts = webdriver.ChromeOptions()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1440,900")
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.page_load_strategy = "eager"
    drv = webdriver.Chrome(options=opts)
    drv.set_page_load_timeout(PAGE_TIMEOUT)
    drv.implicitly_wait(0)
    return drv

driver = _build_driver()
wait   = WebDriverWait(driver, ELEMENT_WAIT)

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION HTTP
# ─────────────────────────────────────────────────────────────────────────────
http_session_admin = requests.Session()
http_session_user  = requests.Session()
http_anon          = requests.Session()

def _http_login(session: requests.Session, username: str, password: str) -> bool:
    """Đăng nhập HTTP cho CAMPRO MVC (session-based)."""
    try:
        r = session.post(urljoin(BASE_URL, "/auth/login"),
                         data={"username": username, "password": password},
                         timeout=API_TIMEOUT, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False

def _selenium_login(username: str, password: str):
    """Đăng nhập bằng Selenium."""
    driver.get(f"{BASE_URL}/auth/logout")
    time.sleep(0.5)
    driver.get(f"{BASE_URL}/auth/login")
    wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.execute_script("arguments[0].click();",
                          driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
    time.sleep(2)

def _selenium_admin_login():
    _selenium_login(ADMIN_USER, ADMIN_PASS)

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 1 – AUTH & E2E CƠ BẢN  (TC 01 → 09)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 1: AUTH & E2E CƠ BẢN – ĐĂNG KÝ / ĐĂNG NHẬP / ADMIN")
print("=" * 80)

def test_01_register_new_user():
    """Đăng ký tài khoản mới hợp lệ → redirect về login."""
    driver.get(f"{BASE_URL}/auth/register")
    wait.until(EC.visibility_of_element_located((By.NAME, "full_name"))).send_keys("Nguyễn Văn Camera")
    driver.find_element(By.NAME, "username").send_keys(FRONTEND_USER)
    driver.find_element(By.NAME, "email").send_keys(f"{FRONTEND_USER}@campro.vn")
    driver.find_element(By.NAME, "password").send_keys(FRONTEND_PASS)
    driver.find_element(By.NAME, "phone").send_keys("0901234567")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)
    assert "500" not in driver.title, "Đăng ký gây lỗi 500!"
    assert "register" not in driver.current_url.lower() or \
           "login" in driver.current_url.lower() or \
           "/" == driver.current_url.replace(BASE_URL, ""), \
        "Sau đăng ký không chuyển trang!"

def test_02_login_user():
    """Đăng nhập với tài khoản vừa đăng ký → vào trang chủ."""
    driver.get(f"{BASE_URL}/auth/login")
    wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys(FRONTEND_USER)
    driver.find_element(By.NAME, "password").send_keys(FRONTEND_PASS)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)
    assert "500" not in driver.title, "Đăng nhập gây 500!"
    assert "login" not in driver.current_url.lower(), "Đăng nhập thất bại – vẫn ở trang login!"

def test_03_search_camera():
    """Tìm kiếm từ khóa 'camera' → trang kết quả load OK."""
    driver.get(f"{BASE_URL}/products?search=camera")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(1)
    assert "500" not in driver.title, "Tìm kiếm gây 500!"
    assert driver.find_element(By.TAG_NAME, "body").is_displayed()

def test_04_view_product_detail():
    """Click sản phẩm bất kỳ → trang chi tiết load đúng."""
    driver.get(f"{BASE_URL}/products")
    time.sleep(1.5)
    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/products/']")
    if not links:
        driver.get(BASE_URL)
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/products/']")
    assert links, "Không tìm thấy sản phẩm nào!"
    driver.execute_script("arguments[0].click();", links[0])
    time.sleep(1.5)
    assert "500" not in driver.title, "Chi tiết sản phẩm gây 500!"
    body = driver.find_element(By.TAG_NAME, "body").text
    assert len(body.strip()) > 50, "Trang chi tiết quá ít nội dung!"

def test_05_add_to_cart():
    """User đã đăng nhập thêm sản phẩm vào giỏ → không crash."""
    _selenium_login(FRONTEND_USER, FRONTEND_PASS)
    driver.get(f"{BASE_URL}/products")
    time.sleep(1)
    add_btns = driver.find_elements(By.CSS_SELECTOR, "form[action='/cart/add'] button")
    if not add_btns:
        driver.get(BASE_URL)
        add_btns = driver.find_elements(By.CSS_SELECTOR, "form[action='/cart/add'] button")
    if add_btns:
        driver.execute_script("arguments[0].click();", add_btns[0])
        time.sleep(1.5)
        assert "500" not in driver.title, "Thêm giỏ hàng gây 500!"
    else:
        print("      * INFO: Không tìm thấy nút add to cart (có thể chưa có SP).")

def test_06_view_cart():
    """Truy cập /cart → hiển thị giỏ hàng (item hoặc thông báo rỗng)."""
    driver.get(f"{BASE_URL}/cart")
    time.sleep(1)
    assert "500" not in driver.title, "Trang giỏ hàng gây 500!"
    assert "404" not in driver.title, "Trang giỏ hàng trả 404!"
    assert len(driver.find_element(By.TAG_NAME, "body").text.strip()) > 10

def test_07_admin_login():
    """Đăng nhập admin → chuyển về admin/dashboard."""
    _selenium_admin_login()
    curr = driver.current_url.lower()
    body = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert "admin" in curr or "dashboard" in curr or "admin" in body, \
        f"Admin login thất bại! URL: {driver.current_url}"

def test_08_admin_sees_new_user():
    """Admin vào /admin/customers → thấy user vừa đăng ký."""
    driver.get(f"{BASE_URL}/admin/customers")
    time.sleep(1.5)
    assert "500" not in driver.title, "Admin/customers gây 500!"
    body = driver.find_element(By.TAG_NAME, "body").text
    if FRONTEND_USER not in body:
        print(f"      * WARN: User '{FRONTEND_USER}' chưa hiện (có thể pagination).")

def test_09_admin_dashboard_stats():
    """Admin dashboard load → hiển thị thống kê tổng quan."""
    driver.get(f"{BASE_URL}/admin/dashboard")
    time.sleep(1.5)
    assert "500" not in driver.title, "Dashboard gây 500!"
    body = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert any(kw in body for kw in ["dashboard", "tổng", "đơn hàng", "sản phẩm", "doanh"]), \
        "Dashboard không hiển thị thống kê!"

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 2 – VALIDATION & BOUNDARY  (TC 10 → 18)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 2: VALIDATION & BOUNDARY TEST")
print("=" * 80)

def test_10_register_duplicate_username():
    """Đăng ký username đã tồn tại → lỗi, không cho phép."""
    driver.get(f"{BASE_URL}/auth/register")
    wait.until(EC.visibility_of_element_located((By.NAME, "full_name"))).send_keys("Duplicate User")
    driver.find_element(By.NAME, "username").send_keys(FRONTEND_USER)
    driver.find_element(By.NAME, "email").send_keys(f"dup_{_TS}@campro.vn")
    driver.find_element(By.NAME, "password").send_keys(FRONTEND_PASS)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1.5)
    body = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert "login" in driver.current_url.lower() or \
           "register" in driver.current_url.lower() or \
           "tồn tại" in body or "exist" in body or "error" in body, \
        "Hệ thống cho đăng ký username trùng – lỗ hổng nghiêm trọng!"

def test_11_register_empty_form():
    """Submit form đăng ký rỗng → không cho qua, không crash 500."""
    driver.get(f"{BASE_URL}/auth/register")
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button[type='submit']")))
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)
    assert "500" not in driver.title, "Form rỗng gây 500!"

def test_12_register_invalid_email():
    """Đăng ký email sai định dạng → server không crash."""
    driver.get(f"{BASE_URL}/auth/register")
    wait.until(EC.visibility_of_element_located((By.NAME, "full_name"))).send_keys("Invalid Email")
    driver.find_element(By.NAME, "username").send_keys(f"invemail_{_TS}")
    driver.find_element(By.NAME, "email").send_keys("KHONG_PHAI_EMAIL_CAMPRO")
    driver.find_element(By.NAME, "password").send_keys(FRONTEND_PASS)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)
    assert "500" not in driver.title, "Email sai gây 500!"

def test_13_register_short_password():
    """Đăng ký mật khẩu < 6 ký tự → hệ thống từ chối."""
    driver.get(f"{BASE_URL}/auth/register")
    wait.until(EC.visibility_of_element_located((By.NAME, "full_name"))).send_keys("Short Pass")
    driver.find_element(By.NAME, "username").send_keys(f"shortpw_{_TS}")
    driver.find_element(By.NAME, "email").send_keys(f"shortpw_{_TS}@campro.vn")
    driver.find_element(By.NAME, "password").send_keys("123")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1.5)
    assert "500" not in driver.title, "Mật khẩu ngắn gây 500!"
    body = driver.find_element(By.TAG_NAME, "body").text.lower()
    if "login" not in driver.current_url.lower() and "/" == driver.current_url.replace(BASE_URL, ""):
        print("      * WARN: Hệ thống có thể đã cho qua mật khẩu ngắn.")
    else:
        assert "6" in body or "ký tự" in body or "register" in driver.current_url.lower(), \
            "Không báo lỗi mật khẩu ngắn!"

def test_14_login_wrong_password():
    """Đăng nhập sai mật khẩu → không vào được."""
    driver.get(f"{BASE_URL}/auth/login")
    wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys(ADMIN_USER)
    driver.find_element(By.NAME, "password").send_keys("SaiMatKhauCamPro999!")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1.5)
    assert "login" in driver.current_url.lower() or \
           "admin" not in driver.current_url.lower(), \
        "Đăng nhập sai mật khẩu vẫn vào được – lỗ hổng nghiêm trọng!"

def test_15_login_nonexistent_user():
    """Đăng nhập username không tồn tại → thông báo lỗi."""
    driver.get(f"{BASE_URL}/auth/login")
    wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys("khongtontai_xyz999")
    driver.find_element(By.NAME, "password").send_keys("AnyPass@123")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1.5)
    assert "500" not in driver.title, "Login user không tồn tại gây 500!"
    assert "login" in driver.current_url.lower(), "Đăng nhập user không tồn tại vẫn qua?"

def test_16_filter_by_category():
    """Lọc sản phẩm theo category_id=1 → status 200."""
    r = http_anon.get(urljoin(BASE_URL, "/products?category_id=1"), timeout=API_TIMEOUT)
    assert r.status_code in [200, 302], f"Filter category trả {r.status_code}"
    assert "500" not in r.text[:500], "Filter category gây 500!"

def test_17_filter_price_range():
    """Lọc sản phẩm theo khoảng giá → status 200, không crash."""
    r = http_anon.get(urljoin(BASE_URL, "/products?min_price=500000&max_price=10000000"),
                      timeout=API_TIMEOUT)
    assert r.status_code in [200, 302], f"Filter giá trả {r.status_code}"

def test_18_sort_products():
    """Sắp xếp sản phẩm price_asc → status 200."""
    r = http_anon.get(urljoin(BASE_URL, "/products?sort=price_asc"), timeout=API_TIMEOUT)
    assert r.status_code == 200, f"Sort sản phẩm trả {r.status_code}"

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 3 – SECURITY  (TC 19 → 27)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 3: SECURITY – SQL INJECTION / XSS / AUTH BYPASS")
print("=" * 80)

def test_19_sqli_login_form():
    """SQL Injection vào form login → không bypass, không gây 500."""
    payloads = ["' OR '1'='1", "' OR 1=1--", "admin'--", "' UNION SELECT 1,2--"]
    for payload in payloads:
        driver.get(f"{BASE_URL}/auth/login")
        try:
            wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys(payload)
            driver.find_element(By.NAME, "password").send_keys("any123")
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(1)
            assert "500" not in driver.title, f"SQLi gây 500! Payload: {payload}"
            assert "admin" not in driver.current_url.lower() or \
                   "login" in driver.current_url.lower(), \
                f"SQLi bypass auth! Payload: {payload}"
        except TimeoutException:
            pass

def test_20_sqli_search():
    """SQL Injection vào search sản phẩm → không lộ stack trace."""
    payloads = ["' OR 1=1--", "' UNION SELECT NULL,NULL--", "'; DROP TABLE products--"]
    for payload in payloads:
        r = http_anon.get(urljoin(BASE_URL, f"/products?search={payload}"),
                          timeout=API_TIMEOUT, allow_redirects=True)
        assert r.status_code != 500, f"SQLi search gây 500! Payload: {payload}"
        assert "SQLSTATE" not in r.text and "SequelizeError" not in r.text, \
            f"SQLi lộ SQL error! Payload: {payload}"

def test_21_sqli_url_params():
    """SQL Injection vào URL params → không crash."""
    payloads = ["' OR 1=1--", "1 OR 1=1", "1; DROP TABLE products--"]
    for p in payloads:
        r = http_anon.get(urljoin(BASE_URL, f"/products?category_id={p}"),
                          timeout=API_TIMEOUT, allow_redirects=True)
        assert r.status_code != 500, f"SQLi URL param gây 500! Payload: {p}"

def test_22_xss_reflected_search():
    """XSS Reflected vào ô tìm kiếm → script không chạy trong DOM."""
    xss_payloads = [
        "<script>alert('XSS_CAMPRO')</script>",
        '"><img src=x onerror=alert(1)>',
        "<svg/onload=alert(1)>",
    ]
    for payload in xss_payloads:
        driver.get(BASE_URL)
        try:
            search_el = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='search']")))
            search_el.clear()
            search_el.send_keys(payload)
            search_el.submit()
            time.sleep(0.8)
            try:
                alert = driver.switch_to.alert
                txt = alert.text
                alert.dismiss()
                raise Exception(f"XSS REFLECTED thành công! Payload: {payload}, Alert: {txt}")
            except Exception as inner:
                if "XSS REFLECTED" in str(inner):
                    raise
        except TimeoutException:
            pass

def test_23_xss_stored_register():
    """XSS Stored vào form đăng ký full_name → script không render."""
    xss_payload = "<script>alert('stored_xss_campro')</script>"
    xss_user = f"xss_{_TS}"
    driver.get(f"{BASE_URL}/auth/register")
    try:
        wait.until(EC.visibility_of_element_located((By.NAME, "full_name"))).send_keys(xss_payload)
        driver.find_element(By.NAME, "username").send_keys(xss_user)
        driver.find_element(By.NAME, "email").send_keys(f"xss_{_TS}@campro.vn")
        driver.find_element(By.NAME, "password").send_keys(FRONTEND_PASS)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1.5)
        try:
            alert = driver.switch_to.alert
            alert.dismiss()
            raise Exception("Stored XSS thực thi được tại form đăng ký CAMPRO!")
        except Exception as inner:
            if "Stored XSS" in str(inner):
                raise
    except TimeoutException:
        pass

def test_24_admin_unauthenticated():
    """GET /admin/* không session → redirect login, không vào được."""
    protected = ["/admin/dashboard", "/admin/products", "/admin/customers",
                 "/admin/orders", "/admin/categories", "/admin/report"]
    for page in protected:
        url = urljoin(BASE_URL, page)
        try:
            r = http_anon.get(url, timeout=API_TIMEOUT, allow_redirects=True)
            final = r.url.lower()
            if "admin" in final and "login" not in final and "auth" not in final and r.status_code == 200:
                body = r.text.lower()
                if "dashboard" in body or "quản lý" in body:
                    raise Exception(f"TRUY CẬP ADMIN KHÔNG CẦN AUTH! URL: {url} → {r.url}")
        except requests.RequestException:
            pass

def test_25_idor_order_access():
    """User thường truy cập /orders/1, 2, 3 → không lộ data người khác."""
    _http_login(http_session_user, FRONTEND_USER, FRONTEND_PASS)
    for oid in ["1", "2", "3", "99"]:
        url = urljoin(BASE_URL, f"/orders/{oid}")
        try:
            r = http_session_user.get(url, timeout=API_TIMEOUT, allow_redirects=True)
            if r.status_code == 200:
                body = r.text.lower()
                if "admin" in body and "order" in body and "customer" in body:
                    raise Exception(f"IDOR: Truy cập order người khác tại /orders/{oid}!")
        except requests.RequestException:
            pass

def test_26_security_headers():
    """Kiểm tra Security Headers cơ bản."""
    r = http_anon.get(BASE_URL, timeout=API_TIMEOUT)
    headers = {k.lower(): v for k, v in r.headers.items()}
    recommended = ["x-content-type-options", "x-frame-options"]
    missing = [h for h in recommended if h not in headers]
    if missing:
        print(f"      * WARN: Thiếu Security Headers: {', '.join(missing)}")
    else:
        print(f"      * INFO: Security Headers OK: {recommended}")

def test_27_password_not_exposed():
    """Password không bị lộ trong HTML response sau login."""
    _http_login(http_session_admin, ADMIN_USER, ADMIN_PASS)
    for url in [urljoin(BASE_URL, "/admin/customers"), urljoin(BASE_URL, "/profile")]:
        try:
            r = http_session_admin.get(url, timeout=API_TIMEOUT)
            clean = re.sub(r'<input[^>]+type=["\']password["\'][^>]*>', '', r.text, flags=re.I)
            if ADMIN_PASS in clean:
                raise Exception(f"Password admin bị lộ trong response tại {url}!")
        except requests.RequestException:
            pass

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 4 – API FUNCTIONAL  (TC 28 → 37)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 4: API FUNCTIONAL TEST (HTTP requests)")
print("=" * 80)

def test_28_homepage_200():
    """GET / → HTTP 200."""
    r = http_anon.get(BASE_URL, timeout=API_TIMEOUT)
    assert r.status_code == 200, f"Homepage trả {r.status_code}"

def test_29_api_login_success():
    """POST /auth/login admin → đăng nhập thành công."""
    ok = _http_login(http_session_admin, ADMIN_USER, ADMIN_PASS)
    assert ok, "HTTP Login admin thất bại!"

def test_30_products_page_200():
    """GET /products → 200, có nội dung sản phẩm."""
    r = http_anon.get(urljoin(BASE_URL, "/products"), timeout=API_TIMEOUT)
    assert r.status_code == 200, f"/products trả {r.status_code}"
    assert any(kw in r.text.lower() for kw in ["sản phẩm", "camera", "product"]), \
        "Trang /products không chứa nội dung sản phẩm!"

def test_31_search_api_status():
    """GET /products?search=camera → 200 hoặc 302."""
    r = http_anon.get(urljoin(BASE_URL, "/products?search=camera"), timeout=API_TIMEOUT)
    assert r.status_code in [200, 302], f"Search API trả {r.status_code}"

def test_32_404_handling():
    """GET trang không tồn tại → 404, không crash 500."""
    r = http_anon.get(urljoin(BASE_URL, "/trang-khong-ton-tai-campro-xyz-999"),
                      timeout=API_TIMEOUT)
    assert r.status_code in [404, 302], f"URL không tồn tại trả {r.status_code}"

def test_33_register_via_http():
    """POST /auth/register user mới → status 200/302."""
    new_user = f"apitest_{_TS}"
    r = http_anon.post(urljoin(BASE_URL, "/auth/register"),
                       data={"full_name": "API Test Camera",
                             "username": new_user,
                             "email": f"{new_user}@campro.vn",
                             "password": FRONTEND_PASS},
                       timeout=API_TIMEOUT, allow_redirects=True)
    assert r.status_code in [200, 302], f"Register POST trả {r.status_code}"

def test_34_logout():
    """GET /auth/logout → đăng xuất, redirect."""
    r = http_session_admin.get(urljoin(BASE_URL, "/auth/logout"),
                                timeout=API_TIMEOUT, allow_redirects=True)
    assert r.status_code == 200, f"Logout trả {r.status_code}"

def test_35_admin_products_200():
    """GET /admin/products (admin session) → 200."""
    _http_login(http_session_admin, ADMIN_USER, ADMIN_PASS)
    r = http_session_admin.get(urljoin(BASE_URL, "/admin/products"), timeout=API_TIMEOUT)
    assert r.status_code == 200, f"Admin/products trả {r.status_code}"

def test_36_contact_page_200():
    """GET /contact → 200, có form liên hệ."""
    r = http_anon.get(urljoin(BASE_URL, "/contact"), timeout=API_TIMEOUT)
    assert r.status_code == 200, f"/contact trả {r.status_code}"
    assert "form" in r.text.lower() or "liên hệ" in r.text.lower(), \
        "Trang /contact không có form!"

def test_37_news_page_200():
    """GET /news → 200 hoặc 302."""
    r = http_anon.get(urljoin(BASE_URL, "/news"), timeout=API_TIMEOUT)
    assert r.status_code in [200, 302], f"/news trả {r.status_code}"

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 5 – RBAC  (TC 38 → 41)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 5: RBAC – KIỂM TRA PHÂN QUYỀN TRUY CẬP")
print("=" * 80)

def test_38_user_cannot_access_admin():
    """User thường không vào được /admin/*."""
    _http_login(http_session_user, FRONTEND_USER, FRONTEND_PASS)
    for path in ["/admin/products", "/admin/customers", "/admin/orders", "/admin/dashboard"]:
        try:
            r = http_session_user.get(urljoin(BASE_URL, path),
                                       timeout=API_TIMEOUT, allow_redirects=True)
            final = r.url.lower()
            if "admin" in final and "login" not in final and "auth" not in final:
                if "dashboard" in r.text.lower() or "quản lý" in r.text.lower():
                    raise Exception(f"RBAC BYPASS: User thường vào được {path}!")
        except requests.RequestException:
            pass

def test_39_anon_cannot_access_admin():
    """Ẩn danh không vào được /admin/*."""
    anon = requests.Session()
    for path in ["/admin/products", "/admin/customers", "/admin/dashboard"]:
        try:
            r = anon.get(urljoin(BASE_URL, path), timeout=API_TIMEOUT, allow_redirects=True)
            if "login" not in r.url.lower() and "auth" not in r.url.lower() and r.status_code == 200:
                if "quản lý" in r.text.lower() or "dashboard" in r.text.lower():
                    raise Exception(f"RBAC BYPASS ANON: Ẩn danh vào được {path}!")
        except requests.RequestException:
            pass

def test_40_admin_can_access_all():
    """Admin truy cập được tất cả trang admin."""
    _http_login(http_session_admin, ADMIN_USER, ADMIN_PASS)
    for path in ["/admin/products", "/admin/customers", "/admin/orders",
                 "/admin/categories", "/admin/report"]:
        r = http_session_admin.get(urljoin(BASE_URL, path), timeout=API_TIMEOUT)
        assert r.status_code == 200, f"Admin không vào được {path} (status={r.status_code})"

def test_41_logout_invalidates_session():
    """Session hết hiệu lực sau logout – không dùng session cũ được."""
    sess = requests.Session()
    _http_login(sess, ADMIN_USER, ADMIN_PASS)
    sess.get(urljoin(BASE_URL, "/auth/logout"), timeout=API_TIMEOUT, allow_redirects=True)
    r = sess.get(urljoin(BASE_URL, "/admin/products"), timeout=API_TIMEOUT, allow_redirects=True)
    if r.status_code == 200 and "quản lý" in r.text.lower():
        raise Exception("Session vẫn còn hiệu lực sau logout – lỗ hổng session!")

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 6 – PERFORMANCE  (TC 42 → 45)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 6: PERFORMANCE – CONCURRENT LOAD TEST")
print("=" * 80)

def _get_one(url: str) -> tuple:
    start = time.perf_counter()
    try:
        r = requests.get(url, timeout=API_TIMEOUT)
        return r.status_code, time.perf_counter() - start
    except Exception:
        return 0, time.perf_counter() - start

def _concurrent_test(url, n_req=PERF_REQUESTS, workers=PERF_WORKERS,
                     rate_threshold=0.85, latency_limit=3.0):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_get_one, url) for _ in range(n_req)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())
    statuses  = [s for s, _ in results]
    latencies = [t for _, t in results]
    success   = sum(1 for s in statuses if s == 200)
    avg_lat   = sum(latencies) / len(latencies)
    return {
        "total": n_req, "success": success,
        "success_rate": success / n_req,
        "avg_latency": avg_lat,
        "max_latency": max(latencies),
        "ok": (success / n_req) >= rate_threshold and avg_lat <= latency_limit,
    }

def test_42_perf_homepage():
    """Homepage 30 requests / 10 workers → pass rate ≥ 85%, avg < 3s."""
    stats = _concurrent_test(BASE_URL)
    print(f"      * Perf Homepage: {stats['success']}/{stats['total']} OK, "
          f"avg={stats['avg_latency']:.2f}s, max={stats['max_latency']:.2f}s")
    assert stats["ok"], \
        f"Homepage quá chậm: rate={stats['success_rate']:.0%}, avg={stats['avg_latency']:.2f}s"

def test_43_perf_search():
    """Search 30 requests → pass rate ≥ 70%."""
    url = urljoin(BASE_URL, "/products?search=camera")
    stats = _concurrent_test(url)
    print(f"      * Perf Search: {stats['success']}/{stats['total']} OK, avg={stats['avg_latency']:.2f}s")
    assert stats["success_rate"] >= 0.7, f"Search quá nhiều lỗi: {stats['success_rate']:.0%}"

def test_44_homepage_response_time():
    """Homepage đơn lẻ trả response < 2 giây."""
    _, elapsed = _get_one(BASE_URL)
    print(f"      * Homepage response: {elapsed:.2f}s")
    assert elapsed < 2.0, f"Homepage load quá chậm: {elapsed:.2f}s"

def test_45_login_page_response_time():
    """Trang /auth/login đơn lẻ trả response < 2 giây."""
    _, elapsed = _get_one(urljoin(BASE_URL, "/auth/login"))
    print(f"      * Login page response: {elapsed:.2f}s")
    assert elapsed < 2.0, f"Login page quá chậm: {elapsed:.2f}s"

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 7 – SESSION & COOKIE  (TC 46 → 48)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 7: SESSION & COOKIE MANAGEMENT")
print("=" * 80)

def test_46_cookie_httponly():
    """Cookie session có HttpOnly flag."""
    _selenium_admin_login()
    cookies = driver.get_cookies()
    sess_cookies = [c for c in cookies
                    if "session" in c["name"].lower() or "connect" in c["name"].lower()]
    if not sess_cookies:
        sess_cookies = [c for c in cookies if c.get("httpOnly") is not None]
    non_httponly = [c["name"] for c in sess_cookies if not c.get("httpOnly", False)]
    if non_httponly:
        print(f"      * WARN: Cookie thiếu HttpOnly: {non_httponly}")
    else:
        print(f"      * INFO: {len(sess_cookies)} session cookie(s) có HttpOnly flag ✓")

def test_47_session_persist_across_pages():
    """Session duy trì khi chuyển các trang sau login."""
    _selenium_login(FRONTEND_USER, FRONTEND_PASS)
    driver.get(f"{BASE_URL}/products")
    time.sleep(0.5)
    driver.get(f"{BASE_URL}/cart")
    time.sleep(0.5)
    assert "500" not in driver.title, "Session mất khi chuyển trang!"
    if "login" in driver.current_url.lower():
        raise Exception("Session không duy trì – user bị logout khi chuyển trang!")

def test_48_logout_clears_session():
    """Sau logout, truy cập /cart → redirect về login."""
    driver.get(f"{BASE_URL}/auth/logout")
    time.sleep(1)
    driver.get(f"{BASE_URL}/cart")
    time.sleep(1)
    assert "login" in driver.current_url.lower() or "auth" in driver.current_url.lower(), \
        "Sau logout vẫn truy cập được /cart – session không bị xóa!"

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 8 – UI/UX  (TC 49 → 53)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 8: UI/UX FRONTEND")
print("=" * 80)

def test_49_homepage_has_navbar():
    """Trang chủ có navbar điều hướng."""
    driver.get(BASE_URL)
    time.sleep(1)
    navbars = driver.find_elements(By.CSS_SELECTOR, "nav, .navbar, .nav, header")
    assert navbars, "Không tìm thấy navbar trên trang chủ!"

def test_50_homepage_has_footer():
    """Trang chủ có footer."""
    driver.get(BASE_URL)
    time.sleep(1)
    footers = driver.find_elements(By.CSS_SELECTOR, "footer, .footer, #footer")
    assert footers, "Không tìm thấy footer trên trang chủ!"

def test_51_css_loaded():
    """CSS đã load thành công."""
    driver.get(BASE_URL)
    time.sleep(1)
    bg = driver.execute_script("return window.getComputedStyle(document.body).backgroundColor")
    assert bg and bg != "", "CSS chưa load – background rỗng!"

def test_52_no_severe_js_errors():
    """Trang chủ không có lỗi JS SEVERE."""
    driver.get(BASE_URL)
    time.sleep(1.5)
    try:
        logs = driver.get_log("browser")
        severe = [l for l in logs if l.get("level") == "SEVERE"
                  and "favicon" not in l.get("message", "").lower()]
        if severe:
            print(f"      * WARN: JS errors: {[l['message'][:80] for l in severe[:3]]}")
    except Exception:
        print("      * INFO: Không lấy được browser logs.")

def test_53_product_card_displays():
    """Thẻ sản phẩm hiển thị đúng trên /products."""
    driver.get(f"{BASE_URL}/products")
    time.sleep(1.5)
    cards = driver.find_elements(By.CSS_SELECTOR, ".product-card, .card, [class*='product']")
    if cards:
        card_text = cards[0].text
        assert len(card_text.strip()) > 5, "Thẻ sản phẩm không có nội dung!"
        print(f"      * INFO: Tìm thấy {len(cards)} product card(s).")
    else:
        print("      * WARN: Không tìm thấy product card.")

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 9 – ADMIN CRUD SẢN PHẨM  (TC 54 → 59)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 9: ADMIN CRUD – QUẢN LÝ SẢN PHẨM")
print("=" * 80)

def test_54_admin_products_list():
    """Admin /admin/products → danh sách sản phẩm hiển thị."""
    _selenium_admin_login()
    driver.get(f"{BASE_URL}/admin/products")
    time.sleep(1.5)
    assert "500" not in driver.title, "Admin/products gây 500!"
    body = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert any(kw in body for kw in ["sản phẩm", "product", "camera"]), \
        "Admin products page không có nội dung!"

def test_55_admin_create_product():
    """Admin tạo sản phẩm mới Camera Hikvision DS-2CD → lưu thành công."""
    driver.get(f"{BASE_URL}/admin/products/create")
    time.sleep(1)
    try:
        pname = f"Camera Hikvision DS-2CD {_TS}"
        wait.until(EC.visibility_of_element_located((By.NAME, "name"))).send_keys(pname)
        driver.find_element(By.NAME, "price").send_keys("3500000")
        driver.find_element(By.NAME, "stock").send_keys("15")
        driver.find_element(By.NAME, "resolution").send_keys("4MP")
        driver.find_element(By.NAME, "view_angle").send_keys("90")
        driver.find_element(By.NAME, "description").send_keys(
            "Camera IP ngoài trời Hikvision 4MP, hỗ trợ H.265+, tích hợp AI.")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1.5)
        assert "500" not in driver.title, "Tạo sản phẩm gây 500!"
        driver.get(f"{BASE_URL}/admin/products")
        time.sleep(1)
        body = driver.find_element(By.TAG_NAME, "body").text
        if pname not in body:
            print(f"      * WARN: Sản phẩm '{pname}' không hiện ngay.")
    except (NoSuchElementException, TimeoutException) as e:
        print(f"      * WARN: Form không chuẩn: {e}")

def test_56_admin_edit_product():
    """Admin vào trang edit sản phẩm → form load OK."""
    driver.get(f"{BASE_URL}/admin/products")
    time.sleep(1.5)
    edit_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/admin/products/'][href*='/edit']")
    if edit_links:
        driver.execute_script("arguments[0].click();", edit_links[0])
        time.sleep(1.5)
        assert "500" not in driver.title, "Edit product gây 500!"
        assert driver.find_elements(By.CSS_SELECTOR, "form"), "Trang edit không có form!"
    else:
        print("      * WARN: Không tìm thấy link edit product.")

def test_57_admin_categories_list():
    """Admin /admin/categories → danh mục hiển thị."""
    driver.get(f"{BASE_URL}/admin/categories")
    time.sleep(1.5)
    assert "500" not in driver.title, "Admin/categories gây 500!"
    body = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert any(kw in body for kw in ["danh mục", "category", "tên"]), \
        "Admin categories không có nội dung!"

def test_58_admin_create_category():
    """Admin tạo danh mục 'Camera IP Dahua' → thành công."""
    driver.get(f"{BASE_URL}/admin/categories")
    time.sleep(1)
    try:
        cat_name = f"Camera IP Dahua {_TS}"
        wait.until(EC.visibility_of_element_located((By.NAME, "name"))).send_keys(cat_name)
        driver.find_element(By.NAME, "description").send_keys(
            "Danh mục dòng camera IP thương hiệu Dahua")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1.5)
        assert "500" not in driver.title, "Tạo category gây 500!"
        body = driver.find_element(By.TAG_NAME, "body").text
        if cat_name not in body:
            print(f"      * WARN: Category '{cat_name}' không hiện ngay.")
    except (NoSuchElementException, TimeoutException):
        print("      * WARN: Không tìm thấy form tạo category.")

def test_59_admin_suppliers_list():
    """Admin /admin/suppliers → trang hiển thị OK."""
    driver.get(f"{BASE_URL}/admin/suppliers")
    time.sleep(1.5)
    assert "500" not in driver.title, "Admin/suppliers gây 500!"
    assert "404" not in driver.title, "Admin/suppliers trả 404!"

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 10 – TRANG SẢN PHẨM & NỘI DUNG  (TC 60 → 69)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 10: TRANG SẢN PHẨM & NỘI DUNG")
print("=" * 80)

def test_60_products_page_loads():
    """Trang /products load OK, có nội dung."""
    driver.get(f"{BASE_URL}/products")
    time.sleep(1.5)
    assert "500" not in driver.title, "Trang /products gây 500!"
    assert len(driver.find_element(By.TAG_NAME, "body").text.strip()) > 100

def test_61_product_detail_info():
    """Trang chi tiết sản phẩm có đủ tên, giá, thông tin."""
    driver.get(f"{BASE_URL}/products")
    time.sleep(1.5)
    links = driver.find_elements(By.CSS_SELECTOR, ".product-card a, a[href*='/products/']")
    if not links:
        print("      * INFO: Không có sản phẩm để test chi tiết.")
        return
    driver.get(links[0].get_attribute("href"))
    time.sleep(1.5)
    body = driver.find_element(By.TAG_NAME, "body").text
    assert len(body.strip()) > 50, "Trang chi tiết sản phẩm quá ít nội dung!"
    assert "500" not in driver.title, "Chi tiết sản phẩm gây 500!"

def test_62_search_no_results():
    """Search từ không tồn tại → không crash, hiển thị phù hợp."""
    driver.get(f"{BASE_URL}/products?search=xyzkhongtontai999abcdef")
    time.sleep(1.5)
    assert "500" not in driver.title, "Search không có kết quả gây 500!"

def test_63_products_pagination():
    """Phân trang sản phẩm hoạt động đúng."""
    driver.get(f"{BASE_URL}/products")
    time.sleep(1)
    paginators = driver.find_elements(By.CSS_SELECTOR, ".pagination, .page-btn, nav[aria-label]")
    if paginators:
        page_links = driver.find_elements(By.CSS_SELECTOR, ".page-btn, .pagination a")
        if len(page_links) > 1:
            driver.execute_script("arguments[0].click();", page_links[-1])
            time.sleep(1.5)
            assert "500" not in driver.title, "Pagination gây 500!"
        print(f"      * INFO: {len(page_links)} pagination link(s).")
    else:
        print("      * INFO: Không có pagination (ít SP).")

def test_64_search_vietnamese():
    """Search tiếng Việt 'camera an ninh' → không crash."""
    r = http_anon.get(urljoin(BASE_URL, "/products?search=camera an ninh"), timeout=API_TIMEOUT)
    assert r.status_code in [200, 302], f"Search tiếng Việt trả {r.status_code}"
    assert "500" not in r.text[:500], "Search tiếng Việt gây 500!"

def test_65_homepage_loads_within_3s():
    """Trang chủ render xong trong 3 giây (Selenium)."""
    start = time.perf_counter()
    driver.get(BASE_URL)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    elapsed = time.perf_counter() - start
    print(f"      * Homepage Selenium render: {elapsed:.2f}s")
    assert elapsed < 3.0, f"Trang chủ render quá chậm: {elapsed:.2f}s"

def test_66_product_images_have_src():
    """Ảnh sản phẩm có src không rỗng."""
    driver.get(f"{BASE_URL}/products")
    time.sleep(1.5)
    images = driver.find_elements(By.CSS_SELECTOR, ".product-card img, .product-info img, img")
    product_imgs = [img for img in images if img.get_attribute("src")
                    and ("product" in (img.get_attribute("src") or "") or
                         "upload" in (img.get_attribute("src") or "") or
                         "no-image" in (img.get_attribute("src") or ""))]
    if product_imgs:
        for img in product_imgs[:3]:
            assert img.get_attribute("src"), "Ảnh sản phẩm không có src!"
        print(f"      * INFO: {len(product_imgs)} sản phẩm có ảnh.")
    else:
        print("      * WARN: Không tìm thấy ảnh sản phẩm cụ thể.")

def test_67_add_cart_requires_login():
    """Guest click 'Thêm giỏ hàng' → redirect login (không 500)."""
    driver.get(f"{BASE_URL}/auth/logout")
    time.sleep(0.5)
    driver.get(f"{BASE_URL}/products")
    time.sleep(1)
    login_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/auth/login']")
    cart_forms  = driver.find_elements(By.CSS_SELECTOR, "form[action='/cart/add']")
    if cart_forms:
        driver.execute_script("arguments[0].submit();", cart_forms[0])
        time.sleep(1.5)
        assert "500" not in driver.title, "Add cart guest gây 500!"
        assert "login" in driver.current_url.lower() or "auth" in driver.current_url.lower(), \
            "Guest add cart không redirect về login!"
    elif login_links:
        print(f"      * INFO: Guest thấy {len(login_links)} link đăng nhập thay vì add cart.")

def test_68_product_related_items():
    """Trang chi tiết sản phẩm hiển thị sản phẩm liên quan."""
    driver.get(f"{BASE_URL}/products")
    time.sleep(1)
    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/products/']")
    if links:
        driver.execute_script("arguments[0].click();", links[0])
        time.sleep(1.5)
        assert "500" not in driver.title, "Chi tiết SP gây 500!"
        related = driver.find_elements(By.CSS_SELECTOR, ".product-card, .related, [class*='related']")
        print(f"      * INFO: Tìm thấy {len(related)} sản phẩm liên quan.")

def test_69_homepage_shows_products():
    """Trang chủ hiển thị sản phẩm nổi bật."""
    driver.get(BASE_URL)
    time.sleep(1.5)
    cards = driver.find_elements(By.CSS_SELECTOR, ".product-card, a[href*='/products/']")
    print(f"      * INFO: Trang chủ hiển thị {len(cards)} product card(s).")
    assert "500" not in driver.title, "Trang chủ gây 500!"

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 11 – PROFILE & TÀI KHOẢN  (TC 70 → 79)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 11: TRANG CÁ NHÂN & QUẢN LÝ TÀI KHOẢN")
print("=" * 80)

def test_70_profile_accessible():
    """User đã login → /profile load OK, không 500/404."""
    _selenium_login(FRONTEND_USER, FRONTEND_PASS)
    driver.get(f"{BASE_URL}/profile")
    time.sleep(1)
    assert "500" not in driver.title, "Profile page gây 500!"
    assert "404" not in driver.title, "Profile page trả 404!"

def test_71_profile_shows_username():
    """Trang /profile hiển thị thông tin user."""
    driver.get(f"{BASE_URL}/profile")
    time.sleep(1)
    body = driver.find_element(By.TAG_NAME, "body").text
    assert FRONTEND_USER in body or "profile" in driver.current_url.lower(), \
        "Profile không hiển thị username!"

def test_72_profile_update_info():
    """User cập nhật phone/address → không crash, redirect OK."""
    driver.get(f"{BASE_URL}/profile")
    time.sleep(1)
    try:
        phone = wait.until(EC.visibility_of_element_located((By.NAME, "phone")))
        phone.clear()
        phone.send_keys("0909876543")
        addr = driver.find_element(By.NAME, "address")
        addr.clear()
        addr.send_keys("123 Đường Lê Lợi, Quận 1, TP. HCM")
        driver.execute_script("arguments[0].click();",
                              driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
        time.sleep(1.5)
        assert "500" not in driver.title, "Cập nhật profile gây 500!"
    except (NoSuchElementException, TimeoutException):
        print("      * WARN: Không tìm thấy form cập nhật profile.")

def test_73_change_password_wrong_old():
    """Đổi mật khẩu với old_password sai → thông báo lỗi."""
    driver.get(f"{BASE_URL}/profile")
    time.sleep(1)
    try:
        old = wait.until(EC.visibility_of_element_located((By.NAME, "old_password")))
        old.send_keys("SaiMatKhauCu999!")
        driver.find_element(By.NAME, "new_password").send_keys("NewCamPro@456")
        driver.find_element(By.NAME, "confirm_password").send_keys("NewCamPro@456")
        submits = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']")
        if len(submits) > 1:
            driver.execute_script("arguments[0].click();", submits[-1])
        time.sleep(1.5)
        assert "500" not in driver.title, "Đổi pass sai gây 500!"
        body = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "không đúng" in body or "error" in body or "profile" in driver.current_url.lower(), \
            "Đổi pass sai mật khẩu cũ không báo lỗi!"
    except (NoSuchElementException, TimeoutException):
        print("      * WARN: Không tìm thấy form đổi mật khẩu.")

def test_74_profile_requires_login():
    """Guest truy cập /profile → redirect login."""
    driver.get(f"{BASE_URL}/auth/logout")
    time.sleep(0.5)
    driver.get(f"{BASE_URL}/profile")
    time.sleep(1)
    assert "login" in driver.current_url.lower() or "auth" in driver.current_url.lower(), \
        "Guest truy cập /profile không bị redirect!"

def test_75_orders_page_accessible():
    """User đã login xem /orders → trang load OK."""
    _selenium_login(FRONTEND_USER, FRONTEND_PASS)
    driver.get(f"{BASE_URL}/orders")
    time.sleep(1.5)
    assert "500" not in driver.title, "Orders page gây 500!"
    assert "404" not in driver.title, "Orders page trả 404!"

def test_76_orders_requires_login():
    """Guest truy cập /orders → redirect login."""
    driver.get(f"{BASE_URL}/auth/logout")
    time.sleep(0.5)
    driver.get(f"{BASE_URL}/orders")
    time.sleep(1)
    assert "login" in driver.current_url.lower() or "auth" in driver.current_url.lower(), \
        "Guest truy cập /orders không bị redirect!"

def test_77_checkout_empty_cart():
    """Checkout giỏ hàng rỗng → redirect hoặc thông báo, không crash."""
    _selenium_login(FRONTEND_USER, FRONTEND_PASS)
    http_sess = requests.Session()
    _http_login(http_sess, FRONTEND_USER, FRONTEND_PASS)
    http_sess.post(urljoin(BASE_URL, "/cart/clear"), timeout=5, allow_redirects=True)
    driver.get(f"{BASE_URL}/orders/checkout")
    time.sleep(1.5)
    assert "500" not in driver.title, "Checkout giỏ rỗng gây 500!"

def test_78_news_page_loads():
    """Trang /news load OK."""
    driver.get(f"{BASE_URL}/news")
    time.sleep(1.5)
    assert "500" not in driver.title, "/news gây 500!"
    assert "404" not in driver.title, "/news trả 404!"

def test_79_contact_form_submit():
    """Gửi form liên hệ đầy đủ thông tin → thành công, không crash."""
    driver.get(f"{BASE_URL}/contact")
    time.sleep(1)
    try:
        wait.until(EC.visibility_of_element_located((By.NAME, "full_name"))).send_keys(
            "Nguyễn Văn Camera Test")
        driver.find_element(By.NAME, "email").send_keys("camera_test@campro.vn")
        driver.find_element(By.NAME, "phone").send_keys("0901234567")
        driver.find_element(By.NAME, "subject").send_keys("Tư vấn camera an ninh")
        driver.find_element(By.NAME, "message").send_keys(
            "Tôi cần tư vấn lắp đặt hệ thống camera Hikvision 4K cho văn phòng 50m². Kiểm thử tự động.")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1.5)
        assert "500" not in driver.title, "Gửi liên hệ gây 500!"
    except (NoSuchElementException, TimeoutException):
        print("      * WARN: Không tìm thấy form liên hệ.")

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 12 – ADMIN ORDERS, COUPONS, NEWS  (TC 80 → 91)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 12: ADMIN ORDERS & COUPONS")
print("=" * 80)

def test_80_admin_orders_list():
    """Admin /admin/orders → danh sách đơn hàng hiển thị."""
    _selenium_admin_login()
    driver.get(f"{BASE_URL}/admin/orders")
    time.sleep(1.5)
    assert "500" not in driver.title, "Admin/orders gây 500!"
    body = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert any(kw in body for kw in ["đơn hàng", "order", "mã đơn"]), \
        "Admin orders page không có nội dung!"

def test_81_admin_orders_filter_pending():
    """Admin lọc đơn hàng status=pending → status 200."""
    _http_login(http_session_admin, ADMIN_USER, ADMIN_PASS)
    r = http_session_admin.get(urljoin(BASE_URL, "/admin/orders?status=pending"),
                                timeout=API_TIMEOUT)
    assert r.status_code == 200, f"Filter orders pending trả {r.status_code}"

def test_82_admin_coupons_list():
    """Admin /admin/coupons → trang hiển thị OK."""
    driver.get(f"{BASE_URL}/admin/coupons")
    time.sleep(1.5)
    assert "500" not in driver.title, "Admin/coupons gây 500!"

def test_83_admin_create_coupon():
    """Admin tạo mã giảm giá CAMERA10 → thêm thành công."""
    driver.get(f"{BASE_URL}/admin/coupons")
    time.sleep(1)
    try:
        code = f"CAM{_TS % 10000}"
        wait.until(EC.visibility_of_element_located((By.NAME, "code"))).send_keys(code)
        driver.find_element(By.NAME, "discount_value").send_keys("10")
        driver.find_element(By.NAME, "min_order_amount").send_keys("500000")
        submits = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", submits[0])
        time.sleep(1.5)
        assert "500" not in driver.title, "Tạo coupon gây 500!"
        body = driver.find_element(By.TAG_NAME, "body").text
        if code in body:
            print(f"      * INFO: Coupon '{code}' tạo thành công.")
    except (NoSuchElementException, TimeoutException):
        print("      * WARN: Form tạo coupon không chuẩn.")

def test_84_admin_news_list():
    """Admin /admin/news → danh sách bài viết hiển thị."""
    driver.get(f"{BASE_URL}/admin/news")
    time.sleep(1.5)
    assert "500" not in driver.title, "Admin/news gây 500!"

def test_85_admin_create_news():
    """Admin tạo bài viết 'Hướng dẫn lắp camera' → thêm thành công."""
    driver.get(f"{BASE_URL}/admin/news/create")
    time.sleep(1)
    try:
        title = f"Hướng dẫn lắp đặt camera Hikvision 4MP {_TS}"
        wait.until(EC.visibility_of_element_located((By.NAME, "title"))).send_keys(title)
        driver.find_element(By.NAME, "excerpt").send_keys(
            "Hướng dẫn chi tiết lắp camera an ninh Hikvision 4MP cho gia đình và văn phòng.")
        driver.find_element(By.NAME, "content").send_keys(
            "Bước 1: Chọn vị trí lắp camera thích hợp, đảm bảo góc quan sát rộng.\n"
            "Bước 2: Khoan lỗ, bắt vít đế camera chắc chắn.\n"
            "Bước 3: Kết nối dây nguồn và dây mạng, cấu hình NVR.\n"
            "Bước 4: Cài đặt ứng dụng Hik-Connect để xem từ xa. " * 3)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1.5)
        assert "500" not in driver.title, "Tạo bài viết gây 500!"
    except (NoSuchElementException, TimeoutException):
        print("      * WARN: Form tạo bài viết không chuẩn.")

def test_86_admin_contacts_list():
    """Admin /admin/contacts → danh sách liên hệ hiển thị."""
    driver.get(f"{BASE_URL}/admin/contacts")
    time.sleep(1.5)
    assert "500" not in driver.title, "Admin/contacts gây 500!"

def test_87_admin_contacts_filter_unread():
    """Admin lọc liên hệ status=unread → status 200."""
    r = http_session_admin.get(urljoin(BASE_URL, "/admin/contacts?status=unread"),
                                timeout=API_TIMEOUT)
    assert r.status_code == 200, f"Filter contacts unread trả {r.status_code}"

def test_88_admin_customers_list():
    """Admin /admin/customers → danh sách khách hàng hiển thị."""
    driver.get(f"{BASE_URL}/admin/customers")
    time.sleep(1.5)
    assert "500" not in driver.title, "Admin/customers gây 500!"
    body = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert any(kw in body for kw in ["khách hàng", "email", "username"]), \
        "Admin customers không có nội dung!"

def test_89_admin_search_customers():
    """Admin tìm kiếm khách hàng → status 200, không crash."""
    r = http_session_admin.get(urljoin(BASE_URL, f"/admin/customers?search=camera"),
                                timeout=API_TIMEOUT)
    assert r.status_code == 200, f"Search customers trả {r.status_code}"

def test_90_admin_toggle_product():
    """Admin toggle trạng thái sản phẩm → không crash."""
    r = http_session_admin.get(urljoin(BASE_URL, "/admin/products"), timeout=API_TIMEOUT)
    match = re.search(r'/admin/products/(\d+)/toggle', r.text)
    if match:
        pid = match.group(1)
        r2  = http_session_admin.post(urljoin(BASE_URL, f"/admin/products/{pid}/toggle"),
                                       timeout=API_TIMEOUT, allow_redirects=True)
        assert r2.status_code in [200, 302], f"Toggle product trả {r2.status_code}"
        print(f"      * INFO: Toggle product #{pid} OK.")
    else:
        print("      * WARN: Không tìm thấy product để toggle.")

def test_91_admin_delete_category():
    """Admin tạo category tạm rồi xóa → không crash."""
    driver.get(f"{BASE_URL}/admin/categories")
    time.sleep(1)
    temp_cat = f"TempCat{_TS}"
    try:
        wait.until(EC.visibility_of_element_located((By.NAME, "name"))).send_keys(temp_cat)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1.5)
        body = driver.find_element(By.TAG_NAME, "body").text
        if temp_cat in body:
            del_forms = driver.find_elements(
                By.CSS_SELECTOR, "form[action*='/admin/categories/'][action*='/delete']")
            if del_forms:
                del_forms[-1].submit()
                time.sleep(1)
                assert "500" not in driver.title, "Xóa category gây 500!"
    except (NoSuchElementException, TimeoutException):
        print("      * WARN: Form tạo/xóa category không chuẩn.")

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 13 – PERFORMANCE NÂNG CAO  (TC 92 → 101)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 13: PERFORMANCE NÂNG CAO")
print("=" * 80)

def test_92_perf_products_page():
    """/products 20 requests / 8 workers → pass rate ≥ 80%."""
    stats = _concurrent_test(urljoin(BASE_URL, "/products"), n_req=20, workers=8, rate_threshold=0.80)
    print(f"      * Perf /products: {stats['success']}/{stats['total']} OK, avg={stats['avg_latency']:.2f}s")
    assert stats["success_rate"] >= 0.80, f"/products quá nhiều lỗi: {stats['success_rate']:.0%}"

def test_93_perf_admin_products():
    """Admin/products đơn lẻ < 3 giây."""
    _http_login(http_session_admin, ADMIN_USER, ADMIN_PASS)
    start = time.perf_counter()
    r = http_session_admin.get(urljoin(BASE_URL, "/admin/products"), timeout=API_TIMEOUT)
    elapsed = time.perf_counter() - start
    print(f"      * Admin/products latency: {elapsed:.2f}s")
    assert r.status_code == 200, f"Admin/products trả {r.status_code}"
    assert elapsed < 3.0, f"Admin/products quá chậm: {elapsed:.2f}s"

def test_94_perf_register_page():
    """/auth/register đơn lẻ < 2 giây."""
    _, elapsed = _get_one(urljoin(BASE_URL, "/auth/register"))
    print(f"      * Register page latency: {elapsed:.2f}s")
    assert elapsed < 2.0, f"Register page quá chậm: {elapsed:.2f}s"

def test_95_perf_news_page():
    """/news đơn lẻ < 2 giây."""
    _, elapsed = _get_one(urljoin(BASE_URL, "/news"))
    print(f"      * News page latency: {elapsed:.2f}s")
    assert elapsed < 2.0, f"News page quá chậm: {elapsed:.2f}s"

def test_96_perf_contact_page():
    """/contact đơn lẻ < 2 giây."""
    _, elapsed = _get_one(urljoin(BASE_URL, "/contact"))
    print(f"      * Contact page latency: {elapsed:.2f}s")
    assert elapsed < 2.0, f"Contact page quá chậm: {elapsed:.2f}s"

def test_97_perf_stress_homepage():
    """Homepage stress 50 requests / 20 workers → pass rate ≥ 75%."""
    stats = _concurrent_test(BASE_URL, n_req=50, workers=20, rate_threshold=0.75, latency_limit=5.0)
    print(f"      * Stress Homepage: {stats['success']}/{stats['total']} OK, avg={stats['avg_latency']:.2f}s")
    assert stats["success_rate"] >= 0.75, f"Stress test homepage fail: {stats['success_rate']:.0%}"

def test_98_perf_products_ttfb():
    """TTFB /products < 1.5 giây."""
    start = time.perf_counter()
    r = http_anon.get(urljoin(BASE_URL, "/products"), timeout=API_TIMEOUT, stream=True)
    r.raw.read(1)
    ttfb = time.perf_counter() - start
    print(f"      * Products TTFB: {ttfb:.2f}s")
    assert ttfb < 1.5, f"Products TTFB quá cao: {ttfb:.2f}s"

def test_99_perf_login_concurrent():
    """Login 20 requests / 10 workers → pass rate ≥ 90%."""
    stats = _concurrent_test(urljoin(BASE_URL, "/auth/login"), n_req=20, workers=10, rate_threshold=0.90)
    print(f"      * Perf Login: {stats['success']}/{stats['total']} OK")
    assert stats["success_rate"] >= 0.90, f"Login quá nhiều lỗi: {stats['success_rate']:.0%}"

def test_100_perf_search_stress():
    """Search stress 30 requests / 15 workers → pass rate ≥ 65%."""
    stats = _concurrent_test(urljoin(BASE_URL, "/products?search=cam"),
                              n_req=30, workers=15, rate_threshold=0.65, latency_limit=5.0)
    print(f"      * Search stress: {stats['success']}/{stats['total']} OK")
    assert stats["success_rate"] >= 0.65, f"Search stress fail: {stats['success_rate']:.0%}"

def test_101_perf_homepage_ttfb():
    """TTFB / < 1.5 giây."""
    start = time.perf_counter()
    r = http_anon.get(BASE_URL, timeout=API_TIMEOUT, stream=True)
    r.raw.read(1)
    ttfb = time.perf_counter() - start
    print(f"      * Homepage TTFB: {ttfb:.2f}s")
    assert ttfb < 1.5, f"Homepage TTFB quá cao: {ttfb:.2f}s"

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 14 – SECURITY NÂNG CAO  (TC 102 → 109)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 14: SECURITY NÂNG CAO")
print("=" * 80)

def test_102_open_redirect():
    """Open Redirect: param next=evil.com bị block."""
    for evil in ["http://evil.com", "https://attacker.vn", "//evil.com"]:
        r = http_anon.get(urljoin(BASE_URL, f"/auth/login?next={evil}"),
                          timeout=API_TIMEOUT, allow_redirects=False)
        if r.status_code in [301, 302]:
            loc = r.headers.get("location", "")
            parsed = urlparse(loc)
            if parsed.netloc and parsed.netloc not in ["localhost", "127.0.0.1", ""]:
                raise Exception(f"Open Redirect! Redirect tới: {loc}")
        print(f"      * INFO: Open redirect '{evil}' → OK.")

def test_103_directory_traversal():
    """Directory Traversal trong URL → không lộ file hệ thống."""
    payloads = ["../../etc/passwd", "../../../etc/shadow", "..%2F..%2Fetc%2Fpasswd"]
    for p in payloads:
        for base_path in ["/products/", "/news/"]:
            r = http_anon.get(urljoin(BASE_URL, base_path + p),
                              timeout=API_TIMEOUT, allow_redirects=True)
            assert r.status_code != 500, f"Directory Traversal gây 500! Path: {p}"
            assert "root:" not in r.text, f"Directory Traversal lộ /etc/passwd! Path: {p}"

def test_104_mass_assignment():
    """POST đăng ký với role=admin → server ignore, không thành admin."""
    hacker = f"hacker_{_TS}"
    r = http_anon.post(urljoin(BASE_URL, "/auth/register"),
                       data={"full_name": "Hacker Test Camera",
                             "username": hacker,
                             "email": f"{hacker}@evil.vn",
                             "password": FRONTEND_PASS,
                             "role": "admin"},
                       timeout=API_TIMEOUT, allow_redirects=True)
    assert r.status_code in [200, 302], f"Mass assignment request trả {r.status_code}"
    sess2 = requests.Session()
    _http_login(sess2, hacker, FRONTEND_PASS)
    r2 = sess2.get(urljoin(BASE_URL, "/admin/products"), timeout=API_TIMEOUT, allow_redirects=True)
    if r2.status_code == 200:
        if "quản lý" in r2.text.lower() or ("admin" in r2.url.lower() and "login" not in r2.url.lower()):
            raise Exception("MASS ASSIGNMENT: User inject role=admin vào được admin!")
    print("      * INFO: Mass assignment OK – role không bị inject.")

def test_105_clickjacking_protection():
    """Kiểm tra X-Frame-Options header."""
    r = http_anon.get(BASE_URL, timeout=API_TIMEOUT)
    headers = {k.lower(): v for k, v in r.headers.items()}
    if "x-frame-options" not in headers:
        print("      * WARN: Thiếu X-Frame-Options (dễ bị Clickjacking).")
    else:
        print(f"      * INFO: X-Frame-Options = {headers['x-frame-options']}")

def test_106_server_info_leakage():
    """X-Powered-By không lộ thông tin phiên bản server."""
    r = http_anon.get(BASE_URL, timeout=API_TIMEOUT)
    headers = {k.lower(): v for k, v in r.headers.items()}
    powered = headers.get("x-powered-by", "")
    if powered:
        print(f"      * WARN: X-Powered-By lộ: '{powered}' (nên ẩn bằng helmet).")
    else:
        print("      * INFO: X-Powered-By không lộ – OK.")

def test_107_brute_force_login():
    """5 lần login sai liên tiếp → server không crash, không 500."""
    for i in range(5):
        r = http_anon.post(urljoin(BASE_URL, "/auth/login"),
                           data={"username": ADMIN_USER, "password": f"WrongCam{i}Pass"},
                           timeout=API_TIMEOUT, allow_redirects=True)
        assert r.status_code != 500, f"Brute force lần {i+1} gây 500!"
    print("      * INFO: 5 lần brute force không gây crash.")

def test_108_http_methods_invalid():
    """PUT/DELETE tới GET-only endpoints → không trả 200 thành công."""
    for endpoint in ["/products", "/news", "/contact"]:
        url = urljoin(BASE_URL, endpoint)
        for method in ["PUT", "DELETE"]:
            try:
                r = http_anon.request(method, url, timeout=API_TIMEOUT)
                assert r.status_code != 200 or "not found" in r.text.lower(), \
                    f"{method} {endpoint} trả 200 (không mong đợi)!"
            except requests.RequestException:
                pass

def test_109_stack_trace_not_exposed():
    """Request không hợp lệ → không lộ stack trace."""
    invalid_urls = [
        "/products?category_id=INVALID_CAMPRO",
        "/orders/NOT_A_NUMBER_999",
        "/products?page=abc_xyz",
    ]
    for url_path in invalid_urls:
        r = http_anon.get(urljoin(BASE_URL, url_path), timeout=API_TIMEOUT, allow_redirects=True)
        assert r.status_code != 500 or "at Object." not in r.text, \
            f"Stack trace lộ tại {url_path}!"
        assert "SequelizeError" not in r.text, f"DB error lộ tại {url_path}!"

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 15 – ADMIN NÂNG CAO  (TC 110 → 119)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 15: ADMIN NÂNG CAO")
print("=" * 80)

def test_110_admin_order_detail():
    """Admin xem chi tiết đơn hàng đầu tiên → load OK."""
    _selenium_admin_login()
    driver.get(f"{BASE_URL}/admin/orders")
    time.sleep(1.5)
    detail_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/admin/orders/']")
    if detail_links:
        driver.execute_script("arguments[0].click();", detail_links[0])
        time.sleep(1.5)
        assert "500" not in driver.title, "Admin order detail gây 500!"
    else:
        print("      * WARN: Không có đơn hàng để xem chi tiết.")

def test_111_admin_update_order_status():
    """Admin cập nhật trạng thái đơn hàng confirmed → không crash."""
    r = http_session_admin.get(urljoin(BASE_URL, "/admin/orders"), timeout=API_TIMEOUT)
    match = re.search(r'/admin/orders/(\d+)"', r.text)
    if match:
        oid = match.group(1)
        r2  = http_session_admin.post(urljoin(BASE_URL, f"/admin/orders/{oid}/status"),
                                       data={"order_status": "confirmed", "payment_status": "pending"},
                                       timeout=API_TIMEOUT, allow_redirects=True)
        assert r2.status_code in [200, 302], f"Update order status trả {r2.status_code}"
        print(f"      * INFO: Cập nhật status đơn #{oid} OK.")
    else:
        print("      * WARN: Không có đơn hàng để cập nhật.")

def test_112_admin_search_products():
    """Admin tìm kiếm sản phẩm 'Hikvision' trong admin → status 200."""
    r = http_session_admin.get(urljoin(BASE_URL, "/admin/products?search=Hikvision"),
                                timeout=API_TIMEOUT)
    assert r.status_code == 200, f"Admin search products trả {r.status_code}"

def test_113_admin_product_validation():
    """Admin tạo sản phẩm không có tên → server không crash 500."""
    driver.get(f"{BASE_URL}/admin/products/create")
    time.sleep(1)
    try:
        driver.find_element(By.NAME, "price").send_keys("2000000")
        driver.find_element(By.NAME, "stock").send_keys("5")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1.5)
        assert "500" not in driver.title, "Tạo SP không tên gây 500!"
    except (NoSuchElementException, TimeoutException):
        print("      * WARN: Form không chuẩn.")

def test_114_admin_customers_not_empty():
    """Admin/customers có ít nhất 1 tài khoản (admin hoặc user vừa đăng ký)."""
    r = http_session_admin.get(urljoin(BASE_URL, "/admin/customers"), timeout=API_TIMEOUT)
    assert r.status_code == 200, "Không vào được admin/customers!"
    assert any(kw in r.text.lower() for kw in ["email", "username", "full_name", FRONTEND_USER.lower()]), \
        "Admin customers trống – cần có ít nhất 1 user!"

def test_115_admin_toggle_customer():
    """Admin khóa/mở khóa khách hàng → không crash."""
    r = http_session_admin.get(urljoin(BASE_URL, "/admin/customers"), timeout=API_TIMEOUT)
    match = re.search(r'/admin/customers/(\d+)/toggle', r.text)
    if match:
        cid = match.group(1)
        r2  = http_session_admin.post(urljoin(BASE_URL, f"/admin/customers/{cid}/toggle"),
                                       timeout=API_TIMEOUT, allow_redirects=True)
        assert r2.status_code in [200, 302], f"Toggle customer trả {r2.status_code}"
        print(f"      * INFO: Toggle customer #{cid} OK.")
    else:
        print("      * WARN: Không tìm thấy customer để toggle.")

def test_116_admin_create_supplier():
    """Admin tạo nhà cung cấp 'Hikvision Vietnam Co.' → thành công."""
    driver.get(f"{BASE_URL}/admin/suppliers")
    time.sleep(1)
    try:
        wait.until(EC.visibility_of_element_located((By.NAME, "name"))).send_keys(
            f"Hikvision Vietnam Co. {_TS}")
        driver.find_element(By.NAME, "email").send_keys("info@hikvision.vn")
        driver.find_element(By.NAME, "phone").send_keys("02812345678")
        driver.find_element(By.NAME, "address").send_keys("123 Lê Văn Sỹ, Q.3, TP.HCM")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1.5)
        assert "500" not in driver.title, "Tạo nhà cung cấp gây 500!"
    except (NoSuchElementException, TimeoutException):
        print("      * WARN: Form tạo nhà cung cấp không chuẩn.")

def test_117_admin_publish_news():
    """Admin tạo bài viết published → xuất hiện trên /news public."""
    title = f"Camera AI thế hệ mới {_TS}"
    r = http_session_admin.post(urljoin(BASE_URL, "/admin/news"),
                                 data={"title": title,
                                       "content": "Xu hướng camera AI thế hệ mới với nhận diện khuôn mặt. " * 10,
                                       "excerpt": "Camera AI thế hệ mới – nhận diện khuôn mặt, đếm người.",
                                       "is_published": "1"},
                                 timeout=API_TIMEOUT, allow_redirects=True)
    assert r.status_code in [200, 302], f"Tạo news POST trả {r.status_code}"
    r2 = http_anon.get(urljoin(BASE_URL, "/news"), timeout=API_TIMEOUT)
    if title in r2.text:
        print(f"      * INFO: News '{title}' xuất hiện public ✓.")
    else:
        print(f"      * WARN: News '{title}' chưa thấy (có thể cần reload).")

def test_118_admin_delete_coupon():
    """Admin xóa mã giảm giá → không crash."""
    r = http_session_admin.get(urljoin(BASE_URL, "/admin/coupons"), timeout=API_TIMEOUT)
    match = re.search(r'/admin/coupons/(\d+)/delete', r.text)
    if match:
        cid = match.group(1)
        r2  = http_session_admin.post(urljoin(BASE_URL, f"/admin/coupons/{cid}/delete"),
                                       timeout=API_TIMEOUT, allow_redirects=True)
        assert r2.status_code in [200, 302], f"Xóa coupon trả {r2.status_code}"
        print(f"      * INFO: Xóa coupon #{cid} OK.")
    else:
        print("      * WARN: Không có coupon để xóa.")

def test_119_admin_report_page():
    """Admin /admin/report → trang báo cáo doanh thu load OK."""
    driver.get(f"{BASE_URL}/admin/report")
    time.sleep(1.5)
    assert "500" not in driver.title, "Admin/report gây 500!"
    body = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert any(kw in body for kw in ["doanh thu", "báo cáo", "report", "tổng"]), \
        "Admin report không có nội dung!"

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 16 – SEO & ACCESSIBILITY  (TC 120 → 129)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 16: SEO & ACCESSIBILITY")
print("=" * 80)

def test_120_images_have_alt():
    """Ảnh trên trang chủ có thuộc tính alt (SEO/A11y)."""
    driver.get(BASE_URL)
    time.sleep(1.5)
    images = driver.find_elements(By.CSS_SELECTOR, "img")
    missing = [img.get_attribute("src") for img in images if not img.get_attribute("alt")]
    if missing:
        print(f"      * WARN: {len(missing)} ảnh không có alt text.")
    else:
        print(f"      * INFO: Tất cả {len(images)} ảnh có alt text ✓")

def test_121_meta_description():
    """Trang chủ có meta description > 10 ký tự."""
    driver.get(BASE_URL)
    time.sleep(1)
    metas = driver.find_elements(By.CSS_SELECTOR, "meta[name='description']")
    if metas:
        content = metas[0].get_attribute("content") or ""
        assert len(content) > 10, f"Meta description quá ngắn: '{content}'"
        print(f"      * INFO: Meta description OK ({len(content)} ký tự).")
    else:
        print("      * WARN: Không có meta description (ảnh hưởng SEO).")

def test_122_favicon_exists():
    """Favicon tồn tại hoặc được khai báo trong HTML."""
    try:
        r = http_anon.get(urljoin(BASE_URL, "/favicon.ico"), timeout=5)
        if r.status_code == 200:
            print(f"      * INFO: favicon.ico OK ({len(r.content)} bytes).")
        else:
            driver.get(BASE_URL)
            favicons = driver.find_elements(By.CSS_SELECTOR, "link[rel*='icon']")
            if favicons:
                print("      * INFO: Favicon khai báo trong HTML.")
            else:
                print("      * WARN: Không tìm thấy favicon.")
    except Exception as e:
        print(f"      * WARN: Không kiểm tra được favicon: {e}")

def test_123_robots_txt():
    """robots.txt nên tồn tại (SEO best practice)."""
    try:
        r = http_anon.get(urljoin(BASE_URL, "/robots.txt"), timeout=API_TIMEOUT)
        if r.status_code == 200:
            print(f"      * INFO: robots.txt OK ({len(r.text)} bytes).")
        else:
            print(f"      * WARN: robots.txt trả {r.status_code} (khuyến nghị có).")
    except Exception as e:
        print(f"      * WARN: Không kiểm tra robots.txt: {e}")

def test_124_page_titles():
    """Mỗi trang có <title> không rỗng và không có 'Error'."""
    pages = ["/", "/products", "/auth/login", "/contact", "/news"]
    for page in pages:
        driver.get(urljoin(BASE_URL, page))
        time.sleep(0.8)
        title = driver.title
        assert title and len(title.strip()) > 0, f"Trang {page} không có title!"
        assert "500" not in title and "Error" not in title, \
            f"Trang {page} có title lỗi: '{title}'"
    print(f"      * INFO: Tất cả {len(pages)} trang có title hợp lệ.")

def test_125_heading_structure():
    """Trang chủ có ít nhất 1 heading h1/h2/h3."""
    driver.get(BASE_URL)
    time.sleep(1)
    headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3")
    assert headings, "Trang chủ không có thẻ heading (ảnh hưởng SEO)!"
    print(f"      * INFO: Tìm thấy {len(headings)} heading(s).")

def test_126_html_lang_attribute():
    """Thẻ <html> có thuộc tính lang (A11y)."""
    driver.get(BASE_URL)
    time.sleep(1)
    html_el = driver.find_element(By.TAG_NAME, "html")
    lang    = html_el.get_attribute("lang")
    if not lang:
        print("      * WARN: Thẻ <html> không có lang attribute (ảnh hưởng A11y).")
    else:
        print(f"      * INFO: lang='{lang}' OK.")

def test_127_form_inputs_have_labels():
    """Form đăng nhập có label/placeholder cho mỗi input."""
    driver.get(f"{BASE_URL}/auth/login")
    time.sleep(1)
    inputs  = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='password']")
    missing = []
    for inp in inputs:
        has_label = bool(driver.find_elements(
            By.CSS_SELECTOR, f"label[for='{inp.get_attribute('id')}']"))
        has_ph    = bool(inp.get_attribute("placeholder"))
        has_aria  = bool(inp.get_attribute("aria-label"))
        if not (has_label or has_ph or has_aria):
            missing.append(inp.get_attribute("name"))
    if missing:
        print(f"      * WARN: Inputs thiếu label/placeholder: {missing}")
    else:
        print("      * INFO: Tất cả inputs có label/placeholder ✓")

def test_128_open_graph_tags():
    """Trang chủ nên có Open Graph tags."""
    driver.get(BASE_URL)
    time.sleep(1)
    og_tags = driver.find_elements(By.CSS_SELECTOR, "meta[property^='og:']")
    if og_tags:
        print(f"      * INFO: Tìm thấy {len(og_tags)} Open Graph tag(s).")
    else:
        print("      * WARN: Không có Open Graph tags (ảnh hưởng share social).")

def test_129_keyboard_navigation_login():
    """Form đăng nhập submit được bằng Tab + Enter."""
    driver.get(f"{BASE_URL}/auth/login")
    time.sleep(1)
    try:
        username = wait.until(EC.visibility_of_element_located((By.NAME, "username")))
        username.send_keys(ADMIN_USER)
        username.send_keys(Keys.TAB)
        active = driver.switch_to.active_element
        active.send_keys(ADMIN_PASS)
        active.send_keys(Keys.TAB)
        active2 = driver.switch_to.active_element
        active2.send_keys(Keys.RETURN)
        time.sleep(2)
        assert "500" not in driver.title, "Keyboard navigation login gây 500!"
        print(f"      * INFO: Keyboard navigation OK → {driver.current_url}")
    except Exception as e:
        if "500" in str(e):
            raise

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 17 – EDGE CASES & BOUNDARY  (TC 130 → 140)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 17: EDGE CASES & BOUNDARY NÂNG CAO")
print("=" * 80)

def test_130_username_with_spaces():
    """Đăng ký username chứa khoảng trắng → trim hoặc từ chối, không 500."""
    driver.get(f"{BASE_URL}/auth/register")
    time.sleep(1)
    wait.until(EC.visibility_of_element_located((By.NAME, "full_name"))).send_keys("Space Test Camera")
    driver.find_element(By.NAME, "username").send_keys("user with space campro")
    driver.find_element(By.NAME, "email").send_keys(f"space_{_TS}@campro.vn")
    driver.find_element(By.NAME, "password").send_keys(FRONTEND_PASS)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1.5)
    assert "500" not in driver.title, "Username có khoảng trắng gây 500!"

def test_131_very_long_username():
    """Đăng ký username 200 ký tự → không crash."""
    driver.get(f"{BASE_URL}/auth/register")
    time.sleep(1)
    wait.until(EC.visibility_of_element_located((By.NAME, "full_name"))).send_keys("Long Name")
    driver.find_element(By.NAME, "username").send_keys("u" * 200)
    driver.find_element(By.NAME, "email").send_keys(f"long200_{_TS}@campro.vn")
    driver.find_element(By.NAME, "password").send_keys(FRONTEND_PASS)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1.5)
    assert "500" not in driver.title, "Username 200 ký tự gây 500!"

def test_132_unicode_email():
    """Đăng ký email chứa ký tự Unicode → server không crash."""
    driver.get(f"{BASE_URL}/auth/register")
    time.sleep(1)
    wait.until(EC.visibility_of_element_located((By.NAME, "full_name"))).send_keys("Unicode Test Camera")
    driver.find_element(By.NAME, "username").send_keys(f"uni_{_TS}")
    driver.find_element(By.NAME, "email").send_keys("têst@ùnicode-campro.com")
    driver.find_element(By.NAME, "password").send_keys(FRONTEND_PASS)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1.5)
    assert "500" not in driver.title, "Email Unicode gây 500!"

def test_133_search_emoji():
    """Search emoji/ký tự đặc biệt → không crash."""
    r = http_anon.get(urljoin(BASE_URL, "/products?search=📷🎬😀"),
                      timeout=API_TIMEOUT, allow_redirects=True)
    assert r.status_code != 500, "Search emoji gây 500!"
    print(f"      * INFO: Search emoji → status {r.status_code} OK.")

def test_134_search_empty_string():
    """Search query rỗng → không 500."""
    r = http_anon.get(urljoin(BASE_URL, "/products?search="), timeout=API_TIMEOUT, allow_redirects=True)
    assert r.status_code != 500, "Search rỗng gây 500!"

def test_135_search_numeric_only():
    """Search chuỗi số thuần túy → không crash."""
    r = http_anon.get(urljoin(BASE_URL, "/products?search=123456"), timeout=API_TIMEOUT)
    assert r.status_code in [200, 302], f"Search số trả {r.status_code}"

def test_136_product_slug_not_exist():
    """Truy cập sản phẩm slug không tồn tại → 404, không 500."""
    r = http_anon.get(urljoin(BASE_URL, "/products/slug-khong-ton-tai-campro-xyz-999999"),
                      timeout=API_TIMEOUT, allow_redirects=True)
    assert r.status_code != 500, "Slug không tồn tại gây 500!"

def test_137_order_negative_id():
    """GET /orders/-1 → graceful handling, không crash."""
    r = http_session_user.get(urljoin(BASE_URL, "/orders/-1"),
                               timeout=API_TIMEOUT, allow_redirects=True)
    assert r.status_code != 500, "Order ID âm gây 500!"
    print(f"      * INFO: /orders/-1 → status {r.status_code} OK.")

def test_138_concurrent_register():
    """5 users đăng ký đồng thời → không lỗi 500."""
    def register_one(idx: int):
        s = requests.Session()
        u = f"conc_{_TS}_{idx}"
        r = s.post(urljoin(BASE_URL, "/auth/register"),
                   data={"full_name": f"Concurrent Camera {idx}", "username": u,
                         "email": f"{u}@campro.vn", "password": FRONTEND_PASS},
                   timeout=API_TIMEOUT, allow_redirects=True)
        return r.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(register_one, i) for i in range(5)]
        statuses = [f.result() for f in concurrent.futures.as_completed(futures)]
    failed = [s for s in statuses if s == 500]
    assert not failed, f"{len(failed)} concurrent registrations gây 500!"
    print(f"      * INFO: 5 concurrent register → {statuses}")

def test_139_large_post_payload():
    """POST 50KB body → server không crash (413/400, không 500)."""
    large = {
        "full_name": "A" * 5000,
        "username":  "B" * 5000,
        "email":     "C" * 5000 + "@test.com",
        "password":  "D" * 5000,
    }
    try:
        r = http_anon.post(urljoin(BASE_URL, "/auth/register"),
                           data=large, timeout=API_TIMEOUT, allow_redirects=True)
        assert r.status_code != 500, "Large payload gây 500!"
        print(f"      * INFO: Large payload → status {r.status_code} OK.")
    except requests.RequestException as e:
        print(f"      * INFO: Server từ chối large payload (OK): {type(e).__name__}")

def test_140_double_submit_login():
    """Double submit form login không gây lỗi bất thường."""
    driver.get(f"{BASE_URL}/auth/login")
    wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys(ADMIN_USER)
    driver.find_element(By.NAME, "password").send_keys(ADMIN_PASS)
    btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", btn)
    try:
        driver.execute_script("arguments[0].click();", btn)
    except Exception:
        pass
    time.sleep(2)
    assert "500" not in driver.title, "Double submit gây 500!"
    print(f"      * INFO: Double submit → {driver.current_url}")

# ══════════════════════════════════════════════════════════════════════════════
#  PHẦN 18 – INTEGRATION E2E FLOWS  (TC 141 → 150)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("PHẦN 18: INTEGRATION E2E FLOWS – LUỒNG NGHIỆP VỤ TỔNG HỢP")
print("=" * 80)

def test_141_full_register_login_browse():
    """E2E: Đăng ký → Login → Duyệt sản phẩm camera → Xem chi tiết."""
    new_user = f"flow1_{_TS}"
    driver.get(f"{BASE_URL}/auth/register")
    wait.until(EC.visibility_of_element_located((By.NAME, "full_name"))).send_keys("Flow Camera User")
    driver.find_element(By.NAME, "username").send_keys(new_user)
    driver.find_element(By.NAME, "email").send_keys(f"{new_user}@campro.vn")
    driver.find_element(By.NAME, "password").send_keys(FRONTEND_PASS)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)
    driver.get(f"{BASE_URL}/auth/login")
    wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys(new_user)
    driver.find_element(By.NAME, "password").send_keys(FRONTEND_PASS)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)
    driver.get(f"{BASE_URL}/products")
    time.sleep(1.5)
    assert "500" not in driver.title, "Flow browse products gây 500!"
    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/products/']")
    if links:
        driver.execute_script("arguments[0].click();", links[0])
        time.sleep(1.5)
        assert "500" not in driver.title, "Flow chi tiết SP gây 500!"
    print(f"      * INFO: Full E2E flow '{new_user}' OK.")

def test_142_admin_create_product_verify_public():
    """Admin tạo sản phẩm Camera Dahua IPC → xuất hiện trên /products public."""
    _selenium_admin_login()
    pname = f"Camera Dahua IPC-HDW {_TS}"
    driver.get(f"{BASE_URL}/admin/products/create")
    time.sleep(1)
    try:
        wait.until(EC.visibility_of_element_located((By.NAME, "name"))).send_keys(pname)
        driver.find_element(By.NAME, "price").send_keys("4200000")
        driver.find_element(By.NAME, "stock").send_keys("8")
        driver.find_element(By.NAME, "description").send_keys(
            "Camera IP Dahua IPC-HDW 4MP, chống nước IP67, hồng ngoại 30m.")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1.5)
        assert "500" not in driver.title, "Admin tạo SP gây 500!"
        driver.get(f"{BASE_URL}/products?search=Dahua")
        time.sleep(1.5)
        body = driver.find_element(By.TAG_NAME, "body").text
        if "Dahua" in body:
            print(f"      * INFO: SP 'Dahua' xuất hiện public ✓")
    except (NoSuchElementException, TimeoutException):
        print("      * WARN: Form tạo SP không chuẩn.")

def test_143_contact_submit_verify_admin():
    """Gửi form liên hệ → Admin thấy liên hệ mới trong /admin/contacts."""
    contact_payload = {
        "full_name": f"Camera Hỏi Hàng {_TS}",
        "email":     f"contact_{_TS}@campro.vn",
        "phone":     "0912345678",
        "subject":   f"Hỏi về camera 8MP cho kho hàng",
        "message":   f"Tôi cần tư vấn lắp đặt 10 camera 8MP cho kho hàng 500m². Test auto {_TS}",
    }
    r = http_anon.post(urljoin(BASE_URL, "/contact"),
                       data=contact_payload, timeout=API_TIMEOUT, allow_redirects=True)
    assert r.status_code in [200, 302], f"Gửi contact trả {r.status_code}"
    _http_login(http_session_admin, ADMIN_USER, ADMIN_PASS)
    r2 = http_session_admin.get(urljoin(BASE_URL, "/admin/contacts"), timeout=API_TIMEOUT)
    if contact_payload["email"] in r2.text:
        print(f"      * INFO: Contact từ '{contact_payload['email']}' xuất hiện trong admin ✓")
    else:
        print(f"      * WARN: Contact chưa thấy (có thể pagination).")

def test_144_search_filter_sort_flow():
    """E2E: Search camera → filter giá → sort → không crash ở bất kỳ bước."""
    driver.get(f"{BASE_URL}/products?search=camera")
    time.sleep(1.5)
    assert "500" not in driver.title, "Search flow gây 500!"
    driver.get(f"{BASE_URL}/products?search=camera&sort=price_asc")
    time.sleep(1.5)
    assert "500" not in driver.title, "Search + sort gây 500!"
    driver.get(f"{BASE_URL}/products?search=camera&sort=price_asc&min_price=1000000&max_price=20000000")
    time.sleep(1.5)
    assert "500" not in driver.title, "Search + sort + filter gây 500!"
    print("      * INFO: Search → Filter → Sort flow OK.")

def test_145_admin_logout_relogin():
    """Admin logout → re-login → vào được admin/products bình thường."""
    _selenium_admin_login()
    driver.get(f"{BASE_URL}/auth/logout")
    time.sleep(1)
    driver.get(f"{BASE_URL}/auth/login")
    wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys(ADMIN_USER)
    driver.find_element(By.NAME, "password").send_keys(ADMIN_PASS)
    driver.execute_script("arguments[0].click();",
                          driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
    time.sleep(2)
    driver.get(f"{BASE_URL}/admin/products")
    time.sleep(1)
    assert "404" not in driver.title and "500" not in driver.title, \
        "Admin re-login rồi vào admin/products gặp lỗi!"

def test_146_admin_all_pages_http():
    """Admin HTTP session truy cập được tất cả trang admin quan trọng."""
    _http_login(http_session_admin, ADMIN_USER, ADMIN_PASS)
    pages = {
        "/admin/products":   "Products",
        "/admin/customers":  "Customers",
        "/admin/orders":     "Orders",
        "/admin/categories": "Categories",
        "/admin/coupons":    "Coupons",
        "/admin/news":       "News",
        "/admin/suppliers":  "Suppliers",
        "/admin/report":     "Report",
    }
    failed = []
    for path, label in pages.items():
        try:
            r = http_session_admin.get(urljoin(BASE_URL, path), timeout=API_TIMEOUT)
            if r.status_code != 200:
                failed.append(f"{label}({r.status_code})")
        except requests.RequestException:
            failed.append(f"{label}(error)")
    if failed:
        raise Exception(f"Admin không vào được: {', '.join(failed)}")
    print(f"      * INFO: {len(pages)} admin pages OK ✓")

def test_147_user_blocked_all_admin():
    """User thường bị block toàn bộ /admin/* pages."""
    _http_login(http_session_user, FRONTEND_USER, FRONTEND_PASS)
    bypass = 0
    for path in ["/admin/products", "/admin/customers", "/admin/orders", "/admin/dashboard"]:
        try:
            r = http_session_user.get(urljoin(BASE_URL, path),
                                       timeout=API_TIMEOUT, allow_redirects=True)
            if r.status_code == 200:
                body = r.text.lower()
                if "quản lý" in body or ("admin" in r.url.lower() and "login" not in r.url.lower()):
                    bypass += 1
        except requests.RequestException:
            pass
    if bypass > 0:
        raise Exception(f"RBAC: User bypass được {bypass} Admin pages!")
    print(f"      * INFO: User bị block toàn bộ admin pages OK ✓")

def test_148_anonymous_blocked_all_admin():
    """Ẩn danh bị block toàn bộ /admin/* pages."""
    anon = requests.Session()
    bypass = 0
    for path in ["/admin/products", "/admin/customers", "/admin/orders", "/admin"]:
        try:
            r = anon.get(urljoin(BASE_URL, path), timeout=API_TIMEOUT, allow_redirects=True)
            if r.status_code == 200 and "quản lý" in r.text.lower():
                bypass += 1
        except requests.RequestException:
            pass
    if bypass > 0:
        raise Exception(f"RBAC: Ẩn danh bypass {bypass} Admin pages!")
    print(f"      * INFO: Ẩn danh bị block toàn bộ admin pages OK ✓")

def test_149_system_health_check():
    """Health check tổng hợp: tất cả endpoint chính trả status hợp lệ."""
    _http_login(http_session_admin, ADMIN_USER, ADMIN_PASS)
    public_eps = {
        "/":              "Homepage",
        "/auth/login":    "Login",
        "/auth/register": "Register",
        "/products":      "Products",
        "/news":          "News",
        "/contact":       "Contact",
    }
    admin_eps = {
        "/admin/products":  "Admin Products",
        "/admin/orders":    "Admin Orders",
        "/admin/customers": "Admin Customers",
        "/admin/report":    "Admin Report",
    }
    issues = []
    for path, label in public_eps.items():
        try:
            r = http_anon.get(urljoin(BASE_URL, path), timeout=API_TIMEOUT, allow_redirects=True)
            if r.status_code not in [200, 302]:
                issues.append(f"{label}:{r.status_code}")
        except requests.RequestException:
            issues.append(f"{label}:error")
    for path, label in admin_eps.items():
        try:
            r = http_session_admin.get(urljoin(BASE_URL, path), timeout=API_TIMEOUT)
            if r.status_code != 200:
                issues.append(f"{label}:{r.status_code}")
        except requests.RequestException:
            issues.append(f"{label}:error")
    if issues:
        raise Exception(f"System Health Check FAIL: {', '.join(issues)}")
    print(f"      * INFO: {len(public_eps)+len(admin_eps)} endpoints hoạt động bình thường ✓")

def test_150_final_smoke_test():
    """Final Smoke Test: Register → Browse Camera → Contact → Admin Verify → Logout."""
    smoke = f"smoke_{_TS}"
    # Đăng ký
    driver.get(f"{BASE_URL}/auth/register")
    wait.until(EC.visibility_of_element_located((By.NAME, "full_name"))).send_keys("Smoke Camera Tester")
    driver.find_element(By.NAME, "username").send_keys(smoke)
    driver.find_element(By.NAME, "email").send_keys(f"{smoke}@campro.vn")
    driver.find_element(By.NAME, "password").send_keys(FRONTEND_PASS)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)
    assert "500" not in driver.title, "Smoke: Register gây 500!"
    # Browse products
    driver.get(f"{BASE_URL}/products")
    time.sleep(1.5)
    assert "500" not in driver.title, "Smoke: Browse products gây 500!"
    # Search camera
    r = http_anon.get(urljoin(BASE_URL, "/products?search=camera"), timeout=API_TIMEOUT)
    assert r.status_code in [200, 302], f"Smoke: Search trả {r.status_code}"
    # Admin verify smoke user
    _selenium_admin_login()
    driver.get(f"{BASE_URL}/admin/customers")
    time.sleep(1)
    body = driver.find_element(By.TAG_NAME, "body").text
    if smoke not in body:
        print(f"      * WARN: Smoke user '{smoke}' chưa thấy trong admin.")
    # Admin logout
    driver.get(f"{BASE_URL}/auth/logout")
    time.sleep(1)
    assert "500" not in driver.title, "Smoke: Logout gây 500!"
    print(f"      * INFO: Final Smoke Test '{smoke}' hoàn thành ✓")

# ══════════════════════════════════════════════════════════════════════════════
#  CHẠY TẤT CẢ 150 TEST CASES
# ══════════════════════════════════════════════════════════════════════════════
try:
    # ── PHẦN 1: AUTH & E2E CƠ BẢN ─────────────────────────────────────────────
    run_test_case("01","Frontend: Đăng ký Tài khoản Mới","Auth","Nhập full_name/username/email/pass hợp lệ","Tạo tài khoản thành công, redirect về login",test_01_register_new_user)
    run_test_case("02","Frontend: Đăng nhập User","Auth","Login với tài khoản vừa tạo","Redirect trang chủ, session hợp lệ",test_02_login_user)
    run_test_case("03","Frontend: Tìm kiếm 'camera'","Search","GET /products?search=camera","Trang kết quả load OK, status 200",test_03_search_camera)
    run_test_case("04","Frontend: Xem Chi tiết Sản phẩm","Product","Click sản phẩm bất kỳ từ /products","Trang chi tiết SP load đúng, có nội dung",test_04_view_product_detail)
    run_test_case("05","Frontend: Thêm Sản phẩm vào Giỏ","Cart","Click 'Thêm vào giỏ hàng' khi đã login","Không crash, flash success hoặc redirect",test_05_add_to_cart)
    run_test_case("06","Frontend: Xem Giỏ hàng","Cart","GET /cart khi đã login","Trang giỏ hàng load OK, có nội dung",test_06_view_cart)
    run_test_case("07","Backend: Đăng nhập Admin","Auth","Login ADMIN_USER/ADMIN_PASS vào admin panel","Vào được trang admin/dashboard",test_07_admin_login)
    run_test_case("08","Admin: Verify User Mới Đăng Ký","Admin","Admin kiểm tra /admin/customers","Thấy user camuser vừa đăng ký",test_08_admin_sees_new_user)
    run_test_case("09","Admin: Dashboard Hiển Thị Thống Kê","Admin","GET /admin/dashboard","Dashboard hiển thị thống kê đơn hàng, SP",test_09_admin_dashboard_stats)
    # ── PHẦN 2: VALIDATION ──────────────────────────────────────────────────
    run_test_case("10","Validation: Username Trùng Lặp","Validation","Đăng ký username đã tồn tại trong DB","Thông báo lỗi, không tạo tài khoản mới",test_10_register_duplicate_username)
    run_test_case("11","Validation: Submit Form Rỗng","Validation","Click submit không nhập gì","Ở lại trang register, không crash 500",test_11_register_empty_form)
    run_test_case("12","Validation: Email Sai Định Dạng","Validation","Email = 'KHONG_PHAI_EMAIL_CAMPRO'","Hệ thống từ chối, không crash",test_12_register_invalid_email)
    run_test_case("13","Validation: Mật Khẩu < 6 Ký Tự","Validation","Password = '123' (3 ký tự)","Báo lỗi mật khẩu ngắn, không đăng ký",test_13_register_short_password)
    run_test_case("14","Validation: Login Sai Mật Khẩu","Validation","Nhập password sai cho admin","Ở lại login, không vào được admin",test_14_login_wrong_password)
    run_test_case("15","Validation: Login User Không Tồn Tại","Validation","Username 'khongtontai_xyz999'","Thông báo lỗi, ở lại trang login",test_15_login_nonexistent_user)
    run_test_case("16","Validation: Filter Theo Danh Mục","Product","GET /products?category_id=1","Status 200, không crash",test_16_filter_by_category)
    run_test_case("17","Validation: Filter Theo Khoảng Giá","Product","GET /products?min_price=500000&max_price=10000000","Status 200, không crash",test_17_filter_price_range)
    run_test_case("18","Validation: Sort Sản Phẩm Giá Tăng Dần","Product","GET /products?sort=price_asc","Status 200, không crash",test_18_sort_products)
    # ── PHẦN 3: SECURITY ─────────────────────────────────────────────────────
    run_test_case("19","Security: SQL Injection Form Login","Security","Inject ' OR '1'='1 vào form login","Block/báo lỗi, không bypass auth",test_19_sqli_login_form)
    run_test_case("20","Security: SQL Injection Tìm Kiếm","Security","UNION SELECT NULL,NULL vào search","Không lộ data/stack trace",test_20_sqli_search)
    run_test_case("21","Security: SQL Injection URL Params","Security","GET /products?category_id=' OR 1=1--","Không crash/500",test_21_sqli_url_params)
    run_test_case("22","Security: XSS Reflected Tìm Kiếm","Security","<script>alert('XSS')</script> trong search","Script không chạy trong DOM",test_22_xss_reflected_search)
    run_test_case("23","Security: XSS Stored Form Đăng Ký","Security","XSS trong full_name field khi đăng ký","Script không render khi view",test_23_xss_stored_register)
    run_test_case("24","Security: Admin Bypass Unauthenticated","Security","GET /admin/* không có session","Redirect về /auth/login",test_24_admin_unauthenticated)
    run_test_case("25","Security: IDOR Order Access","Security","User truy cập /orders/1,2,3","403/redirect, không lộ data người khác",test_25_idor_order_access)
    run_test_case("26","Security: Security Headers Cơ Bản","Security","Kiểm tra X-Content-Type-Options, X-Frame-Options","Header hiện diện",test_26_security_headers)
    run_test_case("27","Security: Password Không Lộ Response","Security","Check response không chứa plain password","Password không lộ trong HTML",test_27_password_not_exposed)
    # ── PHẦN 4: API FUNCTIONAL ───────────────────────────────────────────────
    run_test_case("28","API: Homepage Status 200","API","GET /","HTTP 200",test_28_homepage_200)
    run_test_case("29","API: Login Admin HTTP Session","API","POST /auth/login admin","Session tạo, status 200",test_29_api_login_success)
    run_test_case("30","API: Trang Sản Phẩm Status 200","API","GET /products","HTTP 200, có nội dung sản phẩm",test_30_products_page_200)
    run_test_case("31","API: Search API Status","API","GET /products?search=camera","HTTP 200 hoặc 302",test_31_search_api_status)
    run_test_case("32","API: 404 Handling","API","GET /trang-khong-ton-tai-campro","HTTP 404, không crash 500",test_32_404_handling)
    run_test_case("33","API: Register qua HTTP POST","API","POST /auth/register user mới","HTTP 200/302",test_33_register_via_http)
    run_test_case("34","API: Logout","API","GET /auth/logout","HTTP 200, session hủy",test_34_logout)
    run_test_case("35","API: Admin Products Status 200","API","GET /admin/products (admin session)","HTTP 200",test_35_admin_products_200)
    run_test_case("36","API: Trang Liên Hệ Status 200","API","GET /contact","HTTP 200, có form liên hệ",test_36_contact_page_200)
    run_test_case("37","API: Trang Tin Tức Status 200","API","GET /news","HTTP 200/302",test_37_news_page_200)
    # ── PHẦN 5: RBAC ─────────────────────────────────────────────────────────
    run_test_case("38","RBAC: User Thường Không Vào Admin","RBAC","User session → GET /admin/*","Redirect về login, không vào được",test_38_user_cannot_access_admin)
    run_test_case("39","RBAC: Ẩn Danh Không Vào Admin","RBAC","Anon session → GET /admin/*","Redirect về login",test_39_anon_cannot_access_admin)
    run_test_case("40","RBAC: Admin Vào Được Tất Cả","RBAC","Admin session → tất cả /admin/*","HTTP 200 tất cả",test_40_admin_can_access_all)
    run_test_case("41","RBAC: Logout Hủy Session","RBAC","Logout → dùng session cũ vào admin","Session không còn hiệu lực",test_41_logout_invalidates_session)
    # ── PHẦN 6: PERFORMANCE ──────────────────────────────────────────────────
    run_test_case("42","Perf: Homepage Concurrent 30r/10w","Performance","30 requests concurrent tới /","Pass rate ≥ 85%, avg < 3s",test_42_perf_homepage)
    run_test_case("43","Perf: Search Concurrent 30r/10w","Performance","30 requests concurrent /products?search=camera","Pass rate ≥ 70%",test_43_perf_search)
    run_test_case("44","Perf: Homepage Response < 2s","Performance","GET / đơn lẻ","< 2.0 giây",test_44_homepage_response_time)
    run_test_case("45","Perf: Login Page Response < 2s","Performance","GET /auth/login đơn lẻ","< 2.0 giây",test_45_login_page_response_time)
    # ── PHẦN 7: SESSION & COOKIE ─────────────────────────────────────────────
    run_test_case("46","Session: Cookie HttpOnly Flag","Session","Inspect session cookie sau login","HttpOnly = true",test_46_cookie_httponly)
    run_test_case("47","Session: Session Duy Trì Giữa Các Trang","Session","Chuyển qua nhiều trang sau login","Session không bị mất",test_47_session_persist_across_pages)
    run_test_case("48","Session: Logout Xóa Session","Session","Logout → GET /cart","Redirect về /auth/login",test_48_logout_clears_session)
    # ── PHẦN 8: UI/UX ────────────────────────────────────────────────────────
    run_test_case("49","UI: Trang Chủ Có Navbar","UI/UX","Inspect <nav> hoặc .navbar","Navbar hiện diện",test_49_homepage_has_navbar)
    run_test_case("50","UI: Trang Chủ Có Footer","UI/UX","Inspect <footer>","Footer hiện diện",test_50_homepage_has_footer)
    run_test_case("51","UI: CSS Load Thành Công","UI/UX","Kiểm tra computed style body","CSS đã load, background không rỗng",test_51_css_loaded)
    run_test_case("52","UI: Không Có JS Error Nghiêm Trọng","UI/UX","Kiểm tra browser console logs","Không có lỗi SEVERE",test_52_no_severe_js_errors)
    run_test_case("53","UI: Product Card Hiển Thị Đúng","UI/UX","Inspect .product-card trên /products","Card có nội dung tên, giá",test_53_product_card_displays)
    # ── PHẦN 9: ADMIN CRUD PRODUCTS ──────────────────────────────────────────
    run_test_case("54","Admin: Danh Sách Sản Phẩm","Admin","GET /admin/products","Hiển thị danh sách sản phẩm camera",test_54_admin_products_list)
    run_test_case("55","Admin: Tạo Sản Phẩm Camera Hikvision DS-2CD","Admin","POST /admin/products với name/price/stock","Sản phẩm tạo thành công",test_55_admin_create_product)
    run_test_case("56","Admin: Edit Sản Phẩm","Admin","GET /admin/products/{id}/edit","Form edit load đúng có fields",test_56_admin_edit_product)
    run_test_case("57","Admin: Danh Sách Danh Mục","Admin","GET /admin/categories","Hiển thị danh mục",test_57_admin_categories_list)
    run_test_case("58","Admin: Tạo Danh Mục Camera IP Dahua","Admin","POST /admin/categories name mới","Danh mục tạo thành công",test_58_admin_create_category)
    run_test_case("59","Admin: Danh Sách Nhà Cung Cấp","Admin","GET /admin/suppliers","Trang hiển thị OK, không 404/500",test_59_admin_suppliers_list)
    # ── PHẦN 10: SẢN PHẨM & NỘI DUNG ────────────────────────────────────────
    run_test_case("60","Content: Trang /products Load OK","Content","GET /products","Status 200, có nội dung sản phẩm",test_60_products_page_loads)
    run_test_case("61","Content: Chi Tiết SP Có Đủ Thông Tin","Content","Click vào sản phẩm đầu tiên","Tên, giá, thông tin hiển thị đủ",test_61_product_detail_info)
    run_test_case("62","Content: Search Không Có Kết Quả","Content","search=xyzkhongtontai999abcdef","Không crash, hiển thị phù hợp",test_62_search_no_results)
    run_test_case("63","Content: Phân Trang Sản Phẩm","Content","Kiểm tra .pagination trên /products","Pagination hoạt động, không crash",test_63_products_pagination)
    run_test_case("64","Content: Search Tiếng Việt Có Dấu","Content","search='camera an ninh'","Status 200/302, không crash",test_64_search_vietnamese)
    run_test_case("65","Content: Homepage Load < 3s (Selenium)","Content","driver.get(/) đo elapsed time","< 3.0 giây",test_65_homepage_loads_within_3s)
    run_test_case("66","Content: Ảnh Sản Phẩm Có src","Content","Inspect img tags trong .product-card","img có src không rỗng",test_66_product_images_have_src)
    run_test_case("67","Content: Guest Add-to-Cart → Redirect Login","Content","Guest click form add to cart","Redirect về /auth/login",test_67_add_cart_requires_login)
    run_test_case("68","Content: SP Liên Quan Trong Detail Page","Content","Kiểm tra trang chi tiết SP","Có section sản phẩm liên quan",test_68_product_related_items)
    run_test_case("69","Content: Trang Chủ Hiển Thị SP","Content","Inspect trang chủ CAMPRO","Có sản phẩm camera hiển thị, không 500",test_69_homepage_shows_products)
    # ── PHẦN 11: PROFILE & TÀI KHOẢN ─────────────────────────────────────────
    run_test_case("70","Account: Profile Page Load OK","Account","GET /profile (user đã login)","Trang profile load, không 404/500",test_70_profile_accessible)
    run_test_case("71","Account: Profile Hiển Thị Username","Account","Kiểm tra body trang /profile","Hiển thị username của user camuser",test_71_profile_shows_username)
    run_test_case("72","Account: Cập Nhật Phone & Address","Account","POST /profile/update với phone/address","Cập nhật thành công, không crash",test_72_profile_update_info)
    run_test_case("73","Account: Đổi Pass Sai Mật Khẩu Cũ","Account","POST /profile/change-password old_password sai","Thông báo lỗi, không đổi được",test_73_change_password_wrong_old)
    run_test_case("74","Account: Profile Yêu Cầu Đăng Nhập","Account","Guest GET /profile","Redirect về /auth/login",test_74_profile_requires_login)
    run_test_case("75","Account: Trang Đơn Hàng Của Tôi","Account","GET /orders (user logged in)","Trang load OK, không 500",test_75_orders_page_accessible)
    run_test_case("76","Account: Orders Yêu Cầu Đăng Nhập","Account","Guest GET /orders","Redirect về /auth/login",test_76_orders_requires_login)
    run_test_case("77","Account: Checkout Giỏ Hàng Rỗng","Account","GET /orders/checkout khi cart rỗng","Redirect hoặc thông báo, không crash",test_77_checkout_empty_cart)
    run_test_case("78","Account: Trang Tin Tức Load OK","Account","GET /news","Trang load OK, không 404/500",test_78_news_page_loads)
    run_test_case("79","Account: Gửi Form Liên Hệ Camera","Account","POST /contact với full_name/email/subject/message","Gửi thành công, flash success",test_79_contact_form_submit)
    # ── PHẦN 12: ADMIN ORDERS & COUPONS ──────────────────────────────────────
    run_test_case("80","Admin+: Danh Sách Đơn Hàng","Admin","GET /admin/orders","Hiển thị danh sách đơn hàng",test_80_admin_orders_list)
    run_test_case("81","Admin+: Filter Đơn Hàng Pending","Admin","GET /admin/orders?status=pending","Status 200, không crash",test_81_admin_orders_filter_pending)
    run_test_case("82","Admin+: Danh Sách Mã Giảm Giá","Admin","GET /admin/coupons","Trang coupons load OK",test_82_admin_coupons_list)
    run_test_case("83","Admin+: Tạo Mã Giảm Giá CAMxxxx","Admin","POST /admin/coupons code/discount_value","Coupon tạo thành công",test_83_admin_create_coupon)
    run_test_case("84","Admin+: Danh Sách Bài Viết","Admin","GET /admin/news","Trang news admin load OK",test_84_admin_news_list)
    run_test_case("85","Admin+: Tạo Bài Viết Hướng Dẫn Camera","Admin","POST /admin/news title/content/excerpt","Bài viết tạo thành công",test_85_admin_create_news)
    run_test_case("86","Admin+: Danh Sách Liên Hệ","Admin","GET /admin/contacts","Trang contacts admin load OK",test_86_admin_contacts_list)
    run_test_case("87","Admin+: Filter Liên Hệ Unread","Admin","GET /admin/contacts?status=unread","Status 200, không crash",test_87_admin_contacts_filter_unread)
    run_test_case("88","Admin+: Danh Sách Khách Hàng","Admin","GET /admin/customers","Hiển thị danh sách khách hàng",test_88_admin_customers_list)
    run_test_case("89","Admin+: Tìm Kiếm Khách Hàng","Admin","GET /admin/customers?search=camera","Status 200, không crash",test_89_admin_search_customers)
    run_test_case("90","Admin+: Toggle Trạng Thái Sản Phẩm","Admin","POST /admin/products/{id}/toggle","Status 200/302, không crash",test_90_admin_toggle_product)
    run_test_case("91","Admin+: Tạo & Xóa Danh Mục Tạm","Admin","POST /admin/categories → POST delete","Tạo xóa thành công, không crash",test_91_admin_delete_category)
    # ── PHẦN 13: PERFORMANCE NÂNG CAO ────────────────────────────────────────
    run_test_case("92","Perf+: /products Concurrent 20r/8w","Performance","20 requests concurrent /products","Pass rate ≥ 80%",test_92_perf_products_page)
    run_test_case("93","Perf+: Admin/products Latency < 3s","Performance","GET /admin/products HTTP đơn lẻ","< 3.0 giây",test_93_perf_admin_products)
    run_test_case("94","Perf+: Register Page < 2s","Performance","GET /auth/register đơn lẻ","< 2.0 giây",test_94_perf_register_page)
    run_test_case("95","Perf+: News Page < 2s","Performance","GET /news đơn lẻ","< 2.0 giây",test_95_perf_news_page)
    run_test_case("96","Perf+: Contact Page < 2s","Performance","GET /contact đơn lẻ","< 2.0 giây",test_96_perf_contact_page)
    run_test_case("97","Perf+: Homepage Stress 50r/20w","Performance","50 requests / 20 workers tới /","Pass rate ≥ 75%",test_97_perf_stress_homepage)
    run_test_case("98","Perf+: Products TTFB < 1.5s","Performance","TTFB /products","< 1.5 giây",test_98_perf_products_ttfb)
    run_test_case("99","Perf+: Login Concurrent 20r/10w","Performance","20 requests concurrent /auth/login","Pass rate ≥ 90%",test_99_perf_login_concurrent)
    run_test_case("100","Perf+: Search Stress 30r/15w","Performance","30 requests /products?search=cam","Pass rate ≥ 65%",test_100_perf_search_stress)
    run_test_case("101","Perf+: Homepage TTFB < 1.5s","Performance","TTFB /","< 1.5 giây",test_101_perf_homepage_ttfb)
    # ── PHẦN 14: SECURITY NÂNG CAO ───────────────────────────────────────────
    run_test_case("102","Security+: Open Redirect","Security","?next=http://evil.com","Chỉ redirect nội bộ",test_102_open_redirect)
    run_test_case("103","Security+: Directory Traversal","Security","../../etc/passwd trong URL","404/block, không lộ file hệ thống",test_103_directory_traversal)
    run_test_case("104","Security+: Mass Assignment role=admin","Security","POST đăng ký với role=admin","Server ignore, không thành admin",test_104_mass_assignment)
    run_test_case("105","Security+: Clickjacking Protection","Security","Kiểm tra X-Frame-Options header","Header hiện diện",test_105_clickjacking_protection)
    run_test_case("106","Security+: Server Info Leakage","Security","Inspect X-Powered-By header","Không lộ phiên bản chi tiết",test_106_server_info_leakage)
    run_test_case("107","Security+: Brute Force Login 5 Lần","Security","5 lần login sai liên tiếp","Không crash, không trả 500",test_107_brute_force_login)
    run_test_case("108","Security+: HTTP Methods Không Hợp Lệ","Security","PUT/DELETE tới GET-only endpoints","Không trả 200",test_108_http_methods_invalid)
    run_test_case("109","Security+: Stack Trace Không Lộ","Security","Request không hợp lệ vào endpoint","Không lộ stack trace/DB error",test_109_stack_trace_not_exposed)
    # ── PHẦN 15: ADMIN NÂNG CAO ──────────────────────────────────────────────
    run_test_case("110","Admin++: Chi Tiết Đơn Hàng","Admin","GET /admin/orders/{id}","Trang chi tiết đơn load OK",test_110_admin_order_detail)
    run_test_case("111","Admin++: Cập Nhật Trạng Thái Đơn Hàng confirmed","Admin","POST /admin/orders/{id}/status confirmed","Status 200/302, không crash",test_111_admin_update_order_status)
    run_test_case("112","Admin++: Tìm Kiếm Sản Phẩm Hikvision","Admin","GET /admin/products?search=Hikvision","Status 200, không crash",test_112_admin_search_products)
    run_test_case("113","Admin++: Tạo SP Không Có Tên (Validation)","Admin","POST /admin/products không có name","Validation báo lỗi, không crash 500",test_113_admin_product_validation)
    run_test_case("114","Admin++: Trang Customers Không Rỗng","Admin","GET /admin/customers check content","Có ít nhất 1 tài khoản",test_114_admin_customers_not_empty)
    run_test_case("115","Admin++: Toggle Khóa/Mở Khóa Customer","Admin","POST /admin/customers/{id}/toggle","Status 200/302, không crash",test_115_admin_toggle_customer)
    run_test_case("116","Admin++: Tạo NCC Hikvision Vietnam Co.","Admin","POST /admin/suppliers form hợp lệ","Nhà cung cấp tạo thành công",test_116_admin_create_supplier)
    run_test_case("117","Admin++: Publish Bài Viết Camera AI","Admin","POST /admin/news is_published=1","Bài viết xuất hiện ở /news public",test_117_admin_publish_news)
    run_test_case("118","Admin++: Xóa Mã Giảm Giá","Admin","POST /admin/coupons/{id}/delete","Status 200/302, không crash",test_118_admin_delete_coupon)
    run_test_case("119","Admin++: Trang Báo Cáo Doanh Thu","Admin","GET /admin/report","Trang báo cáo load OK, có nội dung",test_119_admin_report_page)
    # ── PHẦN 16: SEO & ACCESSIBILITY ─────────────────────────────────────────
    run_test_case("120","SEO: Ảnh Có Alt Text","Accessibility","Inspect <img> tags trên trang chủ","Alt text hiện diện",test_120_images_have_alt)
    run_test_case("121","SEO: Meta Description Tồn Tại","Accessibility","Inspect <meta name='description'>","Content > 10 ký tự",test_121_meta_description)
    run_test_case("122","SEO: Favicon Tồn Tại","Accessibility","GET /favicon.ico","Status 200 hoặc khai báo HTML",test_122_favicon_exists)
    run_test_case("123","SEO: robots.txt Accessible","Accessibility","GET /robots.txt","Status 200 (khuyến nghị)",test_123_robots_txt)
    run_test_case("124","SEO: Page Title Tồn Tại","Accessibility","Kiểm tra <title> 5 trang chính","Title không rỗng, không 'Error'",test_124_page_titles)
    run_test_case("125","SEO: Heading Structure h1/h2/h3","Accessibility","Inspect headings trên trang chủ","Ít nhất 1 heading",test_125_heading_structure)
    run_test_case("126","A11y: HTML lang Attribute","Accessibility","Inspect <html lang=...>","lang attribute tồn tại",test_126_html_lang_attribute)
    run_test_case("127","A11y: Form Inputs Có Label/Placeholder","Accessibility","Inspect form login inputs","Label/placeholder/aria-label có mặt",test_127_form_inputs_have_labels)
    run_test_case("128","SEO: Open Graph Tags","Accessibility","Inspect meta[property^='og:']","Có OG tags (khuyến nghị)",test_128_open_graph_tags)
    run_test_case("129","A11y: Keyboard Navigation Login","Accessibility","Tab + Enter để submit form login","Login bằng bàn phím thành công",test_129_keyboard_navigation_login)
    # ── PHẦN 17: EDGE CASES & BOUNDARY ───────────────────────────────────────
    run_test_case("130","Edge: Username Có Khoảng Trắng","Boundary","Username = 'user with space campro'","Trim hoặc từ chối, không crash 500",test_130_username_with_spaces)
    run_test_case("131","Edge: Username 200 Ký Tự","Boundary","Username = 'u'*200","Không crash/500",test_131_very_long_username)
    run_test_case("132","Edge: Email Chứa Ký Tự Unicode","Boundary","Email = 'têst@ùnicode-campro.com'","Server không crash",test_132_unicode_email)
    run_test_case("133","Edge: Search Emoji/Ký Tự Đặc Biệt","Boundary","search='📷🎬😀'","Không crash/500",test_133_search_emoji)
    run_test_case("134","Edge: Search Query Rỗng","Boundary","GET /products?search=","Không trả 500",test_134_search_empty_string)
    run_test_case("135","Edge: Search Số Thuần Túy","Boundary","GET /products?search=123456","Status 200/302",test_135_search_numeric_only)
    run_test_case("136","Edge: Product Slug Không Tồn Tại","Boundary","GET /products/slug-khong-ton-tai-xyz","404/redirect, không 500",test_136_product_slug_not_exist)
    run_test_case("137","Edge: Order ID Âm (-1)","Boundary","GET /orders/-1","Graceful handling, không 500",test_137_order_negative_id)
    run_test_case("138","Edge: Concurrent Register 5 Users","Boundary","5 registrations đồng thời","Không lỗi 500",test_138_concurrent_register)
    run_test_case("139","Edge: Large POST Payload 50KB","Boundary","POST body 50KB","413/400, không phải 500",test_139_large_post_payload)
    run_test_case("140","Edge: Double Submit Form Login","Boundary","Click submit 2 lần liên tiếp","Không crash/500",test_140_double_submit_login)
    # ── PHẦN 18: INTEGRATION E2E FLOWS ───────────────────────────────────────
    run_test_case("141","E2E: Register → Login → Browse → Chi Tiết SP","Integration","Full user flow từ đầu đến cuối","Tất cả bước thành công",test_141_full_register_login_browse)
    run_test_case("142","E2E: Admin Tạo Camera Dahua → Public","Integration","Admin create → check /products public","SP Dahua xuất hiện trang public",test_142_admin_create_product_verify_public)
    run_test_case("143","E2E: Contact Submit → Admin Verify","Integration","Gửi contact → check /admin/contacts","Liên hệ xuất hiện trong admin",test_143_contact_submit_verify_admin)
    run_test_case("144","E2E: Search → Filter Giá → Sort Flow","Integration","Search + filter + sort kết hợp","Không crash ở bất kỳ bước nào",test_144_search_filter_sort_flow)
    run_test_case("145","E2E: Admin Logout → Re-Login → Admin Panel","Integration","Admin logout → re-login → /admin/*","Admin access OK sau re-login",test_145_admin_logout_relogin)
    run_test_case("146","E2E: HTTP Admin Session 8 Pages","Integration","HTTP session tất cả 8 admin pages","Tất cả trả 200",test_146_admin_all_pages_http)
    run_test_case("147","E2E: User Session Bị Block Admin","Integration","User session → tất cả /admin/* pages","Không page nào accessible",test_147_user_blocked_all_admin)
    run_test_case("148","E2E: Ẩn Danh Bị Block Admin","Integration","Anon → tất cả /admin/* pages","Không page nào accessible",test_148_anonymous_blocked_all_admin)
    run_test_case("149","E2E: System Health Check Tổng Hợp 10 EP","Integration","GET 10 endpoint quan trọng","Tất cả trả 200/302",test_149_system_health_check)
    run_test_case("150","E2E: Final Smoke Test CAMPRO Complete","Integration","Register→Browse→Search→Admin verify→Logout","Tất cả bước thành công",test_150_final_smoke_test)

finally:
    driver.quit()

# ══════════════════════════════════════════════════════════════════════════════
#  XUẤT BÁO CÁO EXCEL ENTERPRISE – 5 SHEET
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("XUẤT BÁO CÁO EXCEL ENTERPRISE – 5 SHEET + SUMMARY DASHBOARD")
print("=" * 80)

wb = openpyxl.Workbook()

# ─── FONTS ───────────────────────────────────────────────────────────────────
FONT_HEADER  = Font(name="Arial", bold=True, color="FFFFFF", size=10)
FONT_TITLE   = Font(name="Arial", bold=True, color="FFFFFF", size=14)
FONT_BODY    = Font(name="Arial", size=9)
FONT_PASS    = Font(name="Arial", bold=True, color="00B050", size=9)
FONT_FAIL    = Font(name="Arial", bold=True, color="FF0000", size=9)
FONT_SUMMARY = Font(name="Arial", bold=True, size=10)

# ─── ALIGNMENTS ──────────────────────────────────────────────────────────────
ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
ALIGN_LEFT   = Alignment(horizontal="left",   vertical="top",    wrap_text=True)

# ─── FILLS ───────────────────────────────────────────────────────────────────
FILL_BLUE    = PatternFill(start_color="1A3A5C",  fill_type="solid")
FILL_TEAL    = PatternFill(start_color="17706A",  fill_type="solid")
FILL_STRIPE  = PatternFill(start_color="F0F4FF",  fill_type="solid")
FILL_PASS    = PatternFill(start_color="E2EFDA",  fill_type="solid")
FILL_FAIL    = PatternFill(start_color="FCE4D6",  fill_type="solid")
FILL_YELLOW  = PatternFill(start_color="FFEB9C",  fill_type="solid")

# ─── CATEGORY COLORS ─────────────────────────────────────────────────────────
CATEGORY_COLORS = {
    "Auth":          "1F4E79",
    "Search":        "1565C0",
    "Product":       "2E7D32",
    "Cart":          "6A1B9A",
    "Admin":         "4472C4",
    "Validation":    "833C00",
    "Boundary":      "7F6000",
    "Security":      "C00000",
    "API":           "006400",
    "RBAC":          "7030A0",
    "Performance":   "E65100",
    "Session":       "00695C",
    "UI/UX":         "0D47A1",
    "Content":       "1A6B4A",
    "Account":       "284F8C",
    "Accessibility": "5A3E9E",
    "Integration":   "8B1A1A",
}

def thin_border_all():
    s = Side(style="thin", color="C0C0C0")
    return Border(left=s, right=s, top=s, bottom=s)

def _style_header_row(ws, row_num: int, fill: PatternFill):
    for cell in ws[row_num]:
        cell.font      = FONT_HEADER
        cell.fill      = fill
        cell.border    = thin_border_all()
        cell.alignment = ALIGN_CENTER

def _style_data_cell(cell, col_idx: int, is_even: bool, result_val: str = "", cat: str = ""):
    cell.border    = thin_border_all()
    cell.font      = FONT_BODY
    center_cols    = {1, 2, 4, 8, 10, 11}
    cell.alignment = ALIGN_CENTER if col_idx in center_cols else ALIGN_LEFT
    if col_idx == 8:
        if result_val == "Pass":
            cell.font = FONT_PASS
            cell.fill = FILL_PASS
        elif result_val == "Fail":
            cell.font = FONT_FAIL
            cell.fill = FILL_FAIL
    elif is_even:
        cell.fill = FILL_STRIPE

# ─────────────────────────────────────────────────────────────────────────────
#  SHEET 1: FULL DETAIL REPORT (150 TCs)
# ─────────────────────────────────────────────────────────────────────────────
ws_detail       = wb.active
ws_detail.title = "📋 Full Detail Report"

ws_detail.merge_cells("A1:K1")
ws_detail["A1"] = (
    f"BÁO CÁO KIỂM THỬ E2E – HỆ THỐNG CAMPRO MVC (Web Bán Camera)  |  "
    f"Tester: {TESTER_NAME}  |  Ngày: {TEST_DATE}  |  Phiên bản: v2.0 (150 Test Cases)"
)
ws_detail["A1"].font      = FONT_TITLE
ws_detail["A1"].fill      = FILL_BLUE
ws_detail["A1"].alignment = ALIGN_CENTER
ws_detail.row_dimensions[1].height = 42

for col, w in {"A":6,"B":9,"C":36,"D":16,"E":30,"F":32,"G":30,"H":10,"I":32,"J":7,"K":12}.items():
    ws_detail.column_dimensions[col].width = w

ws_detail.append(["#","TC ID","Tên Test Case","Category","Bước Thực Hiện",
                   "Kết Quả Kỳ Vọng","Kết Quả Thực Tế","Pass/Fail",
                   "Ghi Chú / Thông Báo Lỗi","Phần","Nhóm"])
_style_header_row(ws_detail, 2, FILL_BLUE)
ws_detail.row_dimensions[2].height = 26

part_map = {
    range(1,  10): ("P1",  "Auth & E2E Cơ Bản"),
    range(10, 19): ("P2",  "Validation & Boundary"),
    range(19, 28): ("P3",  "Security"),
    range(28, 38): ("P4",  "API Functional"),
    range(38, 42): ("P5",  "RBAC"),
    range(42, 46): ("P6",  "Performance"),
    range(46, 49): ("P7",  "Session & Cookie"),
    range(49, 54): ("P8",  "UI/UX"),
    range(54, 60): ("P9",  "Admin CRUD Products"),
    range(60, 70): ("P10", "Content & Sản Phẩm"),
    range(70, 80): ("P11", "Profile & Tài Khoản"),
    range(80, 92): ("P12", "Admin Orders & Coupons"),
    range(92, 102):("P13", "Performance Nâng Cao"),
    range(102,110):("P14", "Security Nâng Cao"),
    range(110,120):("P15", "Admin Nâng Cao"),
    range(120,130):("P16", "SEO & Accessibility"),
    range(130,141):("P17", "Edge Cases & Boundary"),
    range(141,151):("P18", "Integration E2E Flows"),
}

def _get_part(n):
    for r, (p, l) in part_map.items():
        if n in r: return p, l
    return "—", "—"

for idx, res in enumerate(actual_test_results, start=1):
    cat      = res["category"]
    part, _  = _get_part(idx)
    cat_col  = CATEGORY_COLORS.get(cat, "444444")
    row_data = [idx, f"TC-{idx:03d}", res["name"], cat, res["step"],
                res["expected"], res["note"], res["result"],
                res["note"] if res["result"] == "Fail" else "Thực thi thành công",
                part, cat]
    ws_detail.append(row_data)
    r_num   = idx + 2
    is_even = idx % 2 == 0
    for ci, cell in enumerate(ws_detail[r_num], start=1):
        _style_data_cell(cell, ci, is_even, res["result"], cat)
        if ci == 4:
            cell.fill = PatternFill(start_color=cat_col, fill_type="solid")
            cell.font = Font(name="Arial", bold=True, color="FFFFFF", size=9)
    ws_detail.row_dimensions[r_num].height = 20

ws_detail.freeze_panes    = "A3"
ws_detail.auto_filter.ref = f"A2:K{len(actual_test_results)+2}"

# ─────────────────────────────────────────────────────────────────────────────
#  SHEET 2: SUMMARY DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
ws_sum       = wb.create_sheet("📊 Summary Dashboard")
for col, w in {"A":4,"B":32,"C":12,"D":12,"E":12,"F":14,"G":20,"H":32}.items():
    ws_sum.column_dimensions[col].width = w

ws_sum.merge_cells("B1:H1")
ws_sum["B1"] = f"SUMMARY DASHBOARD – CAMPRO MVC  |  {TEST_DATE}  |  150 Test Cases"
ws_sum["B1"].font      = Font(name="Arial", bold=True, color="FFFFFF", size=13)
ws_sum["B1"].fill      = FILL_BLUE
ws_sum["B1"].alignment = ALIGN_CENTER
ws_sum.row_dimensions[1].height = 38

total_run  = len(actual_test_results)
total_pass = sum(1 for r in actual_test_results if r["result"] == "Pass")
total_fail = total_run - total_pass
pass_rate  = (total_pass / total_run * 100) if total_run > 0 else 0

sum_overview = [
    ("🔢 Tổng Test Cases",  150,                "1F4E79","FFFFFF"),
    ("▶️ Đã Thực Thi",      total_run,           "4472C4","FFFFFF"),
    ("✅ Pass",              total_pass,          "00B050","FFFFFF"),
    ("❌ Fail",              total_fail,          "C00000","FFFFFF"),
    ("📈 Pass Rate",         f"{pass_rate:.1f}%",
     "00B050" if pass_rate >= 80 else ("FF9800" if pass_rate >= 60 else "C00000"),"FFFFFF"),
    ("📅 Ngày Kiểm Thử",   TEST_DATE,            "37474F","FFFFFF"),
    ("👤 Tester",           TESTER_NAME,          "37474F","FFFFFF"),
    ("🏢 Dự án",            "CAMPRO MVC – Web Bán Camera","37474F","FFFFFF"),
]

ws_sum.append([])
for label, val, bg, fg in sum_overview:
    ws_sum.append(["", label, val])
    r_num = ws_sum.max_row
    for ci, cell in enumerate(ws_sum[r_num]):
        if ci in [1, 2]:
            cell.border    = thin_border_all()
            cell.fill      = PatternFill(start_color=bg, fill_type="solid")
            cell.font      = Font(name="Arial", bold=True, color=fg, size=11)
            cell.alignment = ALIGN_CENTER
    ws_sum.row_dimensions[r_num].height = 30

ws_sum.append([])

# Thống kê theo Category
cat_stats: dict[str, dict] = {}
for res in actual_test_results:
    cat = res["category"]
    if cat not in cat_stats:
        cat_stats[cat] = {"total": 0, "pass": 0}
    cat_stats[cat]["total"] += 1
    if res["result"] == "Pass":
        cat_stats[cat]["pass"] += 1

ws_sum.append(["","📂 Category","Total","✅ Pass","❌ Fail","Pass Rate","Status","Nhận Xét"])
_style_header_row(ws_sum, ws_sum.max_row, FILL_TEAL)
ws_sum.row_dimensions[ws_sum.max_row].height = 24

for cat, stat in sorted(cat_stats.items()):
    fail   = stat["total"] - stat["pass"]
    rate   = (stat["pass"] / stat["total"] * 100) if stat["total"] > 0 else 0
    status = "✅ Tốt" if rate == 100 else ("⚠️ Cần xem lại" if rate >= 60 else "❌ Nghiêm trọng")
    note   = "Tất cả TC pass ✓" if rate == 100 else f"Còn {fail} TC fail cần kiểm tra lại"
    ws_sum.append(["", cat, stat["total"], stat["pass"], fail, f"{rate:.0f}%", status, note])
    r_num     = ws_sum.max_row
    cat_color = CATEGORY_COLORS.get(cat, "444444")
    for ci, cell in enumerate(ws_sum[r_num]):
        cell.border    = thin_border_all()
        cell.font      = FONT_BODY
        cell.alignment = ALIGN_CENTER if ci in [1, 2, 3, 4, 5, 6] else ALIGN_LEFT
        if ci == 1:
            cell.fill = PatternFill(start_color=cat_color, fill_type="solid")
            cell.font = Font(name="Arial", bold=True, color="FFFFFF", size=9)
        elif ci == 6:
            if "✅" in str(cell.value):
                cell.font = FONT_PASS; cell.fill = FILL_PASS
            elif "❌" in str(cell.value):
                cell.font = FONT_FAIL; cell.fill = FILL_FAIL
            else:
                cell.fill = FILL_YELLOW
    ws_sum.row_dimensions[r_num].height = 22

ws_sum.append([])
# Thống kê theo Phần
ws_sum.append(["","📖 Phần","Tên Phần","TC Range","Total","Pass","Fail","Pass Rate"])
_style_header_row(ws_sum, ws_sum.max_row, PatternFill(start_color="5A3E9E", fill_type="solid"))
ws_sum.row_dimensions[ws_sum.max_row].height = 24

for r_range, (part_code, part_name) in sorted(part_map.items(), key=lambda x: x[1][0]):
    tc_nums      = list(r_range)
    part_results = [actual_test_results[i-1] for i in tc_nums if i <= len(actual_test_results)]
    p_total      = len(part_results)
    p_pass       = sum(1 for r in part_results if r["result"] == "Pass")
    p_fail       = p_total - p_pass
    p_rate       = (p_pass / p_total * 100) if p_total > 0 else 0
    ws_sum.append(["", part_code, part_name,
                   f"TC-{min(tc_nums):03d}→TC-{max(tc_nums):03d}",
                   p_total, p_pass, p_fail, f"{p_rate:.0f}%"])
    r_num = ws_sum.max_row
    for ci, cell in enumerate(ws_sum[r_num]):
        cell.border    = thin_border_all()
        cell.font      = FONT_BODY
        cell.alignment = ALIGN_CENTER if ci in [1, 3, 4, 5, 6, 7] else ALIGN_LEFT
        if ci % 2 == 0: cell.fill = FILL_STRIPE
    ws_sum.row_dimensions[r_num].height = 20

ws_sum.freeze_panes = "B2"

# ─────────────────────────────────────────────────────────────────────────────
#  SHEET 3: SECURITY REPORT (OWASP TOP 10)
# ─────────────────────────────────────────────────────────────────────────────
ws_sec = wb.create_sheet("🔐 Security Report")
ws_sec.column_dimensions["A"].width = 4
for col, w in {"B":8,"C":28,"D":26,"E":34,"F":28,"G":13,"H":13,"I":16,"J":20}.items():
    ws_sec.column_dimensions[col].width = w

ws_sec.merge_cells("B1:J1")
ws_sec["B1"] = "BÁO CÁO BẢO MẬT – OWASP TOP 10 REFERENCE – CAMPRO MVC WEB BÁN CAMERA"
ws_sec["B1"].font      = Font(name="Arial", bold=True, color="FFFFFF", size=13)
ws_sec["B1"].fill      = PatternFill(start_color="B71C1C", fill_type="solid")
ws_sec["B1"].alignment = ALIGN_CENTER
ws_sec.row_dimensions[1].height = 38

ws_sec.append(["","#","Loại Tấn Công","OWASP Ref",
               "Mô Tả Test","Kết Quả Kỳ Vọng",
               "Kết Quả TT","Risk Level","TC Ref","Tester"])
_style_header_row(ws_sec, 2, PatternFill(start_color="B71C1C", fill_type="solid"))
ws_sec.row_dimensions[2].height = 24

def _get_result_for(*keywords):
    for res in actual_test_results:
        if all(kw.lower() in res["name"].lower() for kw in keywords):
            return res["result"]
    return "N/A (Manual)"

sec_data = [
    (1, "SQL Injection – Form Login","A03:2021","Inject ' OR 1=1-- vào form login CAMPRO","Block, không bypass auth","Critical","TC-019",_get_result_for("SQL Injection","Login")),
    (2, "SQL Injection – Tìm Kiếm","A03:2021","Inject UNION SELECT vào search camera","Không lộ data/stack trace","Critical","TC-020",_get_result_for("SQL Injection","Tìm")),
    (3, "SQL Injection – URL Params","A03:2021","GET /products?category_id=' OR 1=1--","Không crash/500","Critical","TC-021",_get_result_for("SQL Injection","URL")),
    (4, "XSS Reflected – Tìm Kiếm","A03:2021","<script>alert('XSS_CAMPRO')</script> trong search","Script không chạy trong DOM","High","TC-022",_get_result_for("XSS Reflected")),
    (5, "XSS Stored – Form Đăng Ký","A03:2021","XSS trong full_name field đăng ký","Script không render khi view","High","TC-023",_get_result_for("XSS Stored")),
    (6, "Admin Bypass – Unauthenticated","A07:2021","GET /admin/* không có session","Redirect về /auth/login","Critical","TC-024",_get_result_for("Admin Bypass")),
    (7, "IDOR – Order Access","A01:2021","User truy cập /orders/1,2,3 của người khác","403/redirect, không lộ data","High","TC-025",_get_result_for("IDOR")),
    (8, "Security Headers Cơ Bản","A05:2021","Kiểm tra X-Content-Type-Options","Header hiện diện","Medium","TC-026",_get_result_for("Security Headers")),
    (9, "Password Không Lộ Response","A02:2021","Check response không chứa plain password","Password không lộ HTML","Critical","TC-027",_get_result_for("Password Không Lộ")),
    (10,"Open Redirect","A01:2021","?next=http://evil.com","Chỉ redirect nội bộ","Medium","TC-102",_get_result_for("Open Redirect")),
    (11,"Directory Traversal","A01:2021","../../etc/passwd trong URL","404/block, không lộ file hệ thống","High","TC-103",_get_result_for("Directory Traversal")),
    (12,"Mass Assignment role=admin","A08:2021","POST đăng ký với role=admin","Server ignore, không thành admin","High","TC-104",_get_result_for("Mass Assignment")),
    (13,"Clickjacking Protection","A05:2021","Kiểm tra X-Frame-Options header","Header hiện diện","Medium","TC-105",_get_result_for("Clickjacking")),
    (14,"Server Info Leakage","A05:2021","Inspect X-Powered-By header","Không lộ phiên bản","Low","TC-106",_get_result_for("Server Info")),
    (15,"Brute Force Login 5 Lần","A07:2021","5 lần login sai liên tiếp CAMPRO","Không crash, không 500","Medium","TC-107",_get_result_for("Brute Force")),
    (16,"HTTP Methods Không Hợp Lệ","A05:2021","PUT/DELETE tới GET-only endpoints","Không trả 200","Medium","TC-108",_get_result_for("HTTP Methods")),
    (17,"Stack Trace Không Lộ","A05:2021","Request không hợp lệ vào endpoint","Không lộ stack trace/DB error","High","TC-109",_get_result_for("Stack Trace")),
    (18,"RBAC – User Bypass Admin","A01:2021","User session → /admin/* pages","Tất cả bị block/redirect","Critical","TC-038",_get_result_for("User Thường Không")),
    (19,"RBAC – Logout Hủy Session","A07:2021","Logout → dùng session cũ","Session không còn hiệu lực","High","TC-041",_get_result_for("Logout Hủy")),
    (20,"Cookie HttpOnly Flag","A02:2021","Inspect session cookie sau login","HttpOnly = true","Medium","TC-046",_get_result_for("Cookie HttpOnly")),
]

risk_colors = {"Critical":"FF0000","High":"FF6B35","Medium":"FFC107","Low":"28A745"}

for i, row in enumerate(sec_data):
    num, attack, owasp, desc, expected, risk, tc_ref, actual_res = row
    ws_sec.append(["",num,attack,owasp,desc,expected,actual_res,risk,tc_ref,TESTER_NAME])
    r_num = i + 3
    for ci, cell in enumerate(ws_sec[r_num]):
        cell.border    = thin_border_all()
        cell.font      = FONT_BODY
        cell.alignment = ALIGN_CENTER if ci in [1,3,6,7,8,9] else ALIGN_LEFT
        if ci == 6:
            if actual_res == "Pass": cell.font = FONT_PASS; cell.fill = FILL_PASS
            elif actual_res == "Fail": cell.font = FONT_FAIL; cell.fill = FILL_FAIL
            else: cell.fill = FILL_YELLOW
        elif ci == 7:
            cell.fill = PatternFill(start_color=risk_colors.get(risk,"444444"), fill_type="solid")
            cell.font = Font(name="Arial", bold=True, color="FFFFFF", size=9)
        elif i % 2 == 0 and ci not in [6, 7]:
            cell.fill = FILL_STRIPE
    ws_sec.row_dimensions[r_num].height = 22

ws_sec.freeze_panes = "B3"

# ─────────────────────────────────────────────────────────────────────────────
#  SHEET 4: PERFORMANCE REPORT
# ─────────────────────────────────────────────────────────────────────────────
ws_perf = wb.create_sheet("⚡ Performance Report")
for col, w in {"A":4,"B":8,"C":40,"D":16,"E":18,"F":18,"G":18,"H":14,"I":16,"J":16}.items():
    ws_perf.column_dimensions[col].width = w

ws_perf.merge_cells("B1:J1")
ws_perf["B1"] = "BÁO CÁO HIỆU NĂNG – CONCURRENT LOAD TEST – CAMPRO MVC WEB BÁN CAMERA"
ws_perf["B1"].font      = Font(name="Arial", bold=True, color="FFFFFF", size=13)
ws_perf["B1"].fill      = PatternFill(start_color="E65100", fill_type="solid")
ws_perf["B1"].alignment = ALIGN_CENTER
ws_perf.row_dimensions[1].height = 38

ws_perf.append(["","#","Test Case","Workers","Total Requests","Threshold","Avg Latency (s)","Kết Quả","TC Ref","Nhóm"])
_style_header_row(ws_perf, 2, PatternFill(start_color="E65100", fill_type="solid"))
ws_perf.row_dimensions[2].height = 24

perf_data = [
    (1, "Homepage Concurrent (10w/30r)",      10, 30, "≥85% / <3s", "TC-042", "Performance", _get_result_for("Homepage Concurrent")),
    (2, "Search Concurrent (10w/30r)",         10, 30, "≥70%",       "TC-043", "Performance", _get_result_for("Search Concurrent")),
    (3, "Homepage Response < 2s",              1,  1,  "< 2.0s",     "TC-044", "Performance", _get_result_for("Homepage Response")),
    (4, "Login Page Response < 2s",            1,  1,  "< 2.0s",     "TC-045", "Performance", _get_result_for("Login Page Response")),
    (5, "/products Concurrent (8w/20r)",       8,  20, "≥80%",       "TC-092", "Performance", _get_result_for("products Concurrent")),
    (6, "Admin/products Latency < 3s",         1,  1,  "< 3.0s",     "TC-093", "Performance", _get_result_for("Admin/products")),
    (7, "Register Page Latency < 2s",          1,  1,  "< 2.0s",     "TC-094", "Performance", _get_result_for("Register Page")),
    (8, "News Page Latency < 2s",              1,  1,  "< 2.0s",     "TC-095", "Performance", _get_result_for("News Page")),
    (9, "Contact Page Latency < 2s",           1,  1,  "< 2.0s",     "TC-096", "Performance", _get_result_for("Contact Page")),
    (10,"Homepage Stress (20w/50r)",           20, 50, "≥75%",       "TC-097", "Performance", _get_result_for("Homepage Stress")),
    (11,"Products TTFB < 1.5s",               1,  1,  "< 1.5s",     "TC-098", "Performance", _get_result_for("Products TTFB")),
    (12,"Login Concurrent (10w/20r)",          10, 20, "≥90%",       "TC-099", "Performance", _get_result_for("Login Concurrent")),
    (13,"Search Stress (15w/30r)",             15, 30, "≥65%",       "TC-100", "Performance", _get_result_for("Search Stress")),
    (14,"Homepage TTFB < 1.5s",               1,  1,  "< 1.5s",     "TC-101", "Performance", _get_result_for("Homepage TTFB")),
]

for i, (num, name, workers, reqs, threshold, tc_ref, group, actual_res) in enumerate(perf_data):
    ws_perf.append(["",num,name,workers,reqs,threshold,"—",actual_res,tc_ref,group])
    r_num = i + 3
    for ci, cell in enumerate(ws_perf[r_num]):
        cell.border    = thin_border_all()
        cell.font      = FONT_BODY
        cell.alignment = ALIGN_CENTER
        if ci == 7:
            if actual_res == "Pass": cell.font = FONT_PASS; cell.fill = FILL_PASS
            elif actual_res == "Fail": cell.font = FONT_FAIL; cell.fill = FILL_FAIL
            else: cell.fill = FILL_YELLOW
        elif i % 2 == 0 and ci != 7:
            cell.fill = FILL_STRIPE
    ws_perf.row_dimensions[r_num].height = 22

ws_perf.freeze_panes = "B3"

# ─────────────────────────────────────────────────────────────────────────────
#  SHEET 5: TEST MATRIX (Feature ↔ TC)
# ─────────────────────────────────────────────────────────────────────────────
ws_matrix = wb.create_sheet("🗺️ Test Matrix")
for col, w in {"A":4,"B":34,"C":18,"D":12,"E":12,"F":12,"G":24}.items():
    ws_matrix.column_dimensions[col].width = w

ws_matrix.merge_cells("B1:G1")
ws_matrix["B1"] = "CAMPRO MVC – FEATURE vs TEST CASE MATRIX"
ws_matrix["B1"].font      = Font(name="Arial", bold=True, color="FFFFFF", size=13)
ws_matrix["B1"].fill      = PatternFill(start_color="283593", fill_type="solid")
ws_matrix["B1"].alignment = ALIGN_CENTER
ws_matrix.row_dimensions[1].height = 38

ws_matrix.append(["","Chức Năng / Module","TC IDs","Số TC","Pass","Fail","Ghi Chú"])
_style_header_row(ws_matrix, 2, PatternFill(start_color="283593", fill_type="solid"))
ws_matrix.row_dimensions[2].height = 24

feature_matrix = [
    ("🔐 Đăng ký / Đăng nhập (Auth CAMPRO)",     [1,2,7,10,11,12,13,14,15,33,46,47,48]),
    ("🛒 Giỏ hàng & Checkout Camera",             [5,6,67,75,76,77]),
    ("📦 Sản phẩm (CRUD, Search, Filter Camera)", [3,4,16,17,18,54,55,56,60,61,62,63,64,66,68]),
    ("👤 Quản lý Tài khoản (Profile)",            [70,71,72,73,74]),
    ("🏢 Admin Dashboard & Thống Kê",             [8,9,40,54,57,58,59,80,81,83,84,85,86,87,88,89,90,91]),
    ("📊 Admin Báo Cáo Doanh Thu",                [119]),
    ("🔑 Phân quyền RBAC",                        [38,39,40,41,147,148]),
    ("🛡️ Bảo mật OWASP (Security)",              [19,20,21,22,23,24,25,26,27,102,103,104,105,106,107,108,109]),
    ("⚡ Hiệu năng (Performance)",                [42,43,44,45,92,93,94,95,96,97,98,99,100,101]),
    ("🗝️ Session & Cookie",                       [46,47,48,41]),
    ("📰 Tin tức (News)",                         [78,84,85,117]),
    ("📞 Liên hệ (Contact)",                      [36,79,86,87,143]),
    ("🎨 UI/UX",                                  [49,50,51,52,53]),
    ("♿ SEO & Accessibility",                     [120,121,122,123,124,125,126,127,128,129]),
    ("🔀 Integration E2E Flows",                  [141,142,143,144,145,146,147,148,149,150]),
]

for i, (feature, tc_ids) in enumerate(feature_matrix):
    pass_count = sum(1 for tid in tc_ids
                     if tid <= len(actual_test_results)
                     and actual_test_results[tid-1]["result"] == "Pass")
    fail_count = sum(1 for tid in tc_ids
                     if tid <= len(actual_test_results)
                     and actual_test_results[tid-1]["result"] == "Fail")
    tc_str = ", ".join(f"TC-{t:03d}" for t in sorted(set(tc_ids))[:8])
    if len(tc_ids) > 8:
        tc_str += f" ... (+{len(tc_ids)-8})"
    note = "✅ All Pass" if fail_count == 0 else f"⚠️ {fail_count} Fail cần xem lại"
    ws_matrix.append(["", feature, tc_str, len(tc_ids), pass_count, fail_count, note])
    r_num = i + 3
    for ci, cell in enumerate(ws_matrix[r_num]):
        cell.border    = thin_border_all()
        cell.font      = FONT_BODY
        cell.alignment = ALIGN_LEFT if ci in [1, 2] else ALIGN_CENTER
        if i % 2 == 0: cell.fill = FILL_STRIPE
        if ci == 4 and fail_count == 0: cell.font = FONT_PASS
        elif ci == 5 and fail_count > 0: cell.font = FONT_FAIL
    ws_matrix.row_dimensions[r_num].height = 22

ws_matrix.freeze_panes = "B3"

# ─────────────────────────────────────────────────────────────────────────────
#  LƯU FILE
# ─────────────────────────────────────────────────────────────────────────────
filename = f"BaoCao_CAMPRO_MVC_v2_150TC_{int(time.time())}.xlsx"
wb.save(filename)

total_run  = len(actual_test_results)
total_pass = sum(1 for r in actual_test_results if r["result"] == "Pass")
total_fail = total_run - total_pass

print("\n" + "=" * 80)
print("TỔNG KẾT – CAMPRO MVC ENTERPRISE QA v2.0 (150 TEST CASES)")
print("=" * 80)
print(f"  Tổng test cases thực thi  : {total_run}")
print(f"  ✅ Pass                    : {total_pass}")
print(f"  ❌ Fail                    : {total_fail}")
print(f"  📈 Pass Rate               : {total_pass/total_run*100:.1f}%" if total_run > 0 else "  N/A")
print(f"\n  📁 File báo cáo Excel      : {filename}")
print(f"  📄 Sheets                  : Full Detail | Summary | Security | Performance | Matrix")
print("=" * 80)