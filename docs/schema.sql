-- 企业IP地址管理系统 数据库结构
-- 演示默认用 SQLite；下面 MySQL 版给论文/部署用。
-- 字段与 backend/app/models/entities.py 保持一致。

-- =========================
-- MySQL 8.x
-- =========================
/*
CREATE DATABASE IF NOT EXISTS ipam DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ipam;

CREATE TABLE departments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  code VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  display_name VARCHAR(100) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(30) NOT NULL DEFAULT 'viewer',
  department_id INT NOT NULL,
  avatar_color VARCHAR(20) NOT NULL DEFAULT '#0d9488',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  auth_version INT NOT NULL DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_users_dept FOREIGN KEY (department_id) REFERENCES departments(id)
) ENGINE=InnoDB;

CREATE TABLE sites (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  code VARCHAR(50) NOT NULL UNIQUE,
  location VARCHAR(200) NOT NULL DEFAULT '',
  remark VARCHAR(500) NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE subnets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  site_id INT NOT NULL,
  department_id INT NOT NULL,
  name VARCHAR(100) NOT NULL,
  cidr VARCHAR(50) NOT NULL,
  gateway VARCHAR(50) NOT NULL DEFAULT '',
  vlan_id INT NULL,
  purpose VARCHAR(100) NOT NULL DEFAULT '通用',
  description TEXT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_subnets_cidr (cidr),
  KEY ix_subnets_site (site_id),
  CONSTRAINT fk_subnets_site FOREIGN KEY (site_id) REFERENCES sites(id),
  CONSTRAINT fk_subnets_dept FOREIGN KEY (department_id) REFERENCES departments(id)
) ENGINE=InnoDB;

CREATE TABLE devices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  device_type VARCHAR(30) NOT NULL DEFAULT 'other',
  mac VARCHAR(30) NULL,
  location VARCHAR(200) NULL,
  department_id INT NULL,
  owner_user_id INT NULL,
  remark VARCHAR(500) NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_devices_mac (mac),
  CONSTRAINT fk_devices_dept FOREIGN KEY (department_id) REFERENCES departments(id),
  CONSTRAINT fk_devices_owner FOREIGN KEY (owner_user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE ip_addresses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  subnet_id INT NOT NULL,
  address VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'free',
  hostname VARCHAR(100) NULL,
  mac VARCHAR(30) NULL,
  device_name VARCHAR(100) NULL,
  device_type VARCHAR(30) NULL,
  device_id INT NULL,
  owner_user_id INT NULL,
  department_id INT NULL,
  allocated_at DATETIME NULL,
  expire_at DATE NULL,
  remark VARCHAR(500) NULL,
  is_network_or_broadcast TINYINT(1) NOT NULL DEFAULT 0,
  UNIQUE KEY uq_ip_address (address),
  KEY ix_ip_subnet (subnet_id),
  KEY ix_ip_status (status),
  KEY ix_ip_device (device_id),
  CONSTRAINT fk_ip_subnet FOREIGN KEY (subnet_id) REFERENCES subnets(id),
  CONSTRAINT fk_ip_device FOREIGN KEY (device_id) REFERENCES devices(id),
  CONSTRAINT fk_ip_owner FOREIGN KEY (owner_user_id) REFERENCES users(id),
  CONSTRAINT fk_ip_dept FOREIGN KEY (department_id) REFERENCES departments(id)
) ENGINE=InnoDB;

CREATE TABLE allocation_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ip_address_id INT NULL,
  address VARCHAR(50) NOT NULL,
  action VARCHAR(20) NOT NULL,
  operator_id INT NULL,
  operator_name VARCHAR(100) NOT NULL DEFAULT '',
  detail VARCHAR(500) NOT NULL DEFAULT '',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY ix_log_address (address),
  CONSTRAINT fk_log_ip FOREIGN KEY (ip_address_id) REFERENCES ip_addresses(id),
  CONSTRAINT fk_log_op FOREIGN KEY (operator_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE conflicts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ip_address_id INT NULL,
  ip_address VARCHAR(50) NOT NULL,
  subnet_cidr VARCHAR(50) NOT NULL DEFAULT '',
  conflict_type VARCHAR(40) NOT NULL,
  detail TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'open',
  detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY ix_conflict_status (status),
  CONSTRAINT fk_conflict_ip FOREIGN KEY (ip_address_id) REFERENCES ip_addresses(id)
) ENGINE=InnoDB;
*/

-- =========================
-- SQLite（与程序 create_all 一致，便于对照）
-- =========================

CREATE TABLE IF NOT EXISTS departments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(100) NOT NULL UNIQUE,
  code VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  display_name VARCHAR(100) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(30) NOT NULL DEFAULT 'viewer',
  department_id INTEGER NOT NULL,
  avatar_color VARCHAR(20) NOT NULL DEFAULT '#0d9488',
  is_active BOOLEAN NOT NULL DEFAULT 1,
  auth_version INTEGER NOT NULL DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS sites (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(100) NOT NULL,
  code VARCHAR(50) NOT NULL UNIQUE,
  location VARCHAR(200) NOT NULL DEFAULT '',
  remark VARCHAR(500),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subnets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  site_id INTEGER NOT NULL,
  department_id INTEGER NOT NULL,
  name VARCHAR(100) NOT NULL,
  cidr VARCHAR(50) NOT NULL UNIQUE,
  gateway VARCHAR(50) NOT NULL DEFAULT '',
  vlan_id INTEGER,
  purpose VARCHAR(100) NOT NULL DEFAULT '通用',
  description TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(site_id) REFERENCES sites(id),
  FOREIGN KEY(department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS devices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(100) NOT NULL,
  device_type VARCHAR(30) NOT NULL DEFAULT 'other',
  mac VARCHAR(30) UNIQUE,
  location VARCHAR(200),
  department_id INTEGER,
  owner_user_id INTEGER,
  remark VARCHAR(500),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(department_id) REFERENCES departments(id),
  FOREIGN KEY(owner_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS ip_addresses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subnet_id INTEGER NOT NULL,
  address VARCHAR(50) NOT NULL UNIQUE,
  status VARCHAR(20) NOT NULL DEFAULT 'free',
  hostname VARCHAR(100),
  mac VARCHAR(30),
  device_name VARCHAR(100),
  device_type VARCHAR(30),
  device_id INTEGER,
  owner_user_id INTEGER,
  department_id INTEGER,
  allocated_at DATETIME,
  expire_at DATE,
  remark VARCHAR(500),
  is_network_or_broadcast BOOLEAN NOT NULL DEFAULT 0,
  FOREIGN KEY(subnet_id) REFERENCES subnets(id),
  FOREIGN KEY(device_id) REFERENCES devices(id),
  FOREIGN KEY(owner_user_id) REFERENCES users(id),
  FOREIGN KEY(department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS allocation_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip_address_id INTEGER,
  address VARCHAR(50) NOT NULL,
  action VARCHAR(20) NOT NULL,
  operator_id INTEGER,
  operator_name VARCHAR(100) NOT NULL DEFAULT '',
  detail VARCHAR(500) NOT NULL DEFAULT '',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(ip_address_id) REFERENCES ip_addresses(id),
  FOREIGN KEY(operator_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS conflicts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip_address_id INTEGER,
  ip_address VARCHAR(50) NOT NULL,
  subnet_cidr VARCHAR(50) NOT NULL DEFAULT '',
  conflict_type VARCHAR(40) NOT NULL,
  detail TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'open',
  detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(ip_address_id) REFERENCES ip_addresses(id)
);

CREATE INDEX IF NOT EXISTS ix_ip_status ON ip_addresses(status);
CREATE INDEX IF NOT EXISTS ix_ip_subnet ON ip_addresses(subnet_id);
CREATE INDEX IF NOT EXISTS ix_log_address ON allocation_logs(address);
CREATE INDEX IF NOT EXISTS ix_conflict_status ON conflicts(status);
