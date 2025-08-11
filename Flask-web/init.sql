-- Tạo database nếu chưa có
CREATE DATABASE IF NOT EXISTS iot02;
USE my_app_db;

-- Tạo bảng users
CREATE TABLE IF NOT EXISTS users (
    id INT(11) NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    create_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
)

-- Tạo bảng user_otps
CREATE TABLE IF NOT EXISTS pending_users (
    id INT(11) NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    otp_code VARCHAR(10),
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (id)
) 