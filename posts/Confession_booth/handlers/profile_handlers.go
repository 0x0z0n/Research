package handlers

import (
	"database/sql"
	"net/http"

	"confession-app/config"
	"confession-app/database"

	"github.com/labstack/echo/v4"
)

func ProfileHandler(c echo.Context) error {
	targetUsername := c.Param("username")
	loggedInUserID := c.Get("userID").(int)

	var targetUserID int
	var profilePic string
	var perms int
	var bio string

	err := database.DB.QueryRow("SELECT id, profile_picture_url, permission_level, COALESCE(bio, '') FROM users WHERE username = $1", targetUsername).Scan(&targetUserID, &profilePic, &perms, &bio)
	if err != nil {
		if err == sql.ErrNoRows {
			return c.Render(http.StatusNotFound, "error.html", map[string]interface{}{"Message": "User not found"})
		}
		return c.Render(http.StatusInternalServerError, "error.html", map[string]interface{}{"Message": "Failed to retrieve user profile"})
	}

	role := "User"
	if perms == config.PermissionAdmin {
		role = "Admin"
	}

	rows, err := database.DB.Query("SELECT id, content, created_at FROM confessions WHERE user_id = $1 ORDER BY created_at DESC", targetUserID)
	if err != nil {
		return c.Render(http.StatusInternalServerError, "error.html", map[string]interface{}{"Message": "Failed to fetch confessions"})
	}
	defer rows.Close()

	type Confession struct {
		ID        int
		Content   string
		CreatedAt string
	}

	var confessions []Confession
	for rows.Next() {
		var c Confession
		if err := rows.Scan(&c.ID, &c.Content, &c.CreatedAt); err != nil {
			continue
		}
		confessions = append(confessions, c)
	}

	isOwner := loggedInUserID == targetUserID

	data := map[string]interface{}{
		"Username":    targetUsername,
		"ProfilePic":  profilePic,
		"Role":        role,
		"Bio":         bio,
		"Confessions": confessions,
		"IsOwner":     isOwner,
	}

	return c.Render(http.StatusOK, "profile.html", data)
}

func UpdateProfileHandler(c echo.Context) error {
	userID := c.Get("userID").(int)
	bio := c.FormValue("bio")
	profilePicURL := c.FormValue("profile_picture_url")

	// If bio is provided, update bio
	if bio != "" {
		if err := database.UpdateUserBio(userID, bio); err != nil {
			return c.String(http.StatusInternalServerError, "Failed to update bio")
		}
	}

	// If profile picture URL is provided, validate and update it
	if profilePicURL != "" {
		if err := validateProfilePictureURL(profilePicURL); err != nil {
			return c.String(http.StatusBadRequest, err.Error())
		}
		if err := database.UpdateUserProfilePicture(userID, profilePicURL); err != nil {
			return c.String(http.StatusInternalServerError, "Failed to update profile picture")
		}
	}

	return c.String(http.StatusOK, "Profile updated")
}

func MyProfileHandler(c echo.Context) error {
	userID := c.Get("userID").(int)

	var username string
	err := database.DB.QueryRow("SELECT username FROM users WHERE id = $1", userID).Scan(&username)
	if err != nil {
		return c.Render(http.StatusNotFound, "error.html", map[string]interface{}{"Message": "User not found"})
	}

	return c.Redirect(http.StatusSeeOther, "/profile/"+username)
}
