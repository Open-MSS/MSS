CREATE TABLE `users` (
  `screenname` varchar(255) DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(255) DEFAULT NULL,
  `emailid` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `connections` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `u_id` int(11) DEFAULT NULL,
  `s_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY(u_id) REFERENCES users(id)
);

CREATE TABLE `projects` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `path` varchar(255) DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `u_id` int(11) DEFAULT NULL,
  `p_id` int(11) DEFAULT NULL,
  `access_level` ENUM ('value1','value2','value3'),
  PRIMARY KEY (`id`),
  FOREIGN KEY(u_id) REFERENCES users(id),
  FOREIGN KEY(p_id) REFERENCES projects(id)
);

CREATE TABLE `messages` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `u_id` int(11) DEFAULT NULL,
  `p_id` int(11) DEFAULT NULL,
  `text` BLOB NOT NULL,
  `created_at` timestamp default current_timestamp, 
  PRIMARY KEY (`id`),
  FOREIGN KEY(u_id) REFERENCES users(id),
  FOREIGN KEY(p_id) REFERENCES projects(id)
);


CREATE TABLE `changes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `u_id` int(11) DEFAULT NULL,
  `p_id` int(11) DEFAULT NULL,
  `content` BLOB NOT NULL,
  `created_at` timestamp default current_timestamp, 
  PRIMARY KEY (`id`),
  FOREIGN KEY(u_id) REFERENCES users(id),
  FOREIGN KEY(p_id) REFERENCES projects(id)
);
