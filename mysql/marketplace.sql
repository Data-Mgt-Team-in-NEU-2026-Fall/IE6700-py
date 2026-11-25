-- Seattle Campus Secondhand Marketplace schema

CREATE DATABASE IF NOT EXISTS seattle_marketplace
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE seattle_marketplace;

-- ---------- 1 User identity ----------
CREATE TABLE Campus (
  campusId    INT UNSIGNED NOT NULL AUTO_INCREMENT,
  campusName  VARCHAR(80) NOT NULL,
  emailDomain VARCHAR(255) NOT NULL,
  address     VARCHAR(100),
  city        VARCHAR(50),
  state       CHAR(2),
  zipCode     VARCHAR(10),
  longitude   DECIMAL(9,6),
  latitude    DECIMAL(8,6),
  PRIMARY KEY (campusId),
  CHECK (longitude BETWEEN -180 AND 180),
  CHECK (latitude BETWEEN -90 AND 90)
) ENGINE=InnoDB;

CREATE TABLE `Role` (
  roleId   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  roleName VARCHAR(30) NOT NULL,
  PRIMARY KEY (roleId),
  UNIQUE KEY uq_roleName (roleName)
) ENGINE=InnoDB;

CREATE TABLE `User` (
  userId        INT UNSIGNED NOT NULL AUTO_INCREMENT,
  firstName     VARCHAR(50),
  lastName      VARCHAR(50),
  email         VARCHAR(255) NOT NULL,
  phone         VARCHAR(20),
  birthDate     DATE,
  dateJoined    DATE,
  accountStatus ENUM('ACTIVE', 'SUSPENDED') NOT NULL DEFAULT 'ACTIVE',
  campusId      INT UNSIGNED NOT NULL,
  primaryRoleId INT UNSIGNED NOT NULL,
  PRIMARY KEY (userId),
  UNIQUE KEY uq_email (email),
  CONSTRAINT fk_User_campusId
    FOREIGN KEY (campusId) REFERENCES Campus (campusId)
    ON DELETE RESTRICT,
  CONSTRAINT fk_User_primaryRoleId
    FOREIGN KEY (primaryRoleId) REFERENCES `Role` (roleId)
    ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE UserHasRole (
  userId INT UNSIGNED NOT NULL,
  roleId INT UNSIGNED NOT NULL,
  PRIMARY KEY (userId, roleId),
  CONSTRAINT fk_UserHasRole_userId
    FOREIGN KEY (userId) REFERENCES `User` (userId)
    ON DELETE CASCADE,
  CONSTRAINT fk_UserHasRole_roleId
    FOREIGN KEY (roleId) REFERENCES `Role` (roleId)
    ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------- 2 Listing and discovery ----------
CREATE TABLE ItemCategory (
  categoryId       INT UNSIGNED NOT NULL AUTO_INCREMENT,
  categoryName     VARCHAR(50) NOT NULL,
  description      VARCHAR(255),
  activeStatus     BOOLEAN NOT NULL DEFAULT TRUE,
  parentCategoryId INT UNSIGNED,
  PRIMARY KEY (categoryId),
  CONSTRAINT fk_ItemCategory_parentCategoryId
    FOREIGN KEY (parentCategoryId) REFERENCES ItemCategory (categoryId)
    ON DELETE RESTRICT,
  CHECK (activeStatus IN (0, 1))
) ENGINE=InnoDB;

CREATE TABLE SecondhandItem (
  itemId       INT UNSIGNED NOT NULL AUTO_INCREMENT,
  title        VARCHAR(120),
  description  VARCHAR(2000),
  askingPrice  DECIMAL(8,2),
  listingDate  DATE,
  status       ENUM('AVAILABLE', 'RESERVED', 'SOLD', 'REMOVED')
               NOT NULL DEFAULT 'AVAILABLE',
  brand        VARCHAR(50),
  model        VARCHAR(50),
  `condition`  ENUM('NEW', 'LIKE_NEW', 'GOOD', 'FAIR', 'POOR'),
  yearAcquired YEAR,
  categoryId   INT UNSIGNED NOT NULL,
  sellerId     INT UNSIGNED NOT NULL,
  PRIMARY KEY (itemId),
  CONSTRAINT fk_SecondhandItem_categoryId
    FOREIGN KEY (categoryId) REFERENCES ItemCategory (categoryId)
    ON DELETE RESTRICT,
  CONSTRAINT fk_SecondhandItem_sellerId
    FOREIGN KEY (sellerId) REFERENCES `User` (userId)
    ON DELETE RESTRICT,
  CHECK (askingPrice >= 0),
  CHECK (`condition` IS NOT NULL)
) ENGINE=InnoDB;

CREATE TABLE ItemPhoto (
  photoId      INT UNSIGNED NOT NULL AUTO_INCREMENT,
  itemId       INT UNSIGNED NOT NULL,
  photoURL     VARCHAR(500) NOT NULL,
  displayOrder TINYINT UNSIGNED NOT NULL,
  PRIMARY KEY (photoId),
  CONSTRAINT fk_ItemPhoto_itemId
    FOREIGN KEY (itemId) REFERENCES SecondhandItem (itemId)
    ON DELETE CASCADE,
  CHECK (displayOrder >= 1)
) ENGINE=InnoDB;

CREATE TABLE ItemTag (
  tagId        INT UNSIGNED NOT NULL AUTO_INCREMENT,
  tagName      VARCHAR(30) NOT NULL,
  activeStatus BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (tagId),
  CHECK (activeStatus IN (0, 1))
) ENGINE=InnoDB;

CREATE TABLE ItemTags (
  itemId INT UNSIGNED NOT NULL,
  tagId  INT UNSIGNED NOT NULL,
  PRIMARY KEY (itemId, tagId),
  CONSTRAINT fk_ItemTags_itemId
    FOREIGN KEY (itemId) REFERENCES SecondhandItem (itemId)
    ON DELETE CASCADE,
  CONSTRAINT fk_ItemTags_tagId
    FOREIGN KEY (tagId) REFERENCES ItemTag (tagId)
    ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE SavedItem (
  dateSaved DATE NOT NULL,
  itemId    INT UNSIGNED NOT NULL,
  userId    INT UNSIGNED NOT NULL,
  PRIMARY KEY (itemId, userId),
  CONSTRAINT fk_SavedItem_itemId
    FOREIGN KEY (itemId) REFERENCES SecondhandItem (itemId)
    ON DELETE CASCADE,
  CONSTRAINT fk_SavedItem_userId
    FOREIGN KEY (userId) REFERENCES `User` (userId)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------- 3 Purchase requests and pickup ----------
CREATE TABLE PurchaseRequest (
  purchaseRequestId   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  purchaseRequestDate DATE,
  offeredPrice        DECIMAL(8,2),
  message             VARCHAR(500),
  status              ENUM('PENDING', 'ACCEPTED', 'REJECTED')
                      NOT NULL DEFAULT 'PENDING',
  buyerId             INT UNSIGNED NOT NULL,
  itemId              INT UNSIGNED NOT NULL,
  PRIMARY KEY (purchaseRequestId),
  CONSTRAINT fk_PurchaseRequest_buyerId
    FOREIGN KEY (buyerId) REFERENCES `User` (userId)
    ON DELETE RESTRICT,
  CONSTRAINT fk_PurchaseRequest_itemId
    FOREIGN KEY (itemId) REFERENCES SecondhandItem (itemId)
    ON DELETE RESTRICT,
  CHECK (offeredPrice >= 0)
) ENGINE=InnoDB;

CREATE TABLE Address (
  addressId     INT UNSIGNED NOT NULL AUTO_INCREMENT,
  streetAddress VARCHAR(100) NOT NULL,
  city          VARCHAR(50) NOT NULL,
  state         CHAR(2) NOT NULL,
  zipCode       VARCHAR(10) NOT NULL,
  longitude     DECIMAL(9,6),
  latitude      DECIMAL(8,6),
  PRIMARY KEY (addressId),
  CHECK (longitude BETWEEN -180 AND 180),
  CHECK (latitude BETWEEN -90 AND 90)
) ENGINE=InnoDB;

CREATE TABLE PickupPoint (
  pickupPointId   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  pickupPointName VARCHAR(80) NOT NULL,
  addressId       INT UNSIGNED NOT NULL,
  description     VARCHAR(255),
  activeStatus    BOOLEAN NOT NULL DEFAULT TRUE,
  ownerId         INT UNSIGNED NOT NULL,
  PRIMARY KEY (pickupPointId),
  CONSTRAINT fk_PickupPoint_addressId
    FOREIGN KEY (addressId) REFERENCES Address (addressId)
    ON DELETE RESTRICT,
  CONSTRAINT fk_PickupPoint_ownerId
    FOREIGN KEY (ownerId) REFERENCES `User` (userId)
    ON DELETE CASCADE,
  CHECK (activeStatus IN (0, 1))
) ENGINE=InnoDB;

CREATE TABLE TransactionOrder (
  transactionId     INT UNSIGNED NOT NULL AUTO_INCREMENT,
  agreedPrice       DECIMAL(8,2),
  transactionDate   DATE,
  pickupDateTime    DATETIME,
  status            ENUM('PENDING', 'COMPLETED', 'CANCELLED')
                    NOT NULL DEFAULT 'PENDING',
  completedAt       DATETIME,
  cancelledAt       DATETIME,
  purchaseRequestId INT UNSIGNED NOT NULL,
  pickupPointId     INT UNSIGNED NOT NULL,
  PRIMARY KEY (transactionId),
  CONSTRAINT fk_TransactionOrder_purchaseRequestId
    FOREIGN KEY (purchaseRequestId) REFERENCES PurchaseRequest (purchaseRequestId)
    ON DELETE RESTRICT,
  CONSTRAINT fk_TransactionOrder_pickupPointId
    FOREIGN KEY (pickupPointId) REFERENCES PickupPoint (pickupPointId)
    ON DELETE RESTRICT,
  CHECK (agreedPrice >= 0)
) ENGINE=InnoDB;

-- ---------- 4 Messaging ----------
CREATE TABLE Conversation (
  conversationId INT UNSIGNED NOT NULL AUTO_INCREMENT,
  createdAt      DATETIME,
  itemId         INT UNSIGNED NOT NULL,
  creatorId      INT UNSIGNED NOT NULL,
  PRIMARY KEY (conversationId),
  CONSTRAINT fk_Conversation_itemId
    FOREIGN KEY (itemId) REFERENCES SecondhandItem (itemId)
    ON DELETE RESTRICT,
  CONSTRAINT fk_Conversation_creatorId
    FOREIGN KEY (creatorId) REFERENCES `User` (userId)
    ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE ConversationParticipant (
  conversationId INT UNSIGNED NOT NULL,
  userId         INT UNSIGNED NOT NULL,
  PRIMARY KEY (conversationId, userId),
  CONSTRAINT fk_ConversationParticipant_conversationId
    FOREIGN KEY (conversationId) REFERENCES Conversation (conversationId)
    ON DELETE CASCADE,
  CONSTRAINT fk_ConversationParticipant_userId
    FOREIGN KEY (userId) REFERENCES `User` (userId)
    ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE Message (
  messageId      INT UNSIGNED NOT NULL AUTO_INCREMENT,
  content        VARCHAR(2000),
  sentAt         DATETIME,
  conversationId INT UNSIGNED NOT NULL,
  authorId       INT UNSIGNED NOT NULL,
  PRIMARY KEY (messageId),
  CONSTRAINT fk_Message_conversationId
    FOREIGN KEY (conversationId) REFERENCES Conversation (conversationId)
    ON DELETE RESTRICT,
  CONSTRAINT fk_Message_authorId
    FOREIGN KEY (authorId) REFERENCES `User` (userId)
    ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------- 5 Transaction reviews ----------
CREATE TABLE TransactionReview (
  reviewId     INT UNSIGNED NOT NULL AUTO_INCREMENT,
  reviewDate   DATE,
  rating       TINYINT UNSIGNED,
  comment      VARCHAR(1000),
  reviewStatus ENUM('PUBLISHED', 'FLAGGED', 'REMOVED')
               NOT NULL DEFAULT 'PUBLISHED',
  authorId     INT UNSIGNED NOT NULL,
  recipientId  INT UNSIGNED NOT NULL,
  PRIMARY KEY (reviewId),
  CONSTRAINT fk_TransactionReview_authorId
    FOREIGN KEY (authorId) REFERENCES `User` (userId)
    ON DELETE RESTRICT,
  CONSTRAINT fk_TransactionReview_recipientId
    FOREIGN KEY (recipientId) REFERENCES `User` (userId)
    ON DELETE RESTRICT,
  CHECK (rating BETWEEN 1 AND 5),
  CHECK (authorId <> recipientId)
) ENGINE=InnoDB;

CREATE TABLE BuyerReview (
  reviewId      INT UNSIGNED NOT NULL,
  transactionId INT UNSIGNED NOT NULL,
  PRIMARY KEY (reviewId),
  UNIQUE KEY uq_buyer_transaction (transactionId),
  CONSTRAINT fk_BuyerReview_reviewId
    FOREIGN KEY (reviewId) REFERENCES TransactionReview (reviewId)
    ON DELETE CASCADE,
  CONSTRAINT fk_BuyerReview_transactionId
    FOREIGN KEY (transactionId) REFERENCES TransactionOrder (transactionId)
    ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE SellerReview (
  reviewId      INT UNSIGNED NOT NULL,
  transactionId INT UNSIGNED NOT NULL,
  PRIMARY KEY (reviewId),
  UNIQUE KEY uq_seller_transaction (transactionId),
  CONSTRAINT fk_SellerReview_reviewId
    FOREIGN KEY (reviewId) REFERENCES TransactionReview (reviewId)
    ON DELETE CASCADE,
  CONSTRAINT fk_SellerReview_transactionId
    FOREIGN KEY (transactionId) REFERENCES TransactionOrder (transactionId)
    ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------- 6 Reports ----------
CREATE TABLE Report (
  reportId    INT UNSIGNED NOT NULL AUTO_INCREMENT,
  reason      ENUM('SCAM', 'SPAM', 'INAPPROPRIATE_CONTENT', 'HARASSMENT',
                'WRONG_DESCRIPTION', 'COUNTERFEIT', 'OTHER')
                NOT NULL DEFAULT 'OTHER',
  description VARCHAR(1000),
  reportDate  DATE,
  status      ENUM('RECEIVED', 'UNDER_REVIEW', 'RESOLVED', 'DISMISSED')
                NOT NULL DEFAULT 'RECEIVED',
  resolutionNote VARCHAR(1000),
  handledAt   DATETIME,
  reporterId  INT UNSIGNED NOT NULL,
  handledById INT UNSIGNED,
  PRIMARY KEY (reportId),
  CONSTRAINT fk_Report_reporterId
    FOREIGN KEY (reporterId) REFERENCES `User` (userId)
    ON DELETE RESTRICT,
  CONSTRAINT fk_Report_handledById
    FOREIGN KEY (handledById) REFERENCES `User` (userId)
    ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE ItemReport (
  reportId INT UNSIGNED NOT NULL,
  itemId   INT UNSIGNED NOT NULL,
  PRIMARY KEY (reportId),
  CONSTRAINT fk_ItemReport_reportId
    FOREIGN KEY (reportId) REFERENCES Report (reportId)
    ON DELETE CASCADE,
  CONSTRAINT fk_ItemReport_itemId
    FOREIGN KEY (itemId) REFERENCES SecondhandItem (itemId)
    ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE TransactionReport (
  reportId      INT UNSIGNED NOT NULL,
  transactionId INT UNSIGNED NOT NULL,
  PRIMARY KEY (reportId),
  CONSTRAINT fk_TransactionReport_reportId
    FOREIGN KEY (reportId) REFERENCES Report (reportId)
    ON DELETE CASCADE,
  CONSTRAINT fk_TransactionReport_transactionId
    FOREIGN KEY (transactionId) REFERENCES TransactionOrder (transactionId)
    ON DELETE RESTRICT
) ENGINE=InnoDB;
