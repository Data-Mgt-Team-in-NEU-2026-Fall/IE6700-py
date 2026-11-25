-- ============================================================
CREATE DATABASE IF NOT EXISTS secondhand_marketplace
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE secondhand_marketplace;

-- ---------- Diagram 1: User identity ----------
CREATE TABLE Campus (
  campusId   BIGINT NOT NULL AUTO_INCREMENT,
  campusName VARCHAR(100) NOT NULL,
  address    VARCHAR(200),
  city       VARCHAR(100),
  state      VARCHAR(50),
  zipCode    VARCHAR(20),
  longitude  DOUBLE,
  latitude   DOUBLE,
  PRIMARY KEY (campusId),
  CHECK (latitude BETWEEN -90 AND 90),
  CHECK (longitude BETWEEN -180 AND 180)
) ENGINE=InnoDB;

CREATE TABLE UserRole (
  roleId   BIGINT NOT NULL AUTO_INCREMENT,
  roleName VARCHAR(50) NOT NULL,
  PRIMARY KEY (roleId),
  UNIQUE KEY uq_roleName (roleName)
) ENGINE=InnoDB;

CREATE TABLE `User` (
  userId        BIGINT NOT NULL AUTO_INCREMENT,
  firstName     VARCHAR(50),
  lastName      VARCHAR(50),
  email         VARCHAR(100) NOT NULL,
  phone         VARCHAR(30),
  birthDate     DATE,
  dateJoined    DATETIME,
  campusId      BIGINT NOT NULL,
  primaryRoleId BIGINT NOT NULL,
  PRIMARY KEY (userId),
  UNIQUE KEY uq_email (email),
  FOREIGN KEY (campusId) REFERENCES Campus (campusId),
  FOREIGN KEY (primaryRoleId) REFERENCES UserRole (roleId)
) ENGINE=InnoDB;

CREATE TABLE UserHasRole (
  userId BIGINT NOT NULL,
  roleId BIGINT NOT NULL,
  PRIMARY KEY (userId, roleId),
  FOREIGN KEY (userId) REFERENCES `User` (userId),
  FOREIGN KEY (roleId) REFERENCES UserRole (roleId)
) ENGINE=InnoDB;

-- ---------- Diagram 3: Messaging ----------
CREATE TABLE Conversation (
  conversationId BIGINT NOT NULL AUTO_INCREMENT,
  createdAt      DATETIME,
  itemId         BIGINT NOT NULL COMMENT 'FK to SecondhandItem(itemId) in Diagram 2',
  creatorId      BIGINT NOT NULL,
  PRIMARY KEY (conversationId),
  FOREIGN KEY (creatorId) REFERENCES `User` (userId)
) ENGINE=InnoDB;

CREATE TABLE ConversationParticipant (
  conversationId BIGINT NOT NULL,
  userId         BIGINT NOT NULL,
  PRIMARY KEY (conversationId, userId),
  FOREIGN KEY (conversationId) REFERENCES Conversation (conversationId),
  FOREIGN KEY (userId) REFERENCES `User` (userId)
) ENGINE=InnoDB;

CREATE TABLE Message (
  messageId      BIGINT NOT NULL AUTO_INCREMENT,
  content        TEXT,
  sentAt         DATETIME,
  conversationId BIGINT NOT NULL,
  authorId       BIGINT NOT NULL,
  PRIMARY KEY (messageId),
  FOREIGN KEY (conversationId) REFERENCES Conversation (conversationId),
  FOREIGN KEY (authorId) REFERENCES `User` (userId)
) ENGINE=InnoDB;

-- ---------- Diagram 4: Reviews and reports ----------
CREATE TABLE TransactionReview (
  reviewId      BIGINT NOT NULL AUTO_INCREMENT,
  reviewDate    DATETIME,
  rating        INT,
  comment       TEXT,
  reviewStatus  VARCHAR(30),
  authorId      BIGINT NOT NULL,
  recipientId   BIGINT NOT NULL,
  PRIMARY KEY (reviewId),
  CHECK (rating BETWEEN 1 AND 5),
  CHECK (authorId <> recipientId),
  FOREIGN KEY (authorId) REFERENCES `User` (userId),
  FOREIGN KEY (recipientId) REFERENCES `User` (userId)
) ENGINE=InnoDB;

CREATE TABLE BuyerReview (
  reviewId      BIGINT NOT NULL,
  transactionId BIGINT NOT NULL COMMENT 'FK to TransactionOrder(transactionId) in Diagram 2',
  PRIMARY KEY (reviewId),
  UNIQUE KEY uq_buyer_transaction (transactionId),
  FOREIGN KEY (reviewId) REFERENCES TransactionReview (reviewId)
) ENGINE=InnoDB;

CREATE TABLE SellerReview (
  reviewId      BIGINT NOT NULL,
  transactionId BIGINT NOT NULL COMMENT 'FK to TransactionOrder(transactionId) in Diagram 2',
  PRIMARY KEY (reviewId),
  UNIQUE KEY uq_seller_transaction (transactionId),
  FOREIGN KEY (reviewId) REFERENCES TransactionReview (reviewId)
) ENGINE=InnoDB;

CREATE TABLE Report (
  reportId    BIGINT NOT NULL AUTO_INCREMENT,
  reason      VARCHAR(200),
  description TEXT,
  reportDate  DATETIME,
  status      VARCHAR(30),
  reporterId  BIGINT NOT NULL,
  PRIMARY KEY (reportId),
  FOREIGN KEY (reporterId) REFERENCES `User` (userId)
) ENGINE=InnoDB;

CREATE TABLE ItemReport (
  reportId BIGINT NOT NULL,
  itemId   BIGINT NOT NULL COMMENT 'FK to SecondhandItem(itemId) in Diagram 2',
  PRIMARY KEY (reportId),
  FOREIGN KEY (reportId) REFERENCES Report (reportId)
) ENGINE=InnoDB;

CREATE TABLE TransactionReport (
  reportId      BIGINT NOT NULL,
  transactionId BIGINT NOT NULL COMMENT 'FK to TransactionOrder(transactionId) in Diagram 2',
  PRIMARY KEY (reportId),
  FOREIGN KEY (reportId) REFERENCES Report (reportId)
) ENGINE=InnoDB;
