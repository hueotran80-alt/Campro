-- =====================================================
-- CAMPRO - Website Bán Camera
-- Database: MySQL
-- =====================================================

CREATE DATABASE IF NOT EXISTS campro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campro;

-- =====================================================
-- BẢNG USERS (Khách hàng + Admin)
-- =====================================================
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(100) NOT NULL,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(100) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  phone VARCHAR(15),
  address TEXT,
  role ENUM('admin', 'customer') DEFAULT 'customer',
  is_active TINYINT(1) DEFAULT 1,
  avatar VARCHAR(255) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =====================================================
-- BẢNG CATEGORIES (Loại sản phẩm)
-- =====================================================
CREATE TABLE categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  slug VARCHAR(100) NOT NULL UNIQUE,
  description TEXT,
  image VARCHAR(255),
  is_active TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =====================================================
-- BẢNG SUPPLIERS (Nhà cung cấp)
-- =====================================================
CREATE TABLE suppliers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100),
  phone VARCHAR(15),
  address TEXT,
  website VARCHAR(255),
  is_active TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =====================================================
-- BẢNG PRODUCTS (Sản phẩm Camera)
-- =====================================================
CREATE TABLE products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  category_id INT,
  supplier_id INT,
  description TEXT,
  specifications TEXT,
  price DECIMAL(15,0) NOT NULL,
  sale_price DECIMAL(15,0) DEFAULT NULL,
  stock INT DEFAULT 0,
  image VARCHAR(255),
  images JSON,
  resolution VARCHAR(50),
  view_angle VARCHAR(50),
  is_active TINYINT(1) DEFAULT 1,
  views INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
  FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
);

-- =====================================================
-- BẢNG COUPONS (Mã giảm giá)
-- =====================================================
CREATE TABLE coupons (
  id INT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(50) NOT NULL UNIQUE,
  discount_type ENUM('percent', 'fixed') DEFAULT 'percent',
  discount_value DECIMAL(10,2) NOT NULL,
  min_order_amount DECIMAL(15,0) DEFAULT 0,
  max_discount DECIMAL(15,0) DEFAULT NULL,
  usage_limit INT DEFAULT NULL,
  used_count INT DEFAULT 0,
  start_date DATE,
  end_date DATE,
  is_active TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =====================================================
-- BẢNG ORDERS (Đơn hàng)
-- =====================================================
CREATE TABLE orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  order_code VARCHAR(20) NOT NULL UNIQUE,
  full_name VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  phone VARCHAR(15) NOT NULL,
  address TEXT NOT NULL,
  note TEXT,
  payment_method ENUM('cod', 'bank_transfer', 'e_wallet') DEFAULT 'cod',
  payment_status ENUM('pending', 'paid', 'failed') DEFAULT 'pending',
  order_status ENUM('pending', 'confirmed', 'shipping', 'delivered', 'cancelled') DEFAULT 'pending',
  subtotal DECIMAL(15,0) NOT NULL,
  discount DECIMAL(15,0) DEFAULT 0,
  total DECIMAL(15,0) NOT NULL,
  coupon_id INT DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
  FOREIGN KEY (coupon_id) REFERENCES coupons(id) ON DELETE SET NULL
);

-- =====================================================
-- BẢNG ORDER_ITEMS (Chi tiết đơn hàng)
-- =====================================================
CREATE TABLE order_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  product_id INT,
  product_name VARCHAR(255) NOT NULL,
  product_image VARCHAR(255),
  quantity INT NOT NULL,
  price DECIMAL(15,0) NOT NULL,
  total DECIMAL(15,0) NOT NULL,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);

-- =====================================================
-- BẢNG CART (Giỏ hàng - lưu tạm)
-- =====================================================
CREATE TABLE cart_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY unique_cart (user_id, product_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- =====================================================
-- BẢNG NEWS (Tin tức)
-- =====================================================
CREATE TABLE news (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  content LONGTEXT,
  excerpt TEXT,
  thumbnail VARCHAR(255),
  author_id INT,
  is_published TINYINT(1) DEFAULT 0,
  views INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
);

-- =====================================================
-- BẢNG CONTACTS (Liên hệ)
-- =====================================================
CREATE TABLE contacts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  phone VARCHAR(15),
  subject VARCHAR(255),
  message TEXT NOT NULL,
  status ENUM('unread', 'read', 'replied') DEFAULT 'unread',
  admin_reply TEXT DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =====================================================
-- DỮ LIỆU MẪU
-- =====================================================

-- Tài khoản Admin mặc định (password: Admin@123)
INSERT INTO users (full_name, username, email, password, role, is_active) VALUES
('Administrator', 'admin', 'admin@campro.vn', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'admin', 1),
('Nguyễn Văn A', 'nguyenvana', 'customer@campro.vn', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'customer', 1);

-- Danh mục sản phẩm
INSERT INTO categories (name, slug, description, is_active) VALUES
('Camera IP', 'camera-ip', 'Camera giám sát kết nối mạng IP', 1),
('Camera Analog', 'camera-analog', 'Camera giám sát analog truyền thống', 1),
('Camera WiFi', 'camera-wifi', 'Camera giám sát kết nối WiFi không dây', 1),
('Camera PTZ', 'camera-ptz', 'Camera quay quét 360 độ', 1),
('Camera ngoài trời', 'camera-ngoai-troi', 'Camera chống nước chuyên dụng ngoài trời', 1);

-- Nhà cung cấp
INSERT INTO suppliers (name, email, phone, address, is_active) VALUES
('Hikvision Vietnam', 'info@hikvision.vn', '024 3825 3388', 'Tầng 3, 14 Trần Hưng Đạo, Hà Nội', 1),
('Dahua Technology', 'sale@dahua.vn', '028 3636 9999', '123 Nguyễn Huệ, TP.HCM', 1),
('Axis Communications', 'contact@axis.vn', '024 6656 7777', '45 Bà Triệu, Hà Nội', 1),
('Hanwha Vision', 'info@hanwha.vn', '028 3822 1111', '88 Lê Lợi, TP.HCM', 1);

-- Sản phẩm
INSERT INTO products (name, slug, category_id, supplier_id, description, price, sale_price, stock, resolution, view_angle, is_active) VALUES
('Camera IP Hikvision DS-2CD2143G2-I 4MP', 'camera-ip-hikvision-ds-2cd2143g2-i', 1, 1, 'Camera IP ngoài trời 4MP, hồng ngoại 40m, chống nước IP67, phát hiện chuyển động thông minh', 1850000, 1650000, 50, '4MP (2688×1520)', '103°', 1),
('Camera WiFi Hikvision DS-2CD2121G1-IDW1 2MP', 'camera-wifi-hikvision-ds-2cd2121g1', 2, 1, 'Camera WiFi trong nhà 2MP, tích hợp micro, đàm thoại 2 chiều', 1200000, 990000, 30, '2MP (1920×1080)', '107°', 1),
('Camera Dahua IPC-HDW2831T-AS 8MP 4K', 'camera-dahua-ipc-hdw2831t-as-4k', 1, 2, 'Camera dome 4K 8MP, AI phát hiện người, hồng ngoại 30m, chống nước IP67', 3200000, 2800000, 25, '8MP (3840×2160)', '102°', 1),
('Camera PTZ Hikvision DS-2DE4A425IWG-E 4MP', 'camera-ptz-hikvision-ds-2de4a425', 4, 1, 'Camera PTZ 4MP, zoom quang học 25x, hồng ngoại 100m, theo dõi tự động', 8500000, 7900000, 10, '4MP (2560×1440)', '60°', 1),
('Camera Analog Dahua HAC-HDW1500TL-A 5MP', 'camera-analog-dahua-hac-hdw1500tl', 2, 2, 'Camera HDCVI 5MP tích hợp micro, hồng ngoại 20m, chống nước IP67', 750000, 650000, 80, '5MP (2880×1620)', '98°', 1),
('Camera Ngoài Trời Hikvision DS-2CD2T47G2-L 4MP', 'camera-ngoai-troi-hikvision-ds-2cd2t47g2', 5, 1, 'Camera ColorVu 4MP, đèn bổ sung ánh sáng, màu sắc ban đêm, hồng ngoại 60m', 2100000, 1890000, 40, '4MP (2688×1520)', '98°', 1),
('Camera Axis P3245-V 2MP', 'camera-axis-p3245-v', 1, 3, 'Camera dome cố định 2MP, chống va đập IK10, chống bụi IP52, HDTV 1080p', 4500000, NULL, 15, '2MP (1920×1080)', '104°', 1),
('Camera WiFi Dahua IPC-F42FEP-D 4MP', 'camera-wifi-dahua-ipc-f42fep', 3, 2, 'Camera WiFi full-color 4MP, đèn báo động, phát hiện người thông minh', 1800000, 1600000, 35, '4MP (2560×1440)', '167°', 1);

-- Mã giảm giá
INSERT INTO coupons (code, discount_type, discount_value, min_order_amount, max_discount, usage_limit, start_date, end_date, is_active) VALUES
('CAMPRO10', 'percent', 10, 1000000, 200000, 100, '2025-01-01', '2025-12-31', 1),
('SUMMER50', 'fixed', 50000, 500000, NULL, 50, '2025-06-01', '2025-08-31', 1),
('NEWUSER', 'percent', 15, 0, 300000, 200, '2025-01-01', '2025-12-31', 1),
('FLASH20', 'percent', 20, 2000000, 500000, 30, '2025-07-01', '2025-07-31', 1);

-- Tin tức mẫu
INSERT INTO news (title, slug, content, excerpt, is_published, author_id) VALUES
('Top 5 Camera Giám Sát Tốt Nhất 2025', 'top-5-camera-giam-sat-2025', '<p>Bài viết tổng hợp các camera tốt nhất năm 2025...</p>', 'Tổng hợp top 5 camera giám sát được đánh giá cao nhất năm 2025 về chất lượng, tính năng và giá cả.', 1, 1),
('Hướng Dẫn Lắp Đặt Camera IP Tại Nhà', 'huong-dan-lap-dat-camera-ip', '<p>Hướng dẫn chi tiết từng bước lắp đặt camera IP...</p>', 'Hướng dẫn lắp đặt camera IP tại nhà đơn giản, tiết kiệm chi phí kỹ thuật.', 1, 1),
('So Sánh Camera WiFi và Camera IP: Nên Chọn Loại Nào?', 'so-sanh-camera-wifi-va-ip', '<p>Phân tích ưu nhược điểm của từng loại...</p>', 'Phân tích chi tiết sự khác biệt giữa camera WiFi và camera IP để giúp bạn chọn đúng sản phẩm.', 1, 1);
