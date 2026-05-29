package database

import (
	"confession-app/config"
)

func CreateUser(username, passwordHash, profilePicURL string) (int, error) {
	insertStmt := `INSERT INTO users (username, password_hash, profile_picture_url) VALUES ($1, $2, $3) RETURNING id`
	var userID int
	err := DB.QueryRow(insertStmt, username, passwordHash, profilePicURL).Scan(&userID)
	return userID, err
}

func UpdateUserBio(userID int, bio string) error {
	_, err := DB.Exec("UPDATE users SET bio = $1 WHERE id = $2", bio, userID)
	return err
}

func UpdateUserProfilePicture(userID int, profilePicURL string) error {
	_, err := DB.Exec("UPDATE users SET profile_picture_url = $1 WHERE id = $2", profilePicURL, userID)
	return err
}

func UpdateUserPassword(userID int, passwordHash string) error {
	_, err := DB.Exec("UPDATE users SET password_hash = $1 WHERE id = $2", passwordHash, userID)
	return err
}

func GetUserPasswordHash(userID int) (string, error) {
	var dbHashedPassword string
	err := DB.QueryRow("SELECT password_hash FROM users WHERE id = $1", userID).Scan(&dbHashedPassword)
	return dbHashedPassword, err
}

func UpdateUserPermissions(userID, perms int) error {
	updateStmt := `UPDATE users SET permission_level = $1 WHERE id = $2`
	_, err := DB.Exec(updateStmt, perms, userID)
	return err
}

func PromoteUserToAdmin(username string) error {
	var userID int
	err := DB.QueryRow("SELECT id FROM users WHERE username = $1", username).Scan(&userID)
	if err != nil {
		return err
	}
	return UpdateUserPermissions(userID, config.PermissionAdmin)
}
