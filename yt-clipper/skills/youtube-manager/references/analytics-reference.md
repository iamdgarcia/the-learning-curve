# YouTube Manager — Analytics Reference

Load this file when the user asks about specific metrics, API quota, or advanced queries.

## API Quota

| Operation | Cost | Daily limit |
|-----------|------|------------|
| `videos().insert()` (upload) | 1,600 units | ~6 uploads/day |
| `videos().update()` (schedule) | 50 units | ~200/day |
| `videos().list()` | 1 unit | ~10,000/day |
| `channels().list()` | 1 unit | ~10,000/day |
| Analytics queries | 0 units | separate quota |

Total daily quota: **10,000 units**. Upload is the expensive operation.
Failed uploads are saved to `temp/failed_uploads.json` — retry the next day.

## Valid Analytics Metrics (YouTube Analytics API v2)

```
views                      estimatedMinutesWatched
averageViewDuration        averageViewPercentage
subscribersGained          subscribersLost
likes                      dislikes
shares                     comments
annotationClickThroughRate annotationCloseRate
cardClickRate              cardTeaserClickRate
```

**Note:** `impressions` and `impressionClickThroughRate` are NOT available in the
Analytics API — use YouTube Studio UI for those.

## Valid Dimensions

```
video          channel        playlist       day
month          country        province       city
deviceType     operatingSystem
insightTrafficSourceType     insightTrafficSourceDetail
```

**Note:** `dayOfWeek` is NOT a valid dimension — derive from `day` dimension instead.

## Traffic Source Types

| Code | Description |
|------|-------------|
| `SHORTS` | Shorts feed / Shorts shelf |
| `YT_SEARCH` | YouTube search results |
| `SUBSCRIBER` | Subscriber home feed |
| `RELATED_VIDEO` | Suggested / related videos |
| `EXT_URL` | External websites / social media |
| `YT_CHANNEL` | Channel page |
| `YT_OTHER_PAGE` | Other YouTube pages |
| `NOTIFICATION` | Push notifications |
| `NO_LINK_OTHER` | Direct / unknown |
| `PLAYLIST` | Playlist pages |
| `END_SCREEN` | End screen cards |

## Device Types

`MOBILE`, `DESKTOP`, `TABLET`, `TV`, `GAME_CONSOLE`

## Scheduling — Privacy rules

- Videos can only be scheduled (`publishAt`) when `privacyStatus: "private"`
- `unlisted` videos **cannot** be scheduled — they stay unlisted forever
- `publishAt` format: `"2026-10-28T13:00:00.000Z"` (UTC, not local time)
- YouTube processes the transition within ~1 minute of the scheduled time

## Best publishing times for Spanish tech audience (data-backed)

From channel analytics (`report_schedule_insights`):
- **Sunday**: highest avg views (audience catching up with weekend content)
- **Friday**: second highest (end-of-week engagement peak)
- **Thursday**: strong weekday
- **Wednesday**: historically lowest for this channel
- **14:00 Madrid time** = 13:00 UTC (winter) / 12:00 UTC (summer)

Override these defaults by running `report_schedule_insights` and adjusting
`PREFERRED_SLOTS` in `schedule_clips.py`.

## Retention benchmarks for Shorts

| Retention % | Assessment |
|-------------|-----------|
| > 80% | Excellent — algorithm will push this |
| 60–80% | Good — normal for Shorts |
| 40–60% | Average |
| < 40% | Poor — hook needs improvement |

Note: retention > 100% means viewers are replaying the clip (looping) — very positive signal.

## Advanced: per-video analytics

```python
from src.youtube_analytics import report_video
report_video("VIDEO_ID")
```

Or query the Analytics API directly for date ranges:
```python
yta.reports().query(
    ids=f"channel=={channel_id}",
    startDate="2026-01-01", endDate="2026-10-23",
    metrics="views,averageViewPercentage",
    dimensions="video",
    filters="video==VIDEO_ID",
).execute()
```
