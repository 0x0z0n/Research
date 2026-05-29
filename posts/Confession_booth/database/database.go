package database

import (
	"database/sql"
	"fmt"
	"log"
	"os"

	_ "github.com/lib/pq"
)

var DB *sql.DB

const (
	defaultDbHost = "localhost"
	defaultDbPort = "5432"
	dbUser        = "ctf_user"
	dbName        = "ctf_db"
)

func InitDB() error {
	dbPassword := os.Getenv("CTF_DB_PASSWORD")
	if dbPassword == "" {
		log.Fatal("Fatal: CTF_DB_PASSWORD environment variable not set.")
	}

	dbHost := os.Getenv("CTF_DB_HOST")
	if dbHost == "" {
		dbHost = defaultDbHost
	}

	dbPort := os.Getenv("CTF_DB_PORT")
	if dbPort == "" {
		dbPort = defaultDbPort
	}

	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	var err error
	DB, err = sql.Open("postgres", connStr)
	if err != nil {
		return err
	}

	if err = DB.Ping(); err != nil {
		return err
	}

	createTableSQL := `
    DROP TABLE IF EXISTS confessions;
    DROP TABLE IF EXISTS users;
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        profile_picture_url TEXT,
        permission_level INT,
        bio TEXT
    );

    CREATE TABLE confessions (
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(id) ON DELETE CASCADE,
        content TEXT NOT NULL,
        show INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    `
	_, err = DB.Exec(createTableSQL)
	if err != nil {
		log.Fatalf("Failed to create tables: %v", err)
	}
	log.Println("Database initialized and 'users' and 'confessions' tables created.")

	return nil
}
