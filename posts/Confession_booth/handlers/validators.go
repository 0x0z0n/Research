package handlers

import (
	"errors"
	"net/url"
	"strings"
)

func validateProfilePictureURL(profileURL string) error {
	if !strings.HasPrefix(profileURL, "http://") && !strings.HasPrefix(profileURL, "https://") {
		return errors.New("Invalid profile picture URL")
	}

	u, err := url.Parse(profileURL)
	if err != nil {
		return errors.New("Invalid URL format")
	}

	if u.Hostname() != "ui-avatars.com" {
		return errors.New("Profile picture must be from ui-avatars.com")
	}

	return nil
}
