package main

import (
	"fmt"
	"html/template"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"confession-app/auth"
	"confession-app/config"
	"confession-app/database"
	"confession-app/handlers"

	"github.com/labstack/echo/v4"
)

type TemplateRenderer struct {
	templates map[string]*template.Template
}

func (t *TemplateRenderer) Render(w io.Writer, name string, data interface{}, c echo.Context) error {
	ts, ok := t.templates[name]
	if !ok {
		return echo.NewHTTPError(http.StatusInternalServerError, "Template not found: "+name)
	}

	var templateData map[string]interface{}
	if data != nil {
		if dataMap, ok := data.(map[string]interface{}); ok {
			templateData = dataMap
		} else {
			templateData = map[string]interface{}{}
		}
	} else {
		templateData = map[string]interface{}{}
	}

	_, isLoggedIn := c.Get("userID").(int)
	templateData["IsLoggedIn"] = isLoggedIn

	userPerms, ok := c.Get("userPerms").(int)
	if ok && userPerms == config.PermissionAdmin {
		templateData["IsAdmin"] = true
	} else {
		templateData["IsAdmin"] = false
	}

	return ts.ExecuteTemplate(w, "base", templateData)
}

func LoadTemplates() (map[string]*template.Template, error) {
	templates := make(map[string]*template.Template)

	pages, err := filepath.Glob("templates/*.html")
	if err != nil {
		return nil, err
	}

	for _, page := range pages {
		name := filepath.Base(page)
		if name == "base.html" {
			continue
		}
		ts, err := template.ParseFiles("templates/base.html", page)
		if err != nil {
			return nil, err
		}
		templates[name] = ts
		log.Printf("Loaded template: %s", name)
	}

	return templates, nil
}

func main() {
	log.Println("Waiting for database to start (5s)...")
	time.Sleep(5 * time.Second)

	if err := database.InitDB(); err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	log.Println("Database connection successful.")

	tmpls, err := LoadTemplates()
	if err != nil {
		log.Fatalf("Failed to load templates: %v", err)
	}
	log.Println("HTML templates loaded.")

	e := echo.New()
	e.Renderer = &TemplateRenderer{
		templates: tmpls,
	}

	e.Static("/static", "static")

	// Health check endpoint for Kubernetes
	e.GET("/healthz", func(c echo.Context) error {
		return c.String(http.StatusOK, "ok")
	})

	e.GET("/", handlers.IndexHandler)
	e.Match([]string{"GET", "POST"}, "/auth/register", handlers.RegisterHandler)
	e.Match([]string{"GET", "POST"}, "/auth/login", handlers.LoginHandler)
	e.GET("/auth/logout", handlers.LogoutHandler)
	e.GET("/auth/account", handlers.AccountHandler, auth.AuthMiddleware)
	e.Match([]string{"GET", "POST"}, "/auth/change-password", handlers.ChangePasswordHandler, auth.AuthMiddleware)

	e.GET("/profile/:username", handlers.ProfileHandler, auth.AuthMiddleware)
	e.GET("/my-profile", handlers.MyProfileHandler, auth.AuthMiddleware)
	e.POST("/profile/update", handlers.UpdateProfileHandler, auth.AuthMiddleware)
	e.GET("/feed", handlers.FeedHandler, auth.AuthMiddleware)
	e.POST("/confession", handlers.CreateConfessionHandler, auth.AuthMiddleware)
	e.DELETE("/confession/:id", handlers.DeleteConfessionHandler, auth.AuthMiddleware)

	adminGroup := e.Group("/admin")
	adminGroup.Use(auth.AuthMiddleware)
	adminGroup.Use(auth.AdminMiddleware)
	adminGroup.GET("", handlers.AdminHandler)
	adminGroup.POST("/promote", handlers.PromoteHandler)

	adminGroup.GET("/confessions", handlers.AdminConfessionsHandler)
	adminGroup.POST("/confessions/approve/:id", handlers.ApproveConfessionHandler)
	adminGroup.DELETE("/confessions/:id", handlers.DeleteConfessionAdminHandler)

	bindIP := os.Getenv("BIND_IP")
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	var addr string
	if bindIP != "" {
		addr = fmt.Sprintf("%s:%s", bindIP, port)
	} else {
		addr = fmt.Sprintf(":%s", port)
	}

	log.Printf("Starting server on %s...", addr)
	if err := e.Start(addr); err != nil {
		log.Fatal(err)
	}
}
