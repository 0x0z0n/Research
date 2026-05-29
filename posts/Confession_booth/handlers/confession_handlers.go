package handlers

import (
	"database/sql"
	"net/http"
	"strconv"

	"confession-app/database"

	"github.com/labstack/echo/v4"
)

func CreateConfessionHandler(c echo.Context) error {
	userID := c.Get("userID").(int)
	content := c.FormValue("content")

	if content == "" {
		return c.String(http.StatusBadRequest, "Confession cannot be empty")
	}

	_, err := database.DB.Exec("INSERT INTO confessions (user_id, content) VALUES ($1, $2)", userID, content)
	if err != nil {
		return c.String(http.StatusInternalServerError, "Failed to save confession")
	}

	return c.String(http.StatusOK, "Confession saved")
}

func DeleteConfessionHandler(c echo.Context) error {
	userID := c.Get("userID").(int)
	confessionIDStr := c.Param("id")
	confessionID, err := strconv.Atoi(confessionIDStr)
	if err != nil {
		return c.String(http.StatusBadRequest, "Invalid confession ID")
	}

	// Verify ownership
	var ownerID int
	err = database.DB.QueryRow("SELECT user_id FROM confessions WHERE id = $1", confessionID).Scan(&ownerID)
	if err != nil {
		if err == sql.ErrNoRows {
			return c.String(http.StatusNotFound, "Confession not found")
		}
		return c.String(http.StatusInternalServerError, "Failed to fetch confession")
	}

	if ownerID != userID {
		return c.String(http.StatusForbidden, "You can only delete your own confessions")
	}

	_, err = database.DB.Exec("DELETE FROM confessions WHERE id = $1", confessionID)
	if err != nil {
		return c.String(http.StatusInternalServerError, "Failed to delete confession")
	}

	return c.String(http.StatusOK, "Confession deleted")
}

func FeedHandler(c echo.Context) error {
	type FeedItem struct {
		ID         int
		Content    string
		CreatedAt  string
		Username   string
		ProfilePic string
	}

	rows, err := database.DB.Query(`
		SELECT c.id, c.content, c.created_at, u.username, u.profile_picture_url
		FROM confessions c
		JOIN users u ON c.user_id = u.id
		WHERE c.show = 1
		ORDER BY c.created_at ASC
		LIMIT 15
	`)
	if err != nil {
		return c.Render(http.StatusInternalServerError, "error.html", map[string]interface{}{"Message": "Failed to fetch feed"})
	}
	defer rows.Close()

	var feed []FeedItem
	for rows.Next() {
		var item FeedItem
		if err := rows.Scan(&item.ID, &item.Content, &item.CreatedAt, &item.Username, &item.ProfilePic); err != nil {
			continue
		}
		feed = append(feed, item)
	}

	return c.Render(http.StatusOK, "feed.html", map[string]interface{}{
		"Feed": feed,
	})
}
