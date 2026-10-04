CREATE TABLE IF NOT EXISTS users (
  id BIGINT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  password_hash VARCHAR(500) NOT NULL,
  phone VARCHAR(30) NOT NULL DEFAULT '',
  address VARCHAR(500) NOT NULL DEFAULT '',
  role ENUM('admin','customer') NOT NULL DEFAULT 'customer',
  active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS categories (
  id BIGINT PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  description VARCHAR(500) NOT NULL DEFAULT '',
  active TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS suppliers (
  id BIGINT PRIMARY KEY,
  name VARCHAR(160) NOT NULL UNIQUE,
  description VARCHAR(500) NOT NULL DEFAULT '',
  email VARCHAR(160) NOT NULL DEFAULT '',
  phone VARCHAR(30) NOT NULL DEFAULT '',
  active TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS products (
  id BIGINT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  subtitle VARCHAR(255) NOT NULL DEFAULT '',
  brand VARCHAR(120) NOT NULL DEFAULT '',
  category VARCHAR(120) NOT NULL DEFAULT '',
  resolution VARCHAR(80) NOT NULL DEFAULT '',
  connection_type VARCHAR(80) NOT NULL DEFAULT '',
  price DECIMAL(15,0) NOT NULL,
  old_price DECIMAL(15,0) NOT NULL DEFAULT 0,
  stock INT NOT NULL DEFAULT 0,
  image VARCHAR(255) NOT NULL DEFAULT '',
  tag VARCHAR(100) NOT NULL DEFAULT '',
  angle VARCHAR(80) NOT NULL DEFAULT '',
  night_mode VARCHAR(80) NOT NULL DEFAULT '',
  active TINYINT(1) NOT NULL DEFAULT 1,
  description TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS coupons (
  id BIGINT PRIMARY KEY,
  code VARCHAR(50) NOT NULL UNIQUE,
  discount_type ENUM('percent','fixed') NOT NULL DEFAULT 'percent',
  discount_value DECIMAL(15,2) NOT NULL,
  min_amount DECIMAL(15,0) NOT NULL DEFAULT 0,
  max_amount DECIMAL(15,0) NOT NULL DEFAULT 0,
  active TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS articles (
  id BIGINT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  category VARCHAR(120) NOT NULL DEFAULT '',
  image VARCHAR(255) NOT NULL DEFAULT '',
  published TINYINT(1) NOT NULL DEFAULT 1,
  body LONGTEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS contacts (
  id BIGINT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL,
  phone VARCHAR(30) NOT NULL DEFAULT '',
  subject VARCHAR(255) NOT NULL DEFAULT '',
  message TEXT NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'Chưa xử lý',
  reply TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS orders (
  id VARCHAR(30) PRIMARY KEY,
  customer VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL,
  shipping_email VARCHAR(160) NOT NULL DEFAULT '',
  phone VARCHAR(30) NOT NULL,
  address VARCHAR(500) NOT NULL,
  note VARCHAR(1000) NOT NULL DEFAULT '',
  order_date DATE NOT NULL,
  total DECIMAL(15,0) NOT NULL,
  discount DECIMAL(15,0) NOT NULL DEFAULT 0,
  status VARCHAR(50) NOT NULL,
  payment VARCHAR(50) NOT NULL,
  paid TINYINT(1) NOT NULL DEFAULT 0,
  demo TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_orders_email (email),
  INDEX ix_orders_date (order_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS order_items (
  order_id VARCHAR(30) NOT NULL,
  product_id BIGINT NOT NULL,
  product_name VARCHAR(255) NOT NULL,
  quantity INT NOT NULL,
  price DECIMAL(15,0) NOT NULL,
  image VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY(order_id, product_id),
  CONSTRAINT fk_order_items_order FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS carts (
  user_id BIGINT NOT NULL,
  product_id BIGINT NOT NULL,
  quantity INT NOT NULL,
  PRIMARY KEY(user_id, product_id),
  CONSTRAINT fk_cart_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO categories(id,name,description,active) VALUES
(1,'Trong nhà','Camera cho phòng khách, phòng ngủ và cửa hàng nhỏ',1),
(2,'Ngoài trời','Camera chống chịu thời tiết cho sân, cổng và mặt tiền',1),
(3,'Dùng pin','Camera lắp đặt linh hoạt, không cần đi dây nguồn',1);

INSERT IGNORE INTO suppliers(id,name,description,email,phone,active) VALUES
(1,'TP-Link Tapo','Thiết bị camera thông minh cho gia đình','support.vn@tp-link.com','028 7300 0628',1),
(2,'Hikvision','Giải pháp camera IP và hệ thống giám sát','info@hikvision.vn','024 3825 3388',1),
(3,'Dahua','Camera và thiết bị an ninh','sale@dahua.vn','028 3636 9999',1);

INSERT IGNORE INTO products(id,name,subtitle,brand,category,resolution,connection_type,price,old_price,stock,image,tag,angle,night_mode,active,description) VALUES
(1,'Tapo C225','Camera Wi-Fi quay quét trong nhà','TP-Link Tapo','Trong nhà','2K QHD','Wi-Fi',990000,1290000,28,'c225.jpg','ĐƯỢC QUAN TÂM','360°','Hồng ngoại',1,'Quan sát không gian sống, trò chuyện với người thân và chủ động bảo vệ sự riêng tư. Thiết kế nhỏ gọn phù hợp đặt trên kệ hoặc gắn trần.'),
(2,'Tapo C520WS','Camera Wi-Fi quay quét ngoài trời','TP-Link Tapo','Ngoài trời','2K QHD','Wi-Fi',1390000,1690000,16,'c520ws.jpg','NGOÀI TRỜI','360°','Có màu',1,'Quan sát sân nhà và lối vào với góc quay rộng. Tầm nhìn ban đêm có màu giúp nhận biết chi tiết ngay cả khi trời tối.'),
(3,'Tapo C320WS','Camera Wi-Fi ngoài trời 4MP','TP-Link Tapo','Ngoài trời','2K QHD','Wi-Fi / LAN',1090000,1390000,32,'c320ws.png','GIÁ TỐT','Góc cố định','Có màu',1,'Giải pháp giám sát cố định cho cổng, sân và cửa hàng. Kết nối Wi-Fi hoặc dây mạng.'),
(4,'Tapo C200','Camera Wi-Fi quay quét Full HD','TP-Link Tapo','Trong nhà','Full HD','Wi-Fi',449000,590000,45,'c200.jpg','DỄ SỬ DỤNG','360°','Hồng ngoại',1,'Camera Full HD dễ cài đặt, theo dõi từ điện thoại và đàm thoại hai chiều.'),
(5,'Tapo C425','Camera dùng pin, lắp đặt linh hoạt','TP-Link Tapo','Dùng pin','2K QHD','Wi-Fi',2290000,2690000,8,'c425.jpg','KHÔNG DÂY','Góc rộng','Có màu',1,'Linh hoạt lựa chọn vị trí nhờ nguồn pin, phù hợp nơi khó đi dây điện.'),
(6,'Tapo C120','Camera nhỏ gọn trong và ngoài trời','TP-Link Tapo','Ngoài trời','2K QHD','Wi-Fi',790000,990000,0,'c120.png','NHỎ GỌN','Góc cố định','Có màu',1,'Thiết kế nhỏ gọn cho nhiều vị trí lắp đặt, hình ảnh sắc nét.'),
(7,'Hikvision ColorVu 4MP','Camera IP thân trụ cho cửa hàng','Hikvision','Ngoài trời','2K QHD','PoE',1890000,2190000,12,'hikvision.png','CAMERA IP','Góc cố định','Có màu',1,'Camera thân trụ dùng trong hệ thống giám sát có dây, phù hợp cổng và khu vực kinh doanh.'),
(8,'Dahua IPC-HDW2831T','Camera IP dome 8MP','Dahua','Ngoài trời','4K','PoE',2590000,2890000,6,'dahua.jpg','ĐỘ PHÂN GIẢI 4K','Góc cố định','Hồng ngoại',1,'Camera dome 8MP cho hệ thống giám sát cố định, hỗ trợ hình ảnh 4K sắc nét.');

INSERT IGNORE INTO coupons(id,code,discount_type,discount_value,min_amount,max_amount,active) VALUES
(1,'CAMPRO10','percent',10,500000,200000,1),
(2,'CHAOBAN','fixed',50000,1000000,50000,1);

INSERT IGNORE INTO articles(id,title,category,image,published,body) VALUES
(1,'Chọn camera trong nhà: bắt đầu từ đâu?','HƯỚNG DẪN MUA HÀNG','c225.jpg',1,'Trước khi chọn camera, hãy xác định khu vực cần quan sát và vị trí cấp nguồn. Với phòng khách hoặc cửa hàng nhỏ, camera Wi-Fi quay quét giúp quan sát linh hoạt.\n\nNên đặt mật khẩu mạnh, cập nhật phần mềm và chỉ chia sẻ quyền truy cập với người tin cậy.'),
(2,'Camera Wi-Fi hay có dây: chọn theo vị trí lắp','KIẾN THỨC CAMERA','c320ws.png',1,'Camera Wi-Fi thuận tiện khi vị trí lắp có tín hiệu mạng ổn định. Kết nối có dây phù hợp khu vực xa bộ phát hoặc cần duy trì kết nối ổn định.'),
(3,'Bốn điều cần kiểm tra trước khi lắp ngoài trời','KINH NGHIỆM LẮP ĐẶT','c520ws.jpg',1,'Xác định vùng quan sát, kiểm tra khả năng chống thời tiết, chuẩn bị nguồn điện và kiểm tra kết nối mạng.');

INSERT IGNORE INTO contacts(id,name,email,phone,subject,message,status,reply) VALUES
(1,'Nguyễn Khánh Linh','khanhlinh@example.com','0900000005','Tư vấn camera cho cửa hàng','Mình cần lắp 3 camera cho cửa hàng khoảng 60m², nhờ cửa hàng tư vấn vị trí và thiết bị phù hợp.','Chưa xử lý','');

INSERT IGNORE INTO orders(id,customer,email,shipping_email,phone,address,note,order_date,total,discount,status,payment,paid,demo) VALUES
('CP26092101','Nguyễn Minh Anh','minhanh@example.com','minhanh@example.com','0900000001','24 Nguyễn Văn Cừ, Hà Nội','', '2026-09-21',1980000,0,'Chờ xử lý','COD',0,1),
('CP26092102','Trần Hoàng Nam','hoangnam@example.com','hoangnam@example.com','0900000002','15 Lê Lợi, Đà Nẵng','', '2026-09-21',1390000,0,'Đang giao','Chuyển khoản',1,1),
('CP26092003','Lê Thu Hà','thuha@example.com','thuha@example.com','0900000003','80 Nguyễn Trãi, TP. Hồ Chí Minh','', '2026-09-20',3270000,0,'Hoàn thành','Chuyển khoản',1,1),
('CP26091904','Phạm Đức Huy','duchuy@example.com','duchuy@example.com','0900000004','32 Trần Phú, Hải Phòng','', '2026-09-19',898000,0,'Đã xác nhận','COD',0,1),
('CP26091805','Nguyễn Minh Anh','minhanh@example.com','minhanh@example.com','0900000001','24 Nguyễn Văn Cừ, Hà Nội','', '2026-09-18',2290000,0,'Hoàn thành','COD',1,1);

INSERT IGNORE INTO order_items(order_id,product_id,product_name,quantity,price,image) VALUES
('CP26092101',1,'Tapo C225',2,990000,'c225.jpg'),
('CP26092102',2,'Tapo C520WS',1,1390000,'c520ws.jpg'),
('CP26092003',3,'Tapo C320WS',3,1090000,'c320ws.png'),
('CP26091904',4,'Tapo C200',2,449000,'c200.jpg'),
('CP26091805',5,'Tapo C425',1,2290000,'c425.jpg');
