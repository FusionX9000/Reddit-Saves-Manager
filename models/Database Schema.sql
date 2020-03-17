CREATE TABLE users
(
    id BIGSERIAL NOT NULL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    created_utc TIMESTAMP DEFAULT timezone('utc',now())
);

CREATE TABLE saves
(
    id BIGSERIAL NOT NULL PRIMARY KEY,
    name_id VARCHAR(10) NOT NULL,
    kind VARCHAR(10) NOT NULL,
    link_title TEXT NOT NULL,
    link_permalink TEXT NOT NULL,
    author VARCHAR(50) NOT NULL,
    subreddit VARCHAR(50) NOT NULL,
    score_hidden BOOLEAN NOT NULL,
    score INTEGER NOT NULL,
    created_utc TIMESTAMP NOT NULL,
    over_18 BOOLEAN NOT NULL,
    UNIQUE(kind,name_id)
);

CREATE TABLE user_saves
(
    id BIGSERIAL NOT NULL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    save_id BIGINT NOT NULL REFERENCES saves(id),
    saved BOOLEAN NOT NULL,
    UNIQUE(user_id,save_id)
);


CREATE TABLE links
(
    id BIGSERIAL NOT NULL PRIMARY KEY,
    link_id VARCHAR(10) UNIQUE NOT NULL,
    domain VARCHAR(50) NOT NULL,
    link_url TEXT NOT NULL,
    is_self BOOLEAN NOT NULL,
    selftext TEXT,
    selftext_html TEXT,
    num_comments INT NOT NULL,
    is_video BOOLEAN NOT NULL,
    post_hint VARCHAR(20),
    thumbnail VARCHAR(500),
    media JSON,
    media_embed JSON,
    preview JSON,
    save_id BIGINT references saves(id) NOT NULL,
    UNIQUE(save_id),
    UNIQUE(link_id)
);

CREATE TABLE comments
(
    id BIGSERIAL NOT NULL PRIMARY KEY,
    comment_id VARCHAR(10) UNIQUE NOT NULL,
    link_id VARCHAR(10) NOT NULL,
    body_html TEXT NOT NULL,
    save_id BIGINT references saves(id) NOT NULL,
    UNIQUE(save_id),
    UNIQUE(comment_id)
);

CREATE TABLE tags
(
    id SERIAL NOT NULL PRIMARY KEY,
    tag_name VARCHAR(50)
);

CREATE TABLE save_tags
(
    id SERIAL NOT NULL PRIMARY KEY,
    tag_id INT references tags(id),
    user_save_id BIGINT references user_saves(id),
    UNIQUE(tag_id,user_save_id)
);


create view links_view
as
    (SELECT user_saves.id as user_save_id, user_saves.user_id, saves.id as save_id, saves.name_id, links.link_id, saves.kind, saves.link_title, saves.link_permalink, saves.author, saves.subreddit, saves.score_hidden, saves.score, saves.over_18, links.domain, links.link_url, links.is_self, links.selftext, links.selftext_html, links.num_comments, links.is_video, links.post_hint, links.thumbnail, links.media, links.media_embed, links.preview, saves.created_utc
    FROM user_saves
        INNER JOIN saves
        ON user_saves.save_id = saves.id
        INNER JOIN links
        ON saves.id = links.save_id);

create view comments_view
as
    (SELECT user_saves.id as user_save_id, user_saves.user_id, saves.id as save_id, saves.name_id, comments.link_id, saves.kind, saves.link_title, saves.link_permalink, saves.author, saves.subreddit, saves.score_hidden, saves.score, saves.over_18, comments.body_html, saves.created_utc
    FROM user_saves
        INNER JOIN saves
        ON user_saves.save_id = saves.id
        INNER JOIN comments
        ON saves.id = links.save_id);

create view save_tags_view
as
    select save_tags.user_save_id, array_agg(tags.tag_name)
    FROM save_tags INNER JOIN tags ON save_tags.tag_id=tags.id
    group by save_tags.user_save_id;