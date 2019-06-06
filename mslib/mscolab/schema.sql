# -*- coding: utf-8 -*-
/*
"""

    mslib.mscolab.schema
    ~~~~~~~~~~~~~~~~~~~~

    Preliminary schema of mscolab database.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2019 by the mss team, see AUTHORS.
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
CREATE TABLE `users` (
  `username` varchar(255) DEFAULT NULL,
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
