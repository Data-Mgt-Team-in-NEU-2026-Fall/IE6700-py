-- MySQL dump 10.13  Distrib 9.7.2, for macos15 (arm64)
--
-- Host: localhost    Database: seattle_marketplace
-- ------------------------------------------------------
-- Server version	9.7.2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `seattle_marketplace`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `seattle_marketplace` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `seattle_marketplace`;

--
-- Table structure for table `Address`
--

DROP TABLE IF EXISTS `Address`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Address` (
  `addressId` int NOT NULL AUTO_INCREMENT,
  `streetAddress` varchar(255) NOT NULL,
  `city` varchar(100) NOT NULL,
  `state` varchar(100) NOT NULL,
  `zipCode` varchar(20) NOT NULL,
  `longitude` decimal(9,6) DEFAULT NULL,
  `latitude` decimal(8,6) DEFAULT NULL,
  PRIMARY KEY (`addressId`),
  CONSTRAINT `address_chk_1` CHECK ((`longitude` between -(180) and 180)),
  CONSTRAINT `address_chk_2` CHECK ((`latitude` between -(90) and 90))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Address`
--

LOCK TABLES `Address` WRITE;
/*!40000 ALTER TABLE `Address` DISABLE KEYS */;
INSERT INTO `Address` VALUES (1,'100 Example Street','Seattle','Washington','98109',NULL,NULL);
/*!40000 ALTER TABLE `Address` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Campus`
--

DROP TABLE IF EXISTS `Campus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Campus` (
  `campusId` int NOT NULL AUTO_INCREMENT,
  `campusName` varchar(100) NOT NULL,
  `emailDomain` varchar(255) NOT NULL,
  `address` varchar(255) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `zipCode` varchar(20) DEFAULT NULL,
  `longitude` decimal(9,6) DEFAULT NULL,
  `latitude` decimal(8,6) DEFAULT NULL,
  PRIMARY KEY (`campusId`),
  CONSTRAINT `campus_chk_1` CHECK ((`longitude` between -(180) and 180)),
  CONSTRAINT `campus_chk_2` CHECK ((`latitude` between -(90) and 90))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Campus`
--

LOCK TABLES `Campus` WRITE;
/*!40000 ALTER TABLE `Campus` DISABLE KEYS */;
INSERT INTO `Campus` VALUES (1,'Demo Seattle Campus','example.edu',NULL,'Seattle','Washington',NULL,NULL,NULL);
/*!40000 ALTER TABLE `Campus` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ItemCategory`
--

DROP TABLE IF EXISTS `ItemCategory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ItemCategory` (
  `categoryId` int NOT NULL AUTO_INCREMENT,
  `categoryName` varchar(100) NOT NULL,
  `description` text,
  `activeStatus` tinyint(1) DEFAULT NULL,
  `parentCategoryId` int DEFAULT NULL,
  PRIMARY KEY (`categoryId`),
  KEY `itemcategory_ibfk_1` (`parentCategoryId`),
  CONSTRAINT `itemcategory_ibfk_1` FOREIGN KEY (`parentCategoryId`) REFERENCES `ItemCategory` (`categoryId`),
  CONSTRAINT `chk_ItemCategory_activeStatus` CHECK ((`activeStatus` in (0,1)))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ItemCategory`
--

LOCK TABLES `ItemCategory` WRITE;
/*!40000 ALTER TABLE `ItemCategory` DISABLE KEYS */;
INSERT INTO `ItemCategory` VALUES (1,'Electronics',NULL,1,NULL),(2,'Computers',NULL,1,1);
/*!40000 ALTER TABLE `ItemCategory` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ItemPhoto`
--

DROP TABLE IF EXISTS `ItemPhoto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ItemPhoto` (
  `photoId` int NOT NULL AUTO_INCREMENT,
  `itemId` int NOT NULL,
  `photoURL` varchar(2048) NOT NULL,
  `displayOrder` int NOT NULL,
  PRIMARY KEY (`photoId`),
  KEY `itemphoto_ibfk_1` (`itemId`),
  CONSTRAINT `itemphoto_ibfk_1` FOREIGN KEY (`itemId`) REFERENCES `SecondhandItem` (`itemId`),
  CONSTRAINT `itemphoto_chk_1` CHECK ((`displayOrder` >= 1))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ItemPhoto`
--

LOCK TABLES `ItemPhoto` WRITE;
/*!40000 ALTER TABLE `ItemPhoto` DISABLE KEYS */;
INSERT INTO `ItemPhoto` VALUES (1,1,'https://example.com/laptop.jpg',1);
/*!40000 ALTER TABLE `ItemPhoto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ItemTag`
--

DROP TABLE IF EXISTS `ItemTag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ItemTag` (
  `tagId` int NOT NULL AUTO_INCREMENT,
  `tagName` varchar(100) NOT NULL,
  `activeStatus` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`tagId`),
  CONSTRAINT `chk_ItemTag_activeStatus` CHECK ((`activeStatus` in (0,1)))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ItemTag`
--

LOCK TABLES `ItemTag` WRITE;
/*!40000 ALTER TABLE `ItemTag` DISABLE KEYS */;
INSERT INTO `ItemTag` VALUES (1,'Student deal',1);
/*!40000 ALTER TABLE `ItemTag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ItemTags`
--

DROP TABLE IF EXISTS `ItemTags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ItemTags` (
  `itemId` int NOT NULL,
  `tagId` int NOT NULL,
  PRIMARY KEY (`itemId`,`tagId`),
  KEY `itemtags_ibfk_2` (`tagId`),
  CONSTRAINT `itemtags_ibfk_1` FOREIGN KEY (`itemId`) REFERENCES `SecondhandItem` (`itemId`),
  CONSTRAINT `itemtags_ibfk_2` FOREIGN KEY (`tagId`) REFERENCES `ItemTag` (`tagId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ItemTags`
--

LOCK TABLES `ItemTags` WRITE;
/*!40000 ALTER TABLE `ItemTags` DISABLE KEYS */;
INSERT INTO `ItemTags` VALUES (1,1),(2,1);
/*!40000 ALTER TABLE `ItemTags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `PickupPoint`
--

DROP TABLE IF EXISTS `PickupPoint`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PickupPoint` (
  `pickupPointId` int NOT NULL AUTO_INCREMENT,
  `pickupPointName` varchar(100) NOT NULL,
  `addressId` int NOT NULL,
  `description` text,
  `activeStatus` tinyint(1) DEFAULT NULL,
  `ownerId` int NOT NULL,
  PRIMARY KEY (`pickupPointId`),
  KEY `pickuppoint_ibfk_1` (`addressId`),
  KEY `pickuppoint_ibfk_2` (`ownerId`),
  CONSTRAINT `pickuppoint_ibfk_1` FOREIGN KEY (`addressId`) REFERENCES `Address` (`addressId`),
  CONSTRAINT `pickuppoint_ibfk_2` FOREIGN KEY (`ownerId`) REFERENCES `User` (`userId`),
  CONSTRAINT `chk_PickupPoint_activeStatus` CHECK ((`activeStatus` in (0,1)))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `PickupPoint`
--

LOCK TABLES `PickupPoint` WRITE;
/*!40000 ALTER TABLE `PickupPoint` DISABLE KEYS */;
INSERT INTO `PickupPoint` VALUES (1,'Demo campus lobby',1,NULL,1,1);
/*!40000 ALTER TABLE `PickupPoint` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `PurchaseRequest`
--

DROP TABLE IF EXISTS `PurchaseRequest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PurchaseRequest` (
  `purchaseRequestId` int NOT NULL AUTO_INCREMENT,
  `purchaseRequestDate` date DEFAULT NULL,
  `offeredPrice` decimal(10,2) DEFAULT NULL,
  `message` text,
  `status` varchar(20) DEFAULT NULL,
  `buyerId` int NOT NULL,
  `itemId` int NOT NULL,
  PRIMARY KEY (`purchaseRequestId`),
  KEY `purchaserequest_ibfk_1` (`buyerId`),
  KEY `purchaserequest_ibfk_2` (`itemId`),
  CONSTRAINT `purchaserequest_ibfk_1` FOREIGN KEY (`buyerId`) REFERENCES `User` (`userId`),
  CONSTRAINT `purchaserequest_ibfk_2` FOREIGN KEY (`itemId`) REFERENCES `SecondhandItem` (`itemId`),
  CONSTRAINT `purchaserequest_chk_1` CHECK ((`offeredPrice` >= 0)),
  CONSTRAINT `purchaserequest_chk_2` CHECK ((`status` in (_utf8mb4'PENDING',_utf8mb4'ACCEPTED',_utf8mb4'REJECTED')))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `PurchaseRequest`
--

LOCK TABLES `PurchaseRequest` WRITE;
/*!40000 ALTER TABLE `PurchaseRequest` DISABLE KEYS */;
INSERT INTO `PurchaseRequest` VALUES (1,'2026-10-21',280.00,'Can I collect tomorrow?','ACCEPTED',2,1),(2,'2026-10-24',20.00,NULL,'PENDING',2,2),(3,'2026-10-24',75.00,NULL,'ACCEPTED',2,3);
/*!40000 ALTER TABLE `PurchaseRequest` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Role`
--

DROP TABLE IF EXISTS `Role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Role` (
  `roleId` int NOT NULL AUTO_INCREMENT,
  `roleName` varchar(100) NOT NULL,
  PRIMARY KEY (`roleId`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Role`
--

LOCK TABLES `Role` WRITE;
/*!40000 ALTER TABLE `Role` DISABLE KEYS */;
INSERT INTO `Role` VALUES (1,'Student');
/*!40000 ALTER TABLE `Role` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SavedItem`
--

DROP TABLE IF EXISTS `SavedItem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SavedItem` (
  `dateSaved` date NOT NULL,
  `itemId` int NOT NULL,
  `userId` int NOT NULL,
  PRIMARY KEY (`itemId`,`userId`),
  KEY `saveditem_ibfk_2` (`userId`),
  CONSTRAINT `saveditem_ibfk_1` FOREIGN KEY (`itemId`) REFERENCES `SecondhandItem` (`itemId`),
  CONSTRAINT `saveditem_ibfk_2` FOREIGN KEY (`userId`) REFERENCES `User` (`userId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SavedItem`
--

LOCK TABLES `SavedItem` WRITE;
/*!40000 ALTER TABLE `SavedItem` DISABLE KEYS */;
INSERT INTO `SavedItem` VALUES ('2026-10-23',2,2);
/*!40000 ALTER TABLE `SavedItem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SecondhandItem`
--

DROP TABLE IF EXISTS `SecondhandItem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SecondhandItem` (
  `itemId` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) DEFAULT NULL,
  `description` text,
  `askingPrice` decimal(10,2) DEFAULT NULL,
  `listingDate` date DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `brand` varchar(100) DEFAULT NULL,
  `model` varchar(100) DEFAULT NULL,
  `condition` varchar(20) DEFAULT NULL,
  `yearAcquired` int DEFAULT NULL,
  `categoryId` int NOT NULL,
  `sellerId` int NOT NULL,
  PRIMARY KEY (`itemId`),
  KEY `secondhanditem_ibfk_1` (`categoryId`),
  KEY `secondhanditem_ibfk_2` (`sellerId`),
  CONSTRAINT `secondhanditem_ibfk_1` FOREIGN KEY (`categoryId`) REFERENCES `ItemCategory` (`categoryId`),
  CONSTRAINT `secondhanditem_ibfk_2` FOREIGN KEY (`sellerId`) REFERENCES `User` (`userId`),
  CONSTRAINT `secondhanditem_chk_1` CHECK ((`askingPrice` >= 0)),
  CONSTRAINT `secondhanditem_chk_2` CHECK ((`status` in (_utf8mb4'AVAILABLE',_utf8mb4'RESERVED',_utf8mb4'SOLD',_utf8mb4'REMOVED'))),
  CONSTRAINT `secondhanditem_chk_3` CHECK ((`condition` in (_utf8mb4'NEW',_utf8mb4'LIKE_NEW',_utf8mb4'GOOD',_utf8mb4'FAIR',_utf8mb4'POOR')))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SecondhandItem`
--

LOCK TABLES `SecondhandItem` WRITE;
/*!40000 ALTER TABLE `SecondhandItem` DISABLE KEYS */;
INSERT INTO `SecondhandItem` VALUES (1,'Used laptop',NULL,300.00,'2026-10-20','SOLD',NULL,NULL,'GOOD',NULL,2,1),(2,'Wireless keyboard',NULL,25.00,'2026-10-21','AVAILABLE',NULL,NULL,'LIKE_NEW',NULL,1,1),(3,'Computer monitor',NULL,80.00,'2026-10-22','RESERVED',NULL,NULL,'GOOD',NULL,1,1);
/*!40000 ALTER TABLE `SecondhandItem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `TransactionOrder`
--

DROP TABLE IF EXISTS `TransactionOrder`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `TransactionOrder` (
  `transactionId` int NOT NULL AUTO_INCREMENT,
  `agreedPrice` decimal(10,2) DEFAULT NULL,
  `transactionDate` date DEFAULT NULL,
  `pickupDateTime` datetime DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `completedAt` datetime DEFAULT NULL,
  `cancelledAt` datetime DEFAULT NULL,
  `purchaseRequestId` int NOT NULL,
  `pickupPointId` int NOT NULL,
  PRIMARY KEY (`transactionId`),
  KEY `transactionorder_ibfk_1` (`purchaseRequestId`),
  KEY `transactionorder_ibfk_2` (`pickupPointId`),
  CONSTRAINT `transactionorder_ibfk_1` FOREIGN KEY (`purchaseRequestId`) REFERENCES `PurchaseRequest` (`purchaseRequestId`),
  CONSTRAINT `transactionorder_ibfk_2` FOREIGN KEY (`pickupPointId`) REFERENCES `PickupPoint` (`pickupPointId`),
  CONSTRAINT `transactionorder_chk_1` CHECK ((`agreedPrice` >= 0)),
  CONSTRAINT `transactionorder_chk_2` CHECK ((`status` in (_utf8mb4'PENDING',_utf8mb4'COMPLETED',_utf8mb4'CANCELLED')))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `TransactionOrder`
--

LOCK TABLES `TransactionOrder` WRITE;
/*!40000 ALTER TABLE `TransactionOrder` DISABLE KEYS */;
INSERT INTO `TransactionOrder` VALUES (1,280.00,'2026-10-21','2026-10-22 12:00:00','COMPLETED','2026-10-22 12:15:00',NULL,1,1),(2,75.00,'2026-10-24','2026-10-30 13:00:00','PENDING',NULL,NULL,3,1);
/*!40000 ALTER TABLE `TransactionOrder` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `User`
--

DROP TABLE IF EXISTS `User`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `User` (
  `userId` int NOT NULL AUTO_INCREMENT,
  `firstName` varchar(100) DEFAULT NULL,
  `lastName` varchar(100) DEFAULT NULL,
  `email` varchar(255) NOT NULL,
  `phone` varchar(30) DEFAULT NULL,
  `birthDate` date DEFAULT NULL,
  `dateJoined` date DEFAULT NULL,
  `accountStatus` varchar(20) NOT NULL,
  `campusId` int NOT NULL,
  `primaryRoleId` int NOT NULL,
  PRIMARY KEY (`userId`),
  KEY `user_ibfk_1` (`campusId`),
  KEY `user_ibfk_2` (`primaryRoleId`),
  CONSTRAINT `user_ibfk_1` FOREIGN KEY (`campusId`) REFERENCES `Campus` (`campusId`),
  CONSTRAINT `user_ibfk_2` FOREIGN KEY (`primaryRoleId`) REFERENCES `Role` (`roleId`),
  CONSTRAINT `user_chk_1` CHECK ((`accountStatus` in (_utf8mb4'ACTIVE',_utf8mb4'SUSPENDED')))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `User`
--

LOCK TABLES `User` WRITE;
/*!40000 ALTER TABLE `User` DISABLE KEYS */;
INSERT INTO `User` VALUES (1,'Alex','Chen','alex@example.edu',NULL,NULL,NULL,'ACTIVE',1,1),(2,'Sam','Reyes','sam@example.edu',NULL,NULL,NULL,'ACTIVE',1,1);
/*!40000 ALTER TABLE `User` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-29 12:21:11
