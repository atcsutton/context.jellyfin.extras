# context.jellyfin.extras

Kodi context menu addon that lists Jellyfin extras for movies.

## Prerequisites

- Kodi 19+ (Python 3)
- Jellyfin server with extras indexed
- Jellyfin for Kodi installed (`plugin.video.jellyfin`) for playback

## Configuration

Open addon settings and fill:
- Jellyfin server URL
- Jellyfin API key
- Jellyfin UserId
- Verify HTTPS certificates (optional)
- Debug logging (optional)

## Behavior (V1.0.0)

- Only works on movies (`ListItem.DBTYPE = movie`)
- Resolves the movie via `GET /Search/Hints` using the IMDb id
- Lists extras via `GET /Users/{userId}/Items/{itemId}/Extras`
- Playback is user-initiated: extras are listed first; selecting an item starts playback via `plugin.video.jellyfin`
