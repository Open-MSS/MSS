# -*- coding: utf-8 -*-
/*
"""

    mslib.mscolab.schema
    ~~~~~~~~~~~~~~~~~~~~

    Preliminary schema of mscolab database.

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

*/

# description of the schemas in models.py

CREATE TABLE `users` (`username` varchar(255) DEFAULT NULL,`id` int(11) NOT NULL AUTO_INCREMENT,`password` varchar(255) DEFAULT NULL,`emailid` varchar(255) DEFAULT NULL,PRIMARY KEY (`id`));

CREATE TABLE `connections` (`id` int(11) NOT NULL AUTO_INCREMENT,`u_id` int(11) DEFAULT NULL,`s_id` varchar(255) DEFAULT NULL,PRIMARY KEY (`id`),FOREIGN KEY(u_id) REFERENCES users(id));

CREATE TABLE `projects` (`id` int(11) NOT NULL AUTO_INCREMENT,`path` varchar(255) DEFAULT NULL,`description` varchar(255) DEFAULT NULL,PRIMARY KEY (`id`));

CREATE TABLE `permissions` (`id` int(11) NOT NULL AUTO_INCREMENT,`u_id` int(11) DEFAULT NULL,`p_id` int(11) DEFAULT NULL,`access_level` ENUM ('admin','collaborator','viewer'),PRIMARY KEY (`id`),FOREIGN KEY(u_id) REFERENCES users(id),FOREIGN KEY(p_id) REFERENCES projects(id));

CREATE TABLE `messages` (`id` int(11) NOT NULL AUTO_INCREMENT,`u_id` int(11) DEFAULT NULL,`p_id` int(11) DEFAULT NULL,`text` BLOB NOT NULL,`created_at` timestamp default current_timestamp, PRIMARY KEY (`id`),FOREIGN KEY(u_id) REFERENCES users(id),FOREIGN KEY(p_id) REFERENCES projects(id));


CREATE TABLE `changes` (`id` int(11) NOT NULL AUTO_INCREMENT,`u_id` int(11) DEFAULT NULL,`p_id` int(11) DEFAULT NULL,`content` BLOB NOT NULL,`comment` varchar(255) DEFAULT "",`created_at` timestamp default current_timestamp, PRIMARY KEY (`id`),FOREIGN KEY(u_id) REFERENCES users(id),FOREIGN KEY(p_id) REFERENCES projects(id));



SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';




INSERT INTO `permissions` (`id`, `u_id`, `p_id`, `access_level`) VALUES (1, 8,  1,  'creator'),(2, 9,  1,  'collaborator'),(3, 9,  2,  'creator'),(4, 10, 2,  'collaborator'),(5, 10, 3,  'creator'),(6, 8,  3,  'collaborator'),(7, 10, 1,  'viewer');

INSERT INTO `projects` (`id`, `path`, `description`) VALUES (1, 'one',  'a, b'),(2, 'two',  'b, c'),(3, 'three',  'a, c');

INSERT INTO `users` (`username`, `id`, `password`, `emailid`) VALUES ('a', 8,  '$6$rounds=656000$cPQdxVHb1tlkDNil$Ohb.ZDN350IBuoVozgTg3cmdMKRaBQCJ1KvHPjKyGhnygd.T6x6cyYVddWp/Hc9JFjT5cY9JNw75eTsG0kDt11', 'a'),('b', 9,  '$6$rounds=656000$DqUls/5/BfWuTReI$dJvxnZrsgeo.sKyIYBGn3ShJ.Ccm98Q6gWcETruuWIgBWxL7RtRwmUAQ0I6b2cGITR5ksTDN2KK8xPJEm4v6c1', 'b'),('c', 10, '$6$rounds=656000$z5PgqRSetyiQh4FE$a/1R6JSPieTp32u4xnPY3OBremIQaHcBlmDeFqJ20WyDrd9f.EP.i4yIB/nykv9hmKfGakLJcCaGJ/mb.2uDe1', 'c');

-- 2019-06-10 08:00:36

