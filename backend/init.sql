-- =====================================================
-- 鲟鱼子酱外贸CRM系统 - 完整数据库设计
-- 版本: 1.0
-- 适用数据库: MySQL 8.0+
-- =====================================================

-- 管理员账号表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(100),
    role VARCHAR(20) DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 默认管理员账号: admin / caviar2024
INSERT IGNORE INTO users (username, password_hash, nickname, role)
VALUES ('admin', '1c76c7a99730d87996959a9fa95c0d3ee0e0621eaa060951b9605ed226f30d88', 'Administrator', 'admin');

CREATE DATABASE IF NOT EXISTS caviar_crm
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE caviar_crm;

-- 国家字典表
CREATE TABLE countries (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(10) NOT NULL UNIQUE,
    name_en VARCHAR(100) NOT NULL,
    name_cn VARCHAR(100),
    official_language VARCHAR(50),
    priority TINYINT DEFAULT 0,
    trade_volume DECIMAL(12,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_priority (priority)
);

-- 客户类型字典表
CREATE TABLE customer_types (
    id INT PRIMARY KEY AUTO_INCREMENT,
    type_code VARCHAR(20) UNIQUE NOT NULL,
    type_name_en VARCHAR(100) NOT NULL,
    type_name_cn VARCHAR(100) NOT NULL,
    weight_score INT DEFAULT 0,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO customer_types (type_code, type_name_en, type_name_cn, weight_score) VALUES
('IMPORTER', 'Importer', '进口商', 100),
('WHOLESALER', 'Wholesaler', '批发商', 85),
('DISTRIBUTOR', 'Secondary Distributor', '二级批发商', 70),
('BRAND', 'Caviar Brand', '鱼子酱品牌商', 90),
('MICHELIN_RESTAURANT', 'Michelin Restaurant', '米其林餐厅', 80),
('LUXURY_HOTEL', 'Luxury Hotel', '豪华酒店', 75),
('RETAILER', 'Boutique Retailer', '精品零售商', 60);

-- 客户主表
CREATE TABLE customers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_name_en VARCHAR(255) NOT NULL,
    company_name_local VARCHAR(255),
    country_id INT NOT NULL,
    city VARCHAR(100),
    website VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    customer_type_id INT,
    is_verified BOOLEAN DEFAULT FALSE,
    background_score DECIMAL(5,2) DEFAULT 0,
    import_trade_score TINYINT DEFAULT 0,
    company_scale_score TINYINT DEFAULT 0,
    market_position_score TINYINT DEFAULT 0,
    qualification_score TINYINT DEFAULT 0,
    cooperation_potential_score TINYINT DEFAULT 0,
    social_media_score TINYINT DEFAULT 0,
    responsiveness_score TINYINT DEFAULT 0,
    country_rank INT DEFAULT 999,
    is_collected BOOLEAN DEFAULT FALSE,
    follow_up_status ENUM('NEW','CONTACTED','NEGOTIATING','WON','LOST','INACTIVE') DEFAULT 'NEW',
    priority_level ENUM('HIGH','MEDIUM','LOW') DEFAULT 'MEDIUM',
    notes TEXT,
    tags JSON,
    search_source VARCHAR(100),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_contact_date DATE,
    FOREIGN KEY (country_id) REFERENCES countries(id),
    FOREIGN KEY (customer_type_id) REFERENCES customer_types(id),
    INDEX idx_country (country_id),
    INDEX idx_score (background_score),
    INDEX idx_follow_up (follow_up_status)
);

-- 背调详细信息表
CREATE TABLE background_checks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    founded_year INT,
    employee_count INT,
    annual_revenue DECIMAL(15,2),
    has_import_history BOOLEAN DEFAULT FALSE,
    last_import_date DATE,
    import_frequency VARCHAR(20),
    typical_import_volume DECIMAL(10,2),
    current_suppliers TEXT,
    has_cites_license BOOLEAN DEFAULT FALSE,
    has_haccp_cert BOOLEAN DEFAULT FALSE,
    other_certifications JSON,
    market_segment VARCHAR(50),
    price_position VARCHAR(20),
    distribution_channels JSON,
    linkedin_followers INT,
    instagram_followers INT,
    raw_data JSON,
    scrape_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    UNIQUE KEY uk_customer (customer_id)
);

-- 邮件模板表
CREATE TABLE email_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    customer_type_id INT,
    subject VARCHAR(200) NOT NULL,
    body_content TEXT NOT NULL,
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    variables JSON,
    industry VARCHAR(50) DEFAULT 'caviar',
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_type_id) REFERENCES customer_types(id)
);

-- 邮件发送记录表
CREATE TABLE email_sent_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    template_id INT,
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(100),
    subject VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    language VARCHAR(10),
    send_status ENUM('PENDING','SENT','FAILED','BOUNCED') DEFAULT 'PENDING',
    error_message TEXT,
    opened_at TIMESTAMP NULL,
    clicked_at TIMESTAMP NULL,
    replied_at TIMESTAMP NULL,
    follow_up_sent BOOLEAN DEFAULT FALSE,
    notes TEXT,
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES email_templates(id),
    INDEX idx_customer (customer_id),
    INDEX idx_sent_at (sent_at)
);

-- 跟进任务表
CREATE TABLE follow_up_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    contact_id INT,
    task_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    due_date DATE NOT NULL,
    due_time TIME,
    priority ENUM('HIGH','MEDIUM','LOW') DEFAULT 'MEDIUM',
    status ENUM('PENDING','COMPLETED','CANCELLED','OVERDUE') DEFAULT 'PENDING',
    completed_at TIMESTAMP NULL,
    completion_notes TEXT,
    assigned_to VARCHAR(100),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- 每日统计表
CREATE TABLE statistics_daily (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stat_date DATE NOT NULL,
    total_customers INT DEFAULT 0,
    new_customers INT DEFAULT 0,
    high_score_customers INT DEFAULT 0,
    countries_covered INT DEFAULT 0,
    emails_sent INT DEFAULT 0,
    emails_opened INT DEFAULT 0,
    emails_replied INT DEFAULT 0,
    open_rate DECIMAL(5,2) DEFAULT 0,
    reply_rate DECIMAL(5,2) DEFAULT 0,
    leads_converted INT DEFAULT 0,
    total_potential_value DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_date (stat_date)
);

-- 产品字典表（鱼子酱品类）
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(100) NOT NULL,
    product_name_en VARCHAR(100),
    hs_code VARCHAR(20) NOT NULL UNIQUE,
    hs_code_description VARCHAR(255),
    grade VARCHAR(50),
    origin VARCHAR(100),
    price_range VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_hs_code (hs_code)
);

-- 客户-产品关联表
CREATE TABLE customer_products (
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    typical_volume DECIMAL(10,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customer_id, product_id),
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- 预置鱼子酱产品数据
INSERT INTO products (product_name, product_name_en, hs_code, hs_code_description, grade) VALUES
('里海野生鲟鱼子酱', 'Caspian Wild Sturgeon Caviar', '1604.31.00', 'Caviar and caviar substitutes prepared from fish eggs', 'Grade 0'),
('阿斯特拉罕鱼子酱', 'Astrakhan Caviar', '1604.31.00', 'Caviar prepared from Acipenser baerii (Siberian sturgeon)', 'Grade 1'),
('塞夫鲁加鱼子酱', 'Sevruga Caviar', '1604.31.00', 'Caviar prepared from Acipenser stellatus (Sevruga sturgeon)', 'Grade 2'),
('希特拉鱼子酱', 'Siberian Caviar', '1604.31.00', 'Caviar from Siberian sturgeon (Acipenser baerii)', 'Grade 1'),
('中国养殖鲟鱼子酱', 'Chinese Farmed Sturgeon Caviar', '1604.31.00', 'Premium caviar from Chinese aquaculture', 'Grade 0');

