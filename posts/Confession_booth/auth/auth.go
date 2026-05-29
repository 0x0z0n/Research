package auth

import (
	"crypto/rand"
	"log"
	"net/http"
	"strings"
	"time"

	"confession-app/config"

	"github.com/golang-jwt/jwt/v5"
	"github.com/labstack/echo/v4"
)

var jwtKey []byte

func init() {
	jwtKey = make([]byte, 64)
	if _, err := rand.Read(jwtKey); err != nil {
		log.Fatal("Failed to generate random JWT key: ", err)
	}
	log.Println("Random JWT key generated successfully (HS512).")
}

type Claims struct {
	UserID int `json:"user_id"`
	Perms  int `json:"perms"`
	jwt.RegisteredClaims
}

func CreateJWT(userID int, perms int) (string, error) {
	expirationTime := time.Now().Add(1 * time.Hour)
	claims := &Claims{
		UserID: userID,
		Perms:  perms,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expirationTime),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS512, claims)
	return token.SignedString(jwtKey)
}

func AuthMiddleware(next echo.HandlerFunc) echo.HandlerFunc {
	return func(c echo.Context) error {
		tokenString := ""

		authHeader := c.Request().Header.Get("Authorization")
		if authHeader != "" {
			tokenString = strings.TrimPrefix(authHeader, "Bearer ")
		}

		if tokenString == "" {
			cookie, err := c.Cookie("booth_session")
			if err == nil {
				tokenString = cookie.Value
			}
		}

		if tokenString == "" {
			return c.Render(http.StatusForbidden, "error.html", map[string]interface{}{"Message": "No token provided"})
		}

		claims := &Claims{}
		token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
			return jwtKey, nil
		})

		if err != nil {
			if err == jwt.ErrSignatureInvalid {
				return c.Render(http.StatusForbidden, "error.html", map[string]interface{}{"Message": "Invalid token signature"})
			}
			return c.Render(http.StatusForbidden, "error.html", map[string]interface{}{"Message": "Invalid token"})
		}

		if !token.Valid {
			return c.Render(http.StatusForbidden, "error.html", map[string]interface{}{"Message": "Invalid token"})
		}

		c.Set("userID", claims.UserID)
		c.Set("userPerms", claims.Perms)
		return next(c)
	}
}

func AdminMiddleware(next echo.HandlerFunc) echo.HandlerFunc {
	return func(c echo.Context) error {
		perms, ok := c.Get("userPerms").(int)

		if !ok || perms != config.PermissionAdmin {
			userID, _ := c.Get("userID").(int)
			log.Printf("Auth attempt blocked for user %d with perms %d", userID, perms)
			return c.Render(http.StatusForbidden, "error.html", map[string]interface{}{"Message": "Admin access required"})
		}
		return next(c)
	}
}
