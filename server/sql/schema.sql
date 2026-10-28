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
-- 存量库新增评论审查列 + 公告表：IF NOT EXISTS 建表对已存在的表无效，需手动执行一次：
--     ALTER TABLE `replies`
--       ADD COLUMN `review_status` TINYINT NOT NULL DEFAULT 0 COMMENT '审查状态：0-正常 1-推荐 2-打回 3-封禁 4-待审核' AFTER `status`,
--       ADD COLUMN `review_note` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '审查备注（打回/封禁理由）' AFTER `review_status`;
--     CREATE TABLE IF NOT EXISTS `announcements` (
--       `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '公告ID',
--       `title` VARCHAR(100) NOT NULL COMMENT '公告标题',
--       `content` TEXT NOT NULL COMMENT '公告内容',
--       `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1-发布中 0-已下架',
--       `admin_id` INT UNSIGNED NOT NULL COMMENT '发布管理员ID',
--       `publish_time` DATETIME NULL DEFAULT NULL COMMENT '发布时间（下架不清空）',
--       `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
--       `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
--       PRIMARY KEY (`id`),
--       KEY `idx_status_time` (`status`, `publish_time`),
--       CONSTRAINT `fk_announcements_admin` FOREIGN KEY (`admin_id`) REFERENCES `users` (`id`)
--     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公告表';

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
  `identity` VARCHAR(20) NOT NULL DEFAULT '' COMMENT '特殊身份：anime_master-番剧大佬 resource_master-我就是资源',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1-正常 0-禁用 2-封禁（可登录、禁发言、可申诉）',
  `ban_reason` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '封禁理由',
  `ban_time` DATETIME NULL DEFAULT NULL COMMENT '封禁时间',
  `ban_admin_id` INT UNSIGNED NULL DEFAULT NULL COMMENT '封禁操作的管理员ID',
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
  `visibility` TINYINT NOT NULL DEFAULT 0 COMMENT '可见性：0-公开 1-私密 2-仅好友',
  `review_status` TINYINT NOT NULL DEFAULT 0 COMMENT '审查状态：0-正常 1-推荐 2-打回 3-封禁',
  `review_note` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '审查备注（打回/封禁理由）',
  `edit_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '已修改次数：0-未修改 1-二编 2-三编',
  `publish_time` DATETIME NULL DEFAULT NULL COMMENT '发布时间（修改后更新为修改时间）',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1-已发布 0-草稿',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_create_time` (`create_time`),
  KEY `idx_publish_time` (`publish_time`),
  KEY `idx_visibility_review` (`visibility`, `review_status`),
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
  `review_status` TINYINT NOT NULL DEFAULT 0 COMMENT '审查状态：0-正常 1-推荐 2-打回 3-封禁 4-待审核',
  `review_note` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '审查备注（打回/封禁理由）',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_post_id` (`post_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_parent_id` (`parent_id`),
  KEY `idx_review_status` (`review_status`),
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
  `review_status` TINYINT NOT NULL DEFAULT 0 COMMENT '评审结果：0-未评审 1-推荐 2-打回 3-封禁',
  `review_note` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '评审理由',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_review_status` (`review_status`),
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
  `visibility` TINYINT NOT NULL DEFAULT 0 COMMENT '查看条件：0-所有同好 1-仅管理员与特殊身份 2-仅自己',
  `review_status` TINYINT NOT NULL DEFAULT 0 COMMENT '评审结果：0-未评审 1-推荐 2-打回 3-封禁',
  `review_note` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '评审理由',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_create_time` (`create_time`),
  KEY `idx_review_status` (`review_status`),
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

-- 好友申请表：A 向 B 发起申请，B 同意后写入 friends 双向关系
CREATE TABLE IF NOT EXISTS `friend_requests` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '申请ID',
  `from_user_id` INT UNSIGNED NOT NULL COMMENT '申请人ID',
  `to_user_id` INT UNSIGNED NOT NULL COMMENT '被申请人ID',
  `message` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '申请留言',
  `status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0-待处理 1-已同意 2-已拒绝',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
  `handle_time` DATETIME NULL DEFAULT NULL COMMENT '处理时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_from_to` (`from_user_id`, `to_user_id`),
  KEY `idx_to_status` (`to_user_id`, `status`),
  CONSTRAINT `fk_friend_requests_from` FOREIGN KEY (`from_user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_friend_requests_to` FOREIGN KEY (`to_user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='好友申请表';

-- 好友表：双向写入两行，便于按 user_id 直接查好友列表
CREATE TABLE IF NOT EXISTS `friends` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '关系ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `friend_id` INT UNSIGNED NOT NULL COMMENT '好友ID',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '成为好友时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_friend` (`user_id`, `friend_id`),
  KEY `idx_friend_id` (`friend_id`),
  CONSTRAINT `fk_friends_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_friends_friend` FOREIGN KEY (`friend_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='好友表';

-- 账号申诉表：被封禁用户提交申诉，管理员审核
CREATE TABLE IF NOT EXISTS `appeals` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '申诉ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '申诉用户ID',
  `reason` TEXT NOT NULL COMMENT '申诉理由',
  `status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0-待处理 1-申诉通过 2-申诉驳回',
  `admin_note` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '管理员处理备注',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
  `handle_time` DATETIME NULL DEFAULT NULL COMMENT '处理时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_status` (`user_id`, `status`),
  KEY `idx_status_time` (`status`, `create_time`),
  CONSTRAINT `fk_appeals_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='账号申诉表';

-- 帖子审查日志表：记录管理员对帖子的封禁/打回/推荐操作，便于追溯
CREATE TABLE IF NOT EXISTS `post_review_logs` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `post_id` INT UNSIGNED NOT NULL COMMENT '帖子ID',
  `admin_id` INT UNSIGNED NOT NULL COMMENT '操作管理员ID',
  `action` VARCHAR(20) NOT NULL COMMENT '操作：ban-封禁 reject-打回 recommend-推荐 restore-恢复',
  `reason` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '操作理由',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  PRIMARY KEY (`id`),
  KEY `idx_post_id` (`post_id`),
  KEY `idx_create_time` (`create_time`),
  CONSTRAINT `fk_review_logs_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帖子审查日志表';

-- 番剧库内容表：管理员录入的番剧条目
CREATE TABLE IF NOT EXISTS `animes` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '番剧ID',
  `title` VARCHAR(200) NOT NULL COMMENT '番名',
  `category` VARCHAR(30) NOT NULL DEFAULT '' COMMENT '分类',
  `cover` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '封面',
  `description` TEXT COMMENT '简介',
  `link` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '相关链接',
  `admin_id` INT UNSIGNED NOT NULL COMMENT '录入管理员ID',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_title` (`title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='番剧库内容表';

-- 番剧推荐表：用户推荐番剧，需填写番名、链接与推荐理由
CREATE TABLE IF NOT EXISTS `anime_recommendations` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '推荐ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '推荐人ID',
  `anime_name` VARCHAR(100) NOT NULL COMMENT '番名',
  `link` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '番剧链接',
  `reason` TEXT COMMENT '推荐理由',
  `review_status` TINYINT NOT NULL DEFAULT 0 COMMENT '评审结果：0-未评审 1-推荐 2-打回 3-封禁',
  `review_note` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '评审理由',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_review_status` (`review_status`),
  CONSTRAINT `fk_anime_recommendations_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='番剧推荐表';

-- 身份申请表：番剧大佬 / 我就是资源 的申请与审批
CREATE TABLE IF NOT EXISTS `identity_applications` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '申请ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '申请人ID',
  `identity_type` VARCHAR(20) NOT NULL COMMENT 'anime_master-番剧大佬 resource_master-我就是资源',
  `reason` TEXT COMMENT '申请说明',
  `status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0-待处理 1-已通过 2-已驳回',
  `admin_note` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '审批备注',
  `handle_admin_id` INT UNSIGNED NULL DEFAULT NULL COMMENT '审批管理员ID',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
  `handle_time` DATETIME NULL DEFAULT NULL COMMENT '处理时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  CONSTRAINT `fk_identity_applications_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='身份申请表';

-- 站内通知表：求番提醒管理员、身份申请结果等
CREATE TABLE IF NOT EXISTS `notifications` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '通知ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '接收人ID',
  `type` VARCHAR(20) NOT NULL DEFAULT 'system' COMMENT '类型：anime_request-求番 identity-身份申请 system-系统',
  `title` VARCHAR(100) NOT NULL DEFAULT '' COMMENT '标题',
  `content` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '内容',
  `link` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '跳转地址',
  `is_read` TINYINT NOT NULL DEFAULT 0 COMMENT '1-已读 0-未读',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_read` (`user_id`, `is_read`),
  CONSTRAINT `fk_notifications_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='站内通知表';

-- 公告表：支撑后台公告管理与前台公告展示（管理员发布，前台公开展示发布中的公告）
CREATE TABLE IF NOT EXISTS `announcements` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '公告ID',
  `title` VARCHAR(100) NOT NULL COMMENT '公告标题',
  `content` TEXT NOT NULL COMMENT '公告内容',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1-发布中 0-已下架',
  `admin_id` INT UNSIGNED NOT NULL COMMENT '发布管理员ID',
  `publish_time` DATETIME NULL DEFAULT NULL COMMENT '发布时间（下架不清空）',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_status_time` (`status`, `publish_time`),
  CONSTRAINT `fk_announcements_admin` FOREIGN KEY (`admin_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公告表';