package handlers

import (
	"net/http"
	"strconv"

	"confession-app/database"

	"os"
	"strings"

	"github.com/labstack/echo/v4"
)

func AdminHandler(c echo.Context) error {
	return c.Render(http.StatusOK, "admin.html", nil)
}

func PromoteHandler(c echo.Context) error {
	username := c.FormValue("username")
	if username == "" {
		return c.String(http.StatusBadRequest, "Username required")
	}

	if err := database.PromoteUserToAdmin(username); err != nil {
		return c.String(http.StatusInternalServerError, "Failed to promote user")
	}

	return c.String(http.StatusOK, "User promoted to admin")
}

func AdminConfessionsHandler(c echo.Context) error {
	status := c.QueryParam("status")
	search := c.QueryParam("search")

	query := `
		SELECT c.id, c.content, c.created_at, c.show, u.username
		FROM confessions c
		JOIN users u ON c.user_id = u.id
		WHERE 1=1
	`
	var args []interface{}
	argCount := 1

	if status == "pending" {
		query += " AND c.show = 0"
	}

	if search != "" {
		query += " AND c.content ILIKE $" + strconv.Itoa(argCount)
		args = append(args, "%"+search+"%")
		argCount++
	}

	query += " ORDER BY c.created_at DESC"

	rows, err := database.DB.Query(query, args...)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": "Failed to fetch confessions"})
	}
	defer rows.Close()

	type ConfessionItem struct {
		ID        int
		Content   string
		CreatedAt string
		Username  string
		Show      int
	}

	var confessions []ConfessionItem
	for rows.Next() {
		var item ConfessionItem
		if err := rows.Scan(&item.ID, &item.Content, &item.CreatedAt, &item.Show, &item.Username); err != nil {
			continue
		}
		confessions = append(confessions, item)
	}

	return c.JSON(http.StatusOK, confessions)
}

func ApproveConfessionHandler(c echo.Context) error {
	idStr := c.Param("id")
	if idStr == "flag" {
		flagContent, err := os.ReadFile("/flag.txt")
		if err != nil {
			return c.JSON(http.StatusInternalServerError, map[string]string{
				"error":   "Failed to read flag",
				"details": err.Error(),
			})
		}
		return c.JSON(http.StatusOK, map[string]string{
			"flag": strings.TrimSpace(string(flagContent)),
		})
	}

	// id, err := strconv.Atoi(idStr)
	// if err != nil {
	// 	return c.String(http.StatusBadRequest, "Invalid ID")
	// }

	// _, err = database.DB.Exec("UPDATE confessions SET show = 1 WHERE id = $1", id)
	// if err != nil {
	// 	return c.String(http.StatusInternalServerError, "Failed to approve confession")
	// }

	return c.String(http.StatusOK, "Confession approved")
}

func DeleteConfessionAdminHandler(c echo.Context) error {
	// idStr := c.Param("id")
	// id, err := strconv.Atoi(idStr)
	// if err != nil {
	// 	return c.String(http.StatusBadRequest, "Invalid ID")
	// }

	// _, err = database.DB.Exec("DELETE FROM confessions WHERE id = $1", id)
	// if err != nil {
	// 	return c.String(http.StatusInternalServerError, "Failed to delete confession")
	// }

	return c.String(http.StatusOK, "Confession deleted")
}
