-- 云墨江湖 数据库结构与初始化脚本
-- 说明：本文件不使用行内 -- 注释，避免 init_db.py 按分号切分时出错
-- 执行方式：python init_db.py
-- 注意：全部使用 IF NOT EXISTS，脚本可重复执行；如需重建表结构请先手动 DROP

CREATE DATABASE IF NOT EXISTS `yunmo` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE `yunmo`;

-- 用户表：支撑登录、注册与个人主页
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` VARCHAR(50) NOT NULL COMMENT '登录账号',
  `password` VARCHAR(512) NOT NULL COMMENT '密码（werkzeug 哈希值）',
  `email` VARCHAR(100) NOT NULL COMMENT '邮箱',
  `nickname` VARCHAR(50) NOT NULL DEFAULT '' COMMENT '昵称',
  `avatar` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '头像地址',
  `followers_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '粉丝数',
  `likes_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '获赞数',
  `following_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '关注数',
  `role` TINYINT NOT NULL DEFAULT 0 COMMENT '身份：0-普通用户 1-管理员',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1-正常 0-禁用',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 帖子表：支撑发帖
CREATE TABLE IF NOT EXISTS `posts` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '帖子ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '作者ID',
  `title` VARCHAR(200) NOT NULL DEFAULT '' COMMENT '标题',
  `content` TEXT COMMENT '正文',
  `cover` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '封面图',
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