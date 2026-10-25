-- RAPHA - Hospital Management System: MySQL schema
-- Run in MySQL Workbench (or let the app create it automatically on start-up).
-- MySQL is used for storage only; lookups, ranges and sorting are done by the
-- application's own hash table, BST and merge sort.

CREATE DATABASE IF NOT EXISTS rapha_hospital
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE rapha_hospital;

CREATE TABLE IF NOT EXISTS patients (
    patient_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT CHECK (age BETWEEN 0 AND 120),
    gender VARCHAR(10),
    department VARCHAR(50),
    diagnosis VARCHAR(150),
    doctor VARCHAR(100),
    admission_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
