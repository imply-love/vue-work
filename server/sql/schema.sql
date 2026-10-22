-- 云墨江湖 数据库结构与初始化脚本
-- 说明：本文件不使用行内 -- 注释，避免 init_db.py 按分号切分时出错
-- 执行方式：python init_db.py
-- 注意：全部使用 IF NOT EXISTS，脚本可重复执行；如需重建表结构请先手动 DROP
-- 存量库升级（IF NOT EXISTS 不会给已存在的表补列，需手动执行一次）：
--     ALTER TABLE `users`
--       ADD COLUMN `phone` VARCHAR(20) NULL DEFAULT NULL COMMENT '手机号（非强制绑定，未绑定为 NULL）' AFTER `avatar`,
--       ADD UNIQUE KEY `uk_phone` (`phone`);
-- 存量库新增表（favorites / login_logs）：IF NOT EXISTS 建表对已存在的表无效，需手动执行一次：
--     CREATE TABLE IF NOT EXISTS `favorites` (
--       `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
--       `user_id` INT UNSIGNED NOT NULL,
--       `post_id` INT UNSIGNED NOT NULL,
--       `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
--       PRIMARY KEY (`id`),
--       UNIQUE KEY `uk_user_post` (`user_id`, `post_id`),
--       KEY `idx_post_id` (`post_id`),
--       CONSTRAINT `fk_favorites_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
--       CONSTRAINT `fk_favorites_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE
--     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收藏表';
--     CREATE TABLE IF NOT EXISTS `login_logs` (
--       `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
--       `user_id` INT UNSIGNED NOT NULL,
--       `ip` VARCHAR(45) NOT NULL DEFAULT '',
--       `device` VARCHAR(100) NOT NULL DEFAULT '',
--       `user_agent` VARCHAR(255) NOT NULL DEFAULT '',
--       `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
--       PRIMARY KEY (`id`),
--       KEY `idx_user_id` (`user_id`),
--       KEY `idx_create_time` (`create_time`),
--       CONSTRAINT `fk_login_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
--     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='登录记录表';
-- 存量库新增点赞表（post_likes）：IF NOT EXISTS 建表对已存在的表无效，需手动执行一次：
--     CREATE TABLE IF NOT EXISTS `post_likes` (
--       `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
--       `user_id` INT UNSIGNED NOT NULL,
--       `post_id` INT UNSIGNED NOT NULL,
--       `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
--       PRIMARY KEY (`id`),
--       UNIQUE KEY `uk_user_post` (`user_id`, `post_id`),
--       KEY `idx_post_id` (`post_id`),
--       CONSTRAINT `fk_post_likes_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
--       CONSTRAINT `fk_post_likes_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE
--     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帖子点赞表';

CREATE DATABASE IF NOT EXISTS `yunmo` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE `yunmo`;

-- 用户表：支撑登录、注册与个人主页
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` VARCHAR(50) NOT NULL COMMENT '登录账号',
  `password` VARCHAR(512) NOT NULL COMMENT '密码（werkzeug 哈希值）',
  `email` VARCHAR(100) NOT NULL COMMENT '邮箱（注册时强制验证后绑定）',
  `nickname` VARCHAR(50) NOT NULL DEFAULT '' COMMENT '昵称',
  `avatar` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '头像地址',
  `phone` VARCHAR(20) NULL DEFAULT NULL COMMENT '手机号（非强制绑定，未绑定为 NULL）',
  `followers_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '粉丝数',
  `likes_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '获赞数',
  `following_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '关注数',
  `role` TINYINT NOT NULL DEFAULT 0 COMMENT '身份：0-普通用户 1-管理员',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1-正常 0-禁用',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`),
  UNIQUE KEY `uk_phone` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 邮箱验证码表：注册与换绑邮箱共用（scene 区分场景，避免两个场景的码互相顶用）
CREATE TABLE IF NOT EXISTS `email_codes` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `email` VARCHAR(100) NOT NULL COMMENT '接收邮箱',
  `code` VARCHAR(10) NOT NULL COMMENT '验证码',
  `scene` VARCHAR(20) NOT NULL DEFAULT 'register' COMMENT '场景：register-注册 bind_email-换绑邮箱',
  `expire_time` DATETIME NOT NULL COMMENT '过期时间',
  `used` TINYINT NOT NULL DEFAULT 0 COMMENT '是否已使用：1-是 0-否',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_email_scene` (`email`, `scene`),
  KEY `idx_expire_time` (`expire_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='邮箱验证码表';

-- 帖子表：支撑发帖
-- 存量库升级（IF NOT EXISTS 不会给已存在的表补列，需手动执行一次）：
--     ALTER TABLE `posts`
--       ADD COLUMN `tags` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '标签（逗号分隔）' AFTER `cover`,
--       ADD COLUMN `summary` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '摘要' AFTER `tags`,
--       ADD COLUMN `category` VARCHAR(30) NOT NULL DEFAULT '' COMMENT '分类' AFTER `summary`;
CREATE TABLE IF NOT EXISTS `posts` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '帖子ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '作者ID',
  `title` VARCHAR(200) NOT NULL DEFAULT '' COMMENT '标题',
  `content` TEXT COMMENT '正文',
  `cover` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '封面图',
  `tags` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '标签（逗号分隔）',
  `summary` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '摘要',
  `category` VARCHAR(30) NOT NULL DEFAULT '' COMMENT '分类',
  `view_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '浏览数',
  `like_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '点赞数',
  `reply_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '回帖数',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1-已发布 0-草稿',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_create_time` (`create_time`),
  CONSTRAINT `fk_posts_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帖子表';

-- 回帖表：支撑回帖与楼中楼（parent_id 为 0 表示直接回帖）
CREATE TABLE IF NOT EXISTS `replies` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '回复ID',
  `post_id` INT UNSIGNED NOT NULL COMMENT '所属帖子ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '回复人ID',
  `parent_id` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '父回复ID，0 表示直接回帖',
  `content` TEXT NOT NULL COMMENT '回复内容',
  `like_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '点赞数',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1-正常 0-隐藏',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_post_id` (`post_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_parent_id` (`parent_id`),
  CONSTRAINT `fk_replies_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_replies_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='回帖表';

-- 求番表：支撑番剧库的求番功能（管理员与普通用户均可发起）
CREATE TABLE IF NOT EXISTS `anime_requests` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '求番ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '发起人ID',
  `anime_name` VARCHAR(100) NOT NULL COMMENT '求番名称',
  `reason` TEXT COMMENT '求番理由/补充说明',
  `status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0-待收录 1-已收录',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_create_time` (`create_time`),
  CONSTRAINT `fk_anime_requests_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='求番表';

-- 资源表：支撑资源分享板块的分享资源功能（管理员与普通用户均可分享）
CREATE TABLE IF NOT EXISTS `resources` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '资源ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '分享人ID',
  `title` VARCHAR(200) NOT NULL COMMENT '资源标题',
  `description` TEXT COMMENT '资源描述',
  `link` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '资源链接',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_create_time` (`create_time`),
  CONSTRAINT `fk_resources_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资源表';

-- 收藏表：支撑个人中心「我的收藏」（收藏已发布的帖子）
CREATE TABLE IF NOT EXISTS `favorites` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '收藏ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '收藏人ID',
  `post_id` INT UNSIGNED NOT NULL COMMENT '被收藏的帖子ID',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_post` (`user_id`, `post_id`),
  KEY `idx_post_id` (`post_id`),
  CONSTRAINT `fk_favorites_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_favorites_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收藏表';

-- 登录记录表：支撑个人中心「登录记录」（每次登录成功写一条）
CREATE TABLE IF NOT EXISTS `login_logs` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `ip` VARCHAR(45) NOT NULL DEFAULT '' COMMENT '登录 IP（兼容 IPv6）',
  `device` VARCHAR(100) NOT NULL DEFAULT '' COMMENT '设备/浏览器摘要',
  `user_agent` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '完整 User-Agent',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_create_time` (`create_time`),
  CONSTRAINT `fk_login_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='登录记录表';

-- 点赞表：支撑帖子详情的点赞功能（一篇帖子一人一次点赞，可取消）
CREATE TABLE IF NOT EXISTS `post_likes` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '点赞ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '点赞人ID',
  `post_id` INT UNSIGNED NOT NULL COMMENT '被点赞的帖子ID',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '点赞时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_post` (`user_id`, `post_id`),
  KEY `idx_post_id` (`post_id`),
  CONSTRAINT `fk_post_likes_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_post_likes_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帖子点赞表';

-- 关注表：用户之间的关注关系（关注人 → 被关注人）
CREATE TABLE IF NOT EXISTS `follows` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '关注ID',
  `follower_id` INT UNSIGNED NOT NULL COMMENT '关注人ID（粉丝）',
  `followee_id` INT UNSIGNED NOT NULL COMMENT '被关注人ID（博主）',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '关注时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_follower_followee` (`follower_id`, `followee_id`),
  KEY `idx_followee_id` (`followee_id`),
  CONSTRAINT `fk_follows_follower` FOREIGN KEY (`follower_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_follows_followee` FOREIGN KEY (`followee_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='关注表';

-- 收藏表：支撑个人中心的「我的收藏」功能（收藏已发布的帖子）
CREATE TABLE IF NOT EXISTS `favorites` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '收藏ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '收藏人ID',
  `post_id` INT UNSIGNED NOT NULL COMMENT '被收藏的帖子ID',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_post` (`user_id`, `post_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_post_id` (`post_id`),
  CONSTRAINT `fk_favorites_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_favorites_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收藏表';

-- 登录记录表：支撑个人中心的「登录记录」功能
CREATE TABLE IF NOT EXISTS `login_logs` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '登录用户ID',
  `ip` VARCHAR(45) NOT NULL DEFAULT '' COMMENT '登录IP',
  `device` VARCHAR(100) NOT NULL DEFAULT '' COMMENT '设备/浏览器摘要',
  `user_agent` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '完整 UA（前255字符）',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_create_time` (`create_time`),
  CONSTRAINT `fk_login_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='登录记录表';