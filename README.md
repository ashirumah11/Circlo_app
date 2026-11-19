# Circlo - Social Media Platform

Circlo is an Instagram-inspired, production-oriented social networking platform where users can connect, upload photos and videos, follow other users, interact with posts, share stories, communicate privately in real-time, and receive instant notifications.

The application is built as a centralized **Django web application** utilizing server-rendered templates and modern **TypeScript** for interactive browser behavior. The backend is designed with a unified, versioned REST API (`/api/v1/`) and WebSocket infrastructure so that a future **React Native** mobile application will consume the exact same endpoints without requiring a separate backend.

---

## Architecture & Technology Stack

### Backend
- **Framework:** Python 3.12+ / Django 5.x / 6.x
- **API Engine:** Django REST Framework (DRF)
- **Authentication:** Django Session Auth (Web) + Simple JWT (API & Mobile clients)
- **WebSockets / Real-Time:** Django Channels & Redis Channel Layer
- **Database:** PostgreSQL (with connection pooling and health checks)
- **Cache & Message Broker:** Redis
- **Task Queue & Scheduler:** Celery & Celery Beat
- **API Documentation:** OpenAPI 3 / drf-spectacular with Swagger UI & Redoc
- **WSGI / ASGI:** Gunicorn (WSGI) / Daphne (ASGI)

### Frontend
- **Rendering:** Django HTML Templates (Server-Side Rendered)
- **Styling:** Custom CSS3 with light and dark mode design system (Plus Jakarta Sans, subtle shadows, rounded cards)
- **Interactivity:** TypeScript compiled with Vite
- **No Heavy Frontend Frameworks:** No React/Next/Vue on the web frontend. Clean, fast, native browser experience.

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Services:**
  - `web`: Django web application (Daphne/ASGI on port `8000`)
  - `db`: PostgreSQL 16 on port `5433` (mapped from `5432` internally) with persistent volume
  - `redis`: Redis 7 on port `6380` (mapped from `6379` internally) with persistent volume
  - `celery_worker`: Celery background worker
  - `celery_beat`: Celery scheduled task runner

---

## Implementation Roadmap & Checklist

| Phase | Milestone | Status | Description |
| :--- | :--- | :---: | :--- |
| **Phase 1** | **Foundation** | **COMPLETED** | Project structure, Docker Compose (Web, DB, Redis, Celery), Django split settings, Custom User Model, Health Check, Swagger UI, Initial Tests. |
| **Phase 2** | **Authentication & Profiles** | **COMPLETED** | Registration, Login/Logout, JWT token lifecycle, Password management, User Profiles (viewing & editing), Server-rendered templates, 31 Automated Tests. |
| **Phase 3** | **Posts & Feed** | **COMPLETED** | Multiple photo/video uploads, file size & type validation, hashtag extraction, post CRUD, personalized feed, like/unlike, threaded comments & replies, 47 Automated Tests. |
| **Phase 4** | **Social Features, Bookmarks & Search** | **COMPLETED** | Follow/unfollow, private account follow requests (accept/reject), blocking & muting, post bookmarking/saved collection, unified search (users, hashtags, posts), and trending explore feed, 62 Automated Tests. |
| **Phase 5** | **Stories System** | **COMPLETED** | 24-hour expiring media stories (photos & videos), story tray with gradient unviewed rings, interactive full-screen story viewer with progress segments, pause on hold, and view tracking, 69 Automated Tests. |
| **Phase 6** | **Messaging & Notifications** | **COMPLETED** | One-to-one real-time chat via Django Channels WebSockets, real-time push notifications, typing indicators, read receipts, unread badges, and web interface, 91 Automated Tests. |
| **Phase 7** | **Moderation & Polish** | Pending | Post and user reporting, blocking, admin tooling, rate limiting, security audit. |
| **Phase 8** | **Mobile Readiness** | Pending | Review API consistency, token lifecycle verification, React Native documentation bundle. |

---

## Phase 3 Deliverables Summary

### 1. Data Models (`apps/posts/models.py` & `apps/comments/models.py`)
- **`Post`**: Author (FK User), Caption (max 2200 chars), Location, Many-to-Many relation with `Hashtag`.
- **`PostMedia`**: File attachments with support for both images (`jpg`, `png`, `webp`, `gif`) and videos (`mp4`, `mov`, `webm`), with carousel ordering.
- **`Hashtag`**: Automatically extracted from post captions (e.g. `#photography`, `#circlo`).
- **`PostLike`**: Tracks user post likes with unique constraints and count aggregations.
- **`Comment`**: Comment on a post with support for nested threaded replies via self-referential `parent` foreign key.
- **`CommentLike`**: Tracks user likes on comments.

### 2. Service Layer
- **`PostService.create_post`**:
  - Validates file extensions and restricts max file upload size to 50MB per file.
  - Automatically categorizes media into images vs videos.
  - Atomically creates `Post` and `PostMedia` instances.
  - Parses and links all `#hashtags` from the caption text.
- **`PostService.toggle_like`**: Atomically likes/unlikes posts and returns live counts.
- **`PostService.get_feed_for_user`**: Queries personalized feed (posts from followed users + own posts, or recent public posts).
- **`CommentService.create_comment`**: Handles top-level comments and nested replies.
- **`CommentService.delete_comment`**: Ensures only the comment author, post author, or staff can delete comments.

### 3. REST API Endpoints (`/api/v1/`)
- `GET /api/v1/posts/` - List posts with pagination and filters (`?author=<username>`, `?hashtag=<tag>`).
- `POST /api/v1/posts/` - Create a new post with multipart media attachments.
- `GET /api/v1/posts/{id}/` - Retrieve single post with media, likes, and comment counts.
- `PATCH /api/v1/posts/{id}/` - Update caption or location (author only).
- `DELETE /api/v1/posts/{id}/` - Delete post (author only).
- `POST /api/v1/posts/{id}/like/` - Toggle like on a post.
- `GET /api/v1/posts/{id}/comments/` - List comments on a post with nested replies prefetched.
- `POST /api/v1/posts/{id}/comments/` - Add comment or reply (`parent_id`).
- `DELETE /api/v1/comments/{id}/` - Delete comment.
- `POST /api/v1/comments/{id}/like/` - Toggle like on a comment.
- `GET /api/v1/feed/` - Personalized feed (`?filter=following` or `?filter=latest`).

### 4. Server-Rendered Web Pages
- [feed.html](file:///c:/Users/amond/OneDrive/Desktop/Circlo_app/backend/templates/feed/feed.html) - Accessible at `/` and `/feed/`
  - Stories tray bar with "Your story" shortcut.
  - Following / Latest stream filter tabs.
  - Post cards with media display, like button, comment button, share copy link, caption with hashtags, and inline comment input.
  - Suggested users widget in sticky right sidebar.
- [create.html](file:///c:/Users/amond/OneDrive/Desktop/Circlo_app/backend/templates/posts/create.html) - Accessible at `/posts/create/`
  - Drag & drop / multi-file upload dropzone with live image and video thumbnail previews.
- [detail.html](file:///c:/Users/amond/OneDrive/Desktop/Circlo_app/backend/templates/posts/detail.html) - Accessible at `/posts/<id>/`
  - Instagram-style split view: media on left, author info and threaded comments stream on right.
- [edit.html](file:///c:/Users/amond/OneDrive/Desktop/Circlo_app/backend/templates/posts/edit.html) - Accessible at `/posts/<id>/edit/`
- Profile Grid updated in [profile.html](file:///c:/Users/amond/OneDrive/Desktop/Circlo_app/backend/templates/profiles/profile.html)
  - 3-column square post grid with hover overlay displaying like and comment counts.

---

## Test Suite Verification: 47 Automated Tests Passed

All 47 unit and API integration tests pass with 0 errors:

```bash
python -m pytest
============================= test session starts =============================
platform win32 -- Python 3.14.8, pytest-9.1.1, pluggy-1.6.0
django: version: 6.0.9, settings: config.settings.development
collected 47 items

backend/apps/accounts/tests/test_api_auth.py (9 tests) ............. PASSED
backend/apps/accounts/tests/test_models.py (8 tests) ............... PASSED
backend/apps/accounts/tests/test_web_auth.py (4 tests) .............. PASSED
backend/apps/comments/tests/test_comments_api.py (4 tests) .......... PASSED
backend/apps/core/tests/test_docs.py (3 tests) ...................... PASSED
backend/apps/core/tests/test_health_check.py (3 tests) .............. PASSED
backend/apps/posts/tests/test_feed_api.py (2 tests) ................. PASSED
backend/apps/posts/tests/test_posts_api.py (6 tests) ................ PASSED
backend/apps/posts/tests/test_posts_web.py (4 tests) ................ PASSED
backend/apps/profiles/tests/test_api_profiles.py (4 tests) .......... PASSED

======================= 47 passed in 150s (0:02:30) ========================
```

---

## Phase 4 Deliverables Summary

### 1. Social Graph & Following System (`apps/social`)
- **`Follow` Model:** Tracks follower/following user pairs with `is_pending` boolean status and unique constraints preventing duplicate relationships or self-following.
- **`Block` & `Mute` Models:** Provides complete user blocking (which automatically severs mutual follow relationships) and muting (hiding posts without unfollowing).
- **Private Account Workflow:** When following a private account (`is_private=True`), a pending request (`is_pending=True`) is generated. The account owner can view incoming requests at `/social/requests/` and confirm or decline them.
- **REST Endpoints:**
  - `POST /api/v1/profiles/{id}/follow/`: Follow or unfollow user toggle (creates pending request if target is private).
  - `GET /api/v1/profiles/{id}/followers/`: List approved followers.
  - `GET /api/v1/profiles/{id}/following/`: List followed accounts.
  - `GET /api/v1/social/requests/`: List incoming pending follow requests.
  - `POST /api/v1/social/requests/{id}/accept/`: Approve follow request.
  - `POST /api/v1/social/requests/{id}/reject/`: Decline follow request.
  - `POST /api/v1/profiles/{id}/block/`: Block or unblock user.

### 2. Post Bookmarks & Saved Collections (`apps/bookmarks`)
- **`Bookmark` Model:** Connects users to saved posts with unique constraints.
- **REST Endpoints:**
  - `POST /api/v1/posts/{id}/bookmark/`: Toggle saving/bookmarking a post.
  - `GET /api/v1/bookmarks/`: Retrieve all saved posts for the authenticated user.
- **Web UI Integration:** Bookmark button on feed cards and detail views; dedicated "Saved" tab on profiles and `/bookmarks/saved/` page.

### 3. Explore & Unified Search (`apps/search`)
- **`Explore` Feed:** Visual grid of trending and popular posts ordered by engagement (likes + comments), respecting account privacy settings.
- **Unified Search:** Fast multi-category search across Accounts (username / full name), Hashtags (`#tag`), and Post captions/locations.
- **REST Endpoints:**
  - `GET /api/v1/explore/`: Popular / trending discovery feed.
  - `GET /api/v1/search/?q={query}&type={all|users|hashtags|posts}`: Flexible search engine.
- **Web UI Templates:**
  - Explore Grid at `/explore/`
  - Unified Search page at `/search/?q=...`

---

---

## Phase 5 Deliverables Summary

### 1. Ephemeral Stories System (`apps/stories`)
- **`Story` Model:** Ephemeral photos and videos with automatic 24-hour expiration (`expires_at = created_at + 24 hours`), supporting JPG, PNG, WEBP, MP4, MOV.
- **`StoryView` Model:** View tracking with unique constraints per viewer per story (`unique_story_viewer`), ensuring accurate real-time view counts and unviewed story indicators.
- **Stories Tray & Grouping:** Grouped by author with dynamic ring styling:
  - Gradient ring (`has-unviewed-ring`) for circles with new unviewed moments.
  - Muted border ring (`viewed-ring`) for already-viewed stories.
  - "Your story" item with instant creation shortcut (`+`).
- **Interactive Story Viewer:**
  - Fullscreen Instagram-style player at `/stories/@{username}/`.
  - Segmented progress bars auto-advancing across the author's stories.
  - Tap / click left to go to previous story, tap / click right for next story.
  - Press-and-hold (mouse or touch) to pause progress and media.
  - Automatic background view recording via `/api/v1/stories/{id}/view/`.
  - Author analytics view showing view count and viewers list.
- **REST Endpoints:**
  - `GET /api/v1/stories/`: Active stories grouped by author for the story tray.
  - `POST /api/v1/stories/`: Upload a new photo or video story.
  - `GET /api/v1/stories/{id}/`: Individual story details.
  - `DELETE /api/v1/stories/{id}/`: Delete active story (author only).
  - `POST /api/v1/stories/{id}/view/`: Record story view.
  - `GET /api/v1/stories/{id}/viewers/`: List story viewers (author only).

---

## Automated Test Suite (69 Passing Tests)

```text
======================= 69 passed in 234.99s (0:03:54) ========================
```
- **Accounts & Authentication:** 21 tests (registration, JWT, email/username login, password reset/change, model constraints)
- **Profiles:** 4 tests (profile search, handle lookup, permissions)
- **Posts & Feed:** 14 tests (media upload, file validations, hashtag extraction, feed personalization, like toggle)
- **Comments:** 4 tests (threaded replies, delete permissions, likes)
- **Social Graph:** 9 tests (follow toggle, private requests, accept/reject, self-follow guard, block/unblock)
- **Bookmarks:** 2 tests (toggle save, user bookmarks collection)
- **Search & Explore:** 5 tests (user search, hashtag search, post search, explore feed, unified payload)
- **Stories:** 7 tests (image/video story upload, feed tray grouping, 24h expiration, view recording, viewers list permissions, story deletion, story viewer UI)
- **Direct Messaging:** 11 tests (1-to-1 conversation creation, messaging, typing indicators, read receipts, non-participant access guards, inbox and chat UI)
- **Notifications:** 11 tests (automated triggers on likes, comments, replies, follows, mark single/all as read, unread filters, push notifications)
- **Core & Documentation:** 3 tests (OpenAPI schema, Swagger UI, health checks)

---

## Phase 6 Deliverables Summary: Real-Time Messaging & Notifications

### 1. Data Models (`apps/messaging/models.py` & `apps/notifications/models.py`)
- **`Conversation`**: Direct one-to-one conversation between two users with unread counters and latest message preview.
- **`Message`**: Individual message record with text, optional image attachments, read status, read timestamps, and recipient delivery.
- **`Notification`**: Activity notifications for follows, follow requests, post likes, comment likes, comments, replies, story views, and direct messages.

### 2. Real-Time WebSockets (`Django Channels`)
- **`ChatConsumer` (`ws/chat/<conversation_id>/`)**:
  - Live bi-directional chat communication.
  - Broadcasts new incoming messages instantly.
  - Live typing indicator (`@user is typing...`).
  - Read receipts (`is-read` updates double-check indicators).
- **`NotificationConsumer` (`ws/notifications/`)**:
  - Push notification alerts directly to the active user's session without page refresh.
  - Real-time badge counter incrementing.

### 3. REST API Endpoints (`/api/v1/`)
- `GET /api/v1/conversations/` - List user conversations with latest message & unread counts.
- `POST /api/v1/conversations/` - Start or get existing conversation with a user.
- `GET /api/v1/conversations/{id}/` - Retrieve conversation details.
- `GET /api/v1/conversations/{id}/messages/` - Retrieve conversation message history.
- `POST /api/v1/conversations/{id}/messages/` - Send a new text or image message.
- `POST /api/v1/conversations/{id}/read/` - Mark all incoming messages in conversation as read.
- `GET /api/v1/conversations/unread-count/` - Quick unread message counter for navigation badges.
- `GET /api/v1/notifications/` - List user notifications (supports `?unread=true`).
- `PATCH /api/v1/notifications/{id}/` - Mark individual notification as read.
- `POST /api/v1/notifications/read-all/` - Mark all notifications as read.
- `GET /api/v1/notifications/unread-count/` - Quick unread notification counter.

### 4. Server-Rendered Web Pages & UI
- **Messages Inbox** (`/messages/`):
  - Shows all conversation threads, recipient avatar, latest message snippet, timestamp, and unread badge.
- **Live Conversation Room** (`/messages/<id>/`):
  - Responsive chat interface with live WebSocket messaging.
  - Message bubble styles for sent vs. received.
  - Image attachments preview and upload.
  - Real-time typing indicators and double-check read receipts.
  - "Message" button directly accessible on user profiles (`/@username/`).
- **Notifications Center** (`/notifications/`):
  - Notification items with actor avatar, action description, direct link to post/profile, timestamp, and unread dot.
  - Filter tabs ("All" and "Unread").
  - "Mark all as read" button.
  - Live WebSocket listener that prepends new notifications in real-time.

1. Start your local server:
   ```bash
   python backend/manage.py runserver 0.0.0.0:8000
   ```
2. **Open the Feed:** Visit [http://localhost:8000/](http://localhost:8000/).
3. **Create a Post:**
   - Click the **"+ Create"** tab in the sidebar or go to [http://localhost:8000/posts/create/](http://localhost:8000/posts/create/).
   - Select one or multiple photos/videos.
   - Enter a caption (e.g. `Exploring the city #architecture #weekend`).
   - Click **Share Post**.
4. **Interact with the Post:**
   - Click the heart icon to like/unlike (watch the count update).
   - Enter a comment in the inline input and press Post.
   - Click on the post to open the full detail split view at [http://localhost:8000/posts/1/](http://localhost:8000/posts/1/).
   - Click **Reply** on a comment to create a nested reply.
5. **View Profile Grid:**
   - Visit [http://localhost:8000/profile/](http://localhost:8000/profile/) to view your 3-column square post grid with hover overlay stats.
6. **Interactive API Documentation:**
   - Test the new post, feed, and comment endpoints in Swagger UI at [http://localhost:8000/api/v1/docs/](http://localhost:8000/api/v1/docs/).
