package handlers

import (
	"database/sql"
	"net/http"

	"confession-app/auth"
	"confession-app/config"
	"confession-app/database"

	"github.com/labstack/echo/v4"
	"golang.org/x/crypto/bcrypt"
)

func RegisterHandler(c echo.Context) error {
	if c.Request().Method == "GET" {
		return c.Render(http.StatusOK, "register.html", nil)
	}

	if c.Request().Method == "POST" {
		username := c.FormValue("username")
		password := c.FormValue("password")
		profilePicURL := c.FormValue("profile_picture_url")

		if username == "" || password == "" {
			return c.String(http.StatusBadRequest, "Username and password required")
		}

		if err := validateProfilePictureURL(profilePicURL); err != nil {
			return c.String(http.StatusBadRequest, err.Error())
		}

		hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
		if err != nil {
			return c.String(http.StatusInternalServerError, "Failed to hash password")
		}

		userID, err := database.CreateUser(username, string(hashedPassword), profilePicURL)
		if err != nil {
			return c.String(http.StatusInternalServerError, "Username already exists")
		}

		targetPerms := config.PermissionUser
		if config.AUTO_ADMIN_USER {
			targetPerms = config.PermissionAdmin
		}

		if err := database.UpdateUserPermissions(userID, targetPerms); err != nil {
			return c.String(http.StatusInternalServerError, "Failed to set user permissions")
		}

		// log.Printf("[User %d] Created and set to User permissions.", userID)
		return c.Redirect(http.StatusSeeOther, "/auth/login")
	}
	return c.String(http.StatusMethodNotAllowed, "Method not allowed")
}

func LoginHandler(c echo.Context) error {
	if c.Request().Method == "GET" {
		return c.Render(http.StatusOK, "login.html", nil)
	}

	if c.Request().Method == "POST" {
		username := c.FormValue("username")
		password := c.FormValue("password")

		var userID int
		var dbHashedPassword string
		var userPerms int

		selectStmt := `SELECT id, password_hash, permission_level FROM users WHERE username = $1`
		err := database.DB.QueryRow(selectStmt, username).Scan(&userID, &dbHashedPassword, &userPerms)

		if err == sql.ErrNoRows {
			return c.String(http.StatusUnauthorized, "Invalid credentials")
		}

		if err := bcrypt.CompareHashAndPassword([]byte(dbHashedPassword), []byte(password)); err != nil {
			return c.String(http.StatusUnauthorized, "Invalid credentials")
		}

		token, err := auth.CreateJWT(userID, userPerms)
		if err != nil {
			return c.String(http.StatusInternalServerError, "Failed to create session")
		}

		// log.Printf("[User %d] Logged in. Assigned perms: %d", userID, userPerms)

		response := map[string]string{
			"message": "Login successful",
			"token":   token,
		}
		return c.JSON(http.StatusOK, response)
	}
	return c.String(http.StatusMethodNotAllowed, "Method not allowed")
}

func LogoutHandler(c echo.Context) error {
	cookie := new(http.Cookie)
	cookie.Name = "booth_session"
	cookie.Value = ""
	cookie.Path = "/"
	cookie.MaxAge = -1
	c.SetCookie(cookie)

	return c.Redirect(http.StatusSeeOther, "/auth/login")
}

func ChangePasswordHandler(c echo.Context) error {
	if c.Request().Method == "GET" {
		return c.Render(http.StatusOK, "change_password.html", nil)
	}

	userID := c.Get("userID").(int)
	currentPassword := c.FormValue("current_password")
	newPassword := c.FormValue("new_password")

	if currentPassword == "" || newPassword == "" {
		return c.String(http.StatusBadRequest, "Current and new password required")
	}

	dbHashedPassword, err := database.GetUserPasswordHash(userID)
	if err != nil {
		return c.String(http.StatusInternalServerError, "Failed to fetch user")
	}

	if err := bcrypt.CompareHashAndPassword([]byte(dbHashedPassword), []byte(currentPassword)); err != nil {
		return c.String(http.StatusUnauthorized, "Incorrect current password")
	}

	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		return c.String(http.StatusInternalServerError, "Failed to hash new password")
	}

	if err := database.UpdateUserPassword(userID, string(hashedPassword)); err != nil {
		return c.String(http.StatusInternalServerError, "Failed to update password")
	}

	return c.String(http.StatusOK, "Password updated successfully")
}

func AccountHandler(c echo.Context) error {
	userID := c.Get("userID").(int)

	var profilePic string
	var bio string

	err := database.DB.QueryRow("SELECT profile_picture_url, COALESCE(bio, '') FROM users WHERE id = $1", userID).Scan(&profilePic, &bio)
	if err != nil {
		return c.Render(http.StatusInternalServerError, "error.html", map[string]interface{}{"Message": "Failed to fetch user data"})
	}

	data := map[string]interface{}{
		"ProfilePic": profilePic,
		"Bio":        bio,
	}

	return c.Render(http.StatusOK, "account_settings.html", data)
}
