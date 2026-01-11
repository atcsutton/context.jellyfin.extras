# context.jellyfin.extras

Kodi context menu addon that lists and plays Jellyfin extras (bonus content) for movies.

## Requirements

- **Kodi 19+** (Matrix or newer, Python 3)
- **Jellyfin for Kodi** (`plugin.video.jellyfin`) — **required** for playback
- **Jellyfin server** with extras/bonus content indexed

> ⚠️ **Important**: This addon requires [Jellyfin for Kodi](https://github.com/jellyfin/jellyfin-kodi) to be installed and configured. Extras playback is handled through the Jellyfin plugin.

## Features

- Context menu integration: right-click on any movie to access extras
- Thumbnails displayed in extras selection list
- Duration displayed for each extra
- Two connection modes: Quick Connect (recommended) and Manual
- Works with any Kodi skin

## Installation

1. Download the latest release ZIP file
2. In Kodi: Settings > Add-ons > Install from zip file
3. Select the downloaded ZIP
4. Configure the addon (see below)

## Configuration

### Quick Connect (Recommended)

Quick Connect must be enabled on your Jellyfin server:
**Jellyfin Admin Dashboard > Settings > Quick Connect**

Steps:
1. Open addon settings
2. Select connection method: "Quick Connect (recommended)"
3. Click "Link device via Quick Connect"
4. A code will be displayed
5. On your phone/computer, go to Jellyfin > Settings > Quick Connect
6. Enter the code to authorize the device

### Manual Configuration

If Quick Connect is unavailable:
1. Open addon settings
2. Select connection method: "Manual"
3. Fill in:
   - **Server URL**: Your Jellyfin server address (e.g., `https://jellyfin.example.com`)
   - **User ID**: Found in Jellyfin Dashboard > Users > click user > URL contains the ID
   - **API Key**: Generate one in Jellyfin Dashboard > API Keys

## Usage

1. Navigate to your movie library
2. Select a movie
3. Open the context menu (right-click or menu button)
4. Select "Jellyfin Extras"
5. Browse and select an extra to play

## How it works

- Only works on movies (`ListItem.DBTYPE = movie`)
- Resolves the movie via Jellyfin API using the IMDb ID
- Lists extras via `GET /Users/{userId}/Items/{itemId}/Extras`
- Playback is handled by `plugin.video.jellyfin`

## Troubleshooting

**"Addon not configured"**: Make sure you have completed the Quick Connect process or filled in the manual settings.

**"No extras found"**: The movie may not have any extras indexed in Jellyfin, or the movie could not be matched.

**"Jellyfin for Kodi is required for playback"**: Install and configure the Jellyfin for Kodi addon first.

## License

MIT
