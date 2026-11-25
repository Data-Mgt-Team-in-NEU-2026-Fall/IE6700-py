-- Seattle Campus Secondhand Marketplace queries
USE seattle_marketplace;

-- ============================================================
-- 0. Parameters
-- ============================================================
SET @email = 'liam.fischer3@example.edu';
SET @userId = 3;
SET @sellerId = 12;
SET @itemId = 10;
SET @campusId = NULL;
SET @categoryId = 7;
SET @minPrice = 10;
SET @maxPrice = 300;
SET @keyword = NULL;
SET @tagId = NULL;
SET @transactionId = 18;
SET @reviewedTransactionId = 1;
SET @conversationId = 30;
SET @adminId = 8;
SET @reportId = 3;

-- ============================================================
-- 1. Identity and personal records (UC-1101, UC-1102)
-- ============================================================

-- 1.1 UC-1101 Sign in with the campus e-mail: user, campus, roles, account status
SELECT u.userId, u.firstName, u.lastName, u.email, u.accountStatus,
       c.campusName, c.emailDomain,
       SUBSTRING_INDEX(u.email, '@', -1) = c.emailDomain AS emailMatchesCampus,
       pr.roleName AS primaryRole,
       GROUP_CONCAT(r.roleName ORDER BY r.roleName) AS allRoles
FROM `User` u
JOIN Campus c  ON c.campusId = u.campusId
JOIN `Role` pr ON pr.roleId  = u.primaryRoleId
LEFT JOIN UserHasRole uh ON uh.userId = u.userId
LEFT JOIN `Role` r       ON r.roleId  = uh.roleId
WHERE u.email = @email
GROUP BY u.userId, c.campusId, pr.roleId;

-- 1.2 UC-1102 My listings: status, photos, saves, open requests
SELECT i.itemId, i.title, i.askingPrice, i.status, i.listingDate,
       (SELECT COUNT(*) FROM ItemPhoto p WHERE p.itemId = i.itemId) AS photos,
       (SELECT COUNT(*) FROM SavedItem s WHERE s.itemId = i.itemId) AS saves,
       (SELECT COUNT(*) FROM PurchaseRequest pr
         WHERE pr.itemId = i.itemId AND pr.status = 'PENDING') AS pendingRequests
FROM SecondhandItem i
WHERE i.sellerId = @sellerId
ORDER BY i.listingDate DESC;

-- 1.3 UC-1102 My purchase requests and how they are going
SELECT pr.purchaseRequestId, pr.purchaseRequestDate, i.title, i.askingPrice,
       pr.offeredPrice, pr.status AS requestStatus,
       CONCAT(s.firstName, ' ', s.lastName) AS seller,
       t.transactionId, t.status AS orderStatus
FROM PurchaseRequest pr
JOIN SecondhandItem i ON i.itemId = pr.itemId
JOIN `User` s         ON s.userId = i.sellerId
LEFT JOIN TransactionOrder t ON t.purchaseRequestId = pr.purchaseRequestId
WHERE pr.buyerId = @userId
ORDER BY pr.purchaseRequestDate DESC;

-- 1.4 UC-1102 / UC-4402 My orders as buyer or seller, with pickup details and a cross-campus flag
SELECT t.transactionId,
       IF(pr.buyerId = @userId, 'buyer', 'seller') AS myRole,
       i.title, i.askingPrice, t.agreedPrice, t.status,
       CONCAT(o.firstName, ' ', o.lastName) AS counterpart,
       t.pickupDateTime, pp.pickupPointName,
       CONCAT(a.streetAddress, ', ', a.city) AS pickupAddress,
       bc.campusId <> sc.campusId AS crossCampus
FROM TransactionOrder t
JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
JOIN SecondhandItem i   ON i.itemId = pr.itemId
JOIN `User` b  ON b.userId = pr.buyerId
JOIN `User` s  ON s.userId = i.sellerId
JOIN Campus bc ON bc.campusId = b.campusId
JOIN Campus sc ON sc.campusId = s.campusId
JOIN `User` o  ON o.userId = IF(pr.buyerId = @userId, s.userId, b.userId)
JOIN PickupPoint pp ON pp.pickupPointId = t.pickupPointId
JOIN Address a      ON a.addressId = pp.addressId
WHERE pr.buyerId = @userId OR i.sellerId = @userId
ORDER BY t.transactionDate DESC;

-- 1.5 UC-1102 My saved items with their current status
SELECT s.dateSaved, i.itemId, i.title, i.askingPrice, i.status
FROM SavedItem s
JOIN SecondhandItem i ON i.itemId = s.itemId
WHERE s.userId = @userId
ORDER BY s.dateSaved DESC;

-- 1.6 UC-1102 Reviews I received (with average) and reviews I wrote
SELECT r.reviewId, r.reviewDate, r.rating, r.comment,
       IF(b.reviewId IS NOT NULL, 'as buyer', 'as seller') AS reviewedAs,
       CONCAT(a.firstName, ' ', a.lastName) AS author
FROM TransactionReview r
JOIN `User` a ON a.userId = r.authorId
LEFT JOIN BuyerReview b ON b.reviewId = r.reviewId
WHERE r.recipientId = @userId
ORDER BY r.reviewDate DESC;

SELECT ROUND(AVG(rating), 2) AS averageRatingReceived, COUNT(*) AS reviewsReceived
FROM TransactionReview
WHERE recipientId = @userId;

SELECT r.reviewId, r.reviewDate, r.rating, r.comment,
       CONCAT(rc.firstName, ' ', rc.lastName) AS aboutUser
FROM TransactionReview r
JOIN `User` rc ON rc.userId = r.recipientId
WHERE r.authorId = @userId
ORDER BY r.reviewDate DESC;

-- ============================================================
-- 2. Browse, save and request items (UC-2201, UC-2202, UC-2401)
-- ============================================================

-- 2.1 UC-5201 / UC-2201 Category tree with depth, path and item counts
WITH RECURSIVE tree AS (
  SELECT categoryId, categoryName, parentCategoryId, activeStatus,
         0 AS depth, CAST(categoryName AS CHAR(300)) AS path
  FROM ItemCategory WHERE parentCategoryId IS NULL
  UNION ALL
  SELECT c.categoryId, c.categoryName, c.parentCategoryId, c.activeStatus,
         t.depth + 1, CONCAT(t.path, ' > ', c.categoryName)
  FROM ItemCategory c JOIN tree t ON c.parentCategoryId = t.categoryId
)
SELECT t.categoryId, CONCAT(REPEAT('  ', t.depth), t.categoryName) AS category, t.activeStatus,
       COUNT(i.itemId) AS items,
       SUM(i.status = 'AVAILABLE') AS availableItems
FROM tree t
LEFT JOIN SecondhandItem i ON i.categoryId = t.categoryId
GROUP BY t.categoryId, t.categoryName, t.depth, t.activeStatus, t.path
ORDER BY t.path;

-- 2.2 UC-2201 Browse and filter available items by category (with subcategories),
WITH RECURSIVE cat AS (
  SELECT categoryId FROM ItemCategory WHERE categoryId = @categoryId
  UNION ALL
  SELECT c.categoryId FROM ItemCategory c JOIN cat ON c.parentCategoryId = cat.categoryId
)
SELECT i.itemId, i.title, i.askingPrice, i.`condition`, c.categoryName,
       camp.campusName AS sellerCampus,
       (SELECT p.photoURL FROM ItemPhoto p
         WHERE p.itemId = i.itemId ORDER BY p.displayOrder LIMIT 1) AS coverPhoto,
       (SELECT GROUP_CONCAT(t.tagName ORDER BY t.tagName)
          FROM ItemTags it JOIN ItemTag t ON t.tagId = it.tagId
         WHERE it.itemId = i.itemId) AS tags,
       i.listingDate
FROM SecondhandItem i
JOIN ItemCategory c ON c.categoryId = i.categoryId
JOIN `User` u       ON u.userId = i.sellerId
JOIN Campus camp    ON camp.campusId = u.campusId
WHERE i.status = 'AVAILABLE'
  AND (@categoryId IS NULL OR i.categoryId IN (SELECT categoryId FROM cat))
  AND (@campusId   IS NULL OR u.campusId = @campusId)
  AND (@minPrice   IS NULL OR i.askingPrice >= @minPrice)
  AND (@maxPrice   IS NULL OR i.askingPrice <= @maxPrice)
  AND (@keyword    IS NULL OR i.title LIKE CONCAT('%', @keyword, '%')
                           OR i.description LIKE CONCAT('%', @keyword, '%'))
  AND (@tagId      IS NULL OR EXISTS (SELECT 1 FROM ItemTags it
                                       WHERE it.itemId = i.itemId AND it.tagId = @tagId))
ORDER BY i.listingDate DESC, i.itemId;

-- 2.3 UC-2201 Item detail: seller with rating, photos, tags, interest
SELECT i.itemId, i.title, i.description, i.askingPrice, i.`condition`, i.brand, i.model,
       i.yearAcquired, i.status, i.listingDate, c.categoryName,
       CONCAT(s.firstName, ' ', s.lastName) AS seller, sc.campusName AS sellerCampus,
       (SELECT ROUND(AVG(r.rating), 2) FROM TransactionReview r WHERE r.recipientId = s.userId) AS sellerRating,
       (SELECT COUNT(*) FROM TransactionReview r WHERE r.recipientId = s.userId) AS sellerReviews,
       (SELECT GROUP_CONCAT(p.photoURL ORDER BY p.displayOrder SEPARATOR ' | ')
          FROM ItemPhoto p WHERE p.itemId = i.itemId) AS photos,
       (SELECT GROUP_CONCAT(t.tagName ORDER BY t.tagName)
          FROM ItemTags it JOIN ItemTag t ON t.tagId = it.tagId WHERE it.itemId = i.itemId) AS tags,
       (SELECT COUNT(*) FROM SavedItem sv WHERE sv.itemId = i.itemId) AS saves,
       (SELECT COUNT(*) FROM PurchaseRequest pr WHERE pr.itemId = i.itemId) AS requests
FROM SecondhandItem i
JOIN ItemCategory c ON c.categoryId = i.categoryId
JOIN `User` s       ON s.userId = i.sellerId
JOIN Campus sc      ON sc.campusId = s.campusId
WHERE i.itemId = @itemId;

-- 2.4 UC-2202 Most saved items that can still be bought
SELECT i.itemId, i.title, i.askingPrice, COUNT(s.userId) AS saves
FROM SecondhandItem i
JOIN SavedItem s ON s.itemId = i.itemId
WHERE i.status = 'AVAILABLE'
GROUP BY i.itemId, i.title, i.askingPrice
ORDER BY saves DESC, i.itemId
LIMIT 5;

-- 2.5 UC-2401 Requests received by one item, with the offer against the asking price
SELECT pr.purchaseRequestId, pr.purchaseRequestDate,
       CONCAT(b.firstName, ' ', b.lastName) AS buyer,
       pr.offeredPrice, i.askingPrice,
       ROUND(pr.offeredPrice / NULLIF(i.askingPrice, 0) * 100) AS offerPercentOfAsking,
       pr.message, pr.status
FROM PurchaseRequest pr
JOIN SecondhandItem i ON i.itemId = pr.itemId
JOIN `User` b         ON b.userId = pr.buyerId
WHERE pr.itemId = @itemId
ORDER BY pr.purchaseRequestDate;

-- ============================================================
-- 3. Seller tools (UC-3202, UC-3401, UC-3402)
-- ============================================================

-- 3.1 UC-3401 Open requests on my items (to answer or accept)
SELECT pr.purchaseRequestId, i.itemId, i.title, i.status AS itemStatus,
       CONCAT(b.firstName, ' ', b.lastName) AS buyer, bc.campusName AS buyerCampus,
       i.askingPrice, pr.offeredPrice, pr.message, pr.purchaseRequestDate
FROM PurchaseRequest pr
JOIN SecondhandItem i ON i.itemId = pr.itemId
JOIN `User` b         ON b.userId = pr.buyerId
JOIN Campus bc        ON bc.campusId = b.campusId
WHERE pr.status = 'PENDING' AND i.sellerId = @sellerId
ORDER BY pr.purchaseRequestDate;

-- 3.2 UC-3402 My saved pickup points (the seller's own), with address and how often they were used
SELECT pp.pickupPointId, pp.pickupPointName, pp.description, pp.activeStatus,
       CONCAT(a.streetAddress, ', ', a.city, ', ', a.state, ' ', a.zipCode) AS address,
       COUNT(t.transactionId) AS ordersUsingIt
FROM PickupPoint pp
JOIN Address a ON a.addressId = pp.addressId
LEFT JOIN TransactionOrder t ON t.pickupPointId = pp.pickupPointId
WHERE pp.ownerId = @sellerId
GROUP BY pp.pickupPointId, a.addressId
ORDER BY pp.pickupPointName;

-- 3.3 UC-3202 Listings that need attention: sold or removed items still with pending
SELECT i.itemId, i.title, i.status, i.listingDate,
       SUM(pr.status = 'PENDING') AS pendingRequests,
       COUNT(pr.purchaseRequestId) AS totalRequests
FROM SecondhandItem i
LEFT JOIN PurchaseRequest pr ON pr.itemId = i.itemId
GROUP BY i.itemId, i.title, i.status, i.listingDate
HAVING (i.status IN ('SOLD', 'REMOVED') AND SUM(pr.status = 'PENDING') > 0)
    OR (i.status = 'AVAILABLE' AND COUNT(pr.purchaseRequestId) = 0
        AND i.listingDate < DATE_SUB('2026-10-30', INTERVAL 30 DAY))
ORDER BY i.listingDate;

-- ============================================================
-- 4. Conversations (UC-4301)
-- ============================================================

-- 4.1 My conversations: item, last message, message count, and whether they are still open.
SELECT c.conversationId, i.title, c.createdAt,
       lm.content AS lastMessage, lm.sentAt AS lastMessageAt,
       (SELECT COUNT(*) FROM Message m WHERE m.conversationId = c.conversationId) AS messages,
       IF(i.status = 'REMOVED'
          OR EXISTS (SELECT 1 FROM PurchaseRequest pr
                     JOIN TransactionOrder t ON t.purchaseRequestId = pr.purchaseRequestId
                     WHERE pr.itemId = i.itemId AND t.status = 'COMPLETED')
          OR EXISTS (SELECT 1 FROM ConversationParticipant cp2
                     JOIN `User` u2 ON u2.userId = cp2.userId
                     WHERE cp2.conversationId = c.conversationId AND u2.accountStatus = 'SUSPENDED'),
          'closed', 'open') AS chatState
FROM ConversationParticipant cp
JOIN Conversation c   ON c.conversationId = cp.conversationId
JOIN SecondhandItem i ON i.itemId = c.itemId
JOIN Message lm ON lm.messageId = (SELECT m2.messageId FROM Message m2
                                    WHERE m2.conversationId = c.conversationId
                                    ORDER BY m2.sentAt DESC, m2.messageId DESC LIMIT 1)
WHERE cp.userId = @userId
ORDER BY lm.sentAt DESC;

-- 4.2 Message thread of one conversation, oldest first
SELECT m.messageId, m.sentAt, CONCAT(u.firstName, ' ', u.lastName) AS author, m.content
FROM Message m
JOIN `User` u ON u.userId = m.authorId
WHERE m.conversationId = @conversationId
ORDER BY m.sentAt, m.messageId;

-- 4.3 Participants of one conversation
SELECT u.userId, CONCAT(u.firstName, ' ', u.lastName) AS participant,
       CASE WHEN u.userId = c.creatorId THEN 'creator'
            WHEN u.userId = i.sellerId  THEN 'seller'
            ELSE 'participant' END AS roleInConversation
FROM ConversationParticipant cp
JOIN Conversation c   ON c.conversationId = cp.conversationId
JOIN SecondhandItem i ON i.itemId = c.itemId
JOIN `User` u         ON u.userId = cp.userId
WHERE cp.conversationId = @conversationId;

-- 4.4 Conversations about one item, with creator and message count
SELECT c.conversationId, c.createdAt, CONCAT(u.firstName, ' ', u.lastName) AS creator,
       COUNT(m.messageId) AS messages
FROM Conversation c
JOIN `User` u ON u.userId = c.creatorId
LEFT JOIN Message m ON m.conversationId = c.conversationId
WHERE c.itemId = @itemId
GROUP BY c.conversationId, c.createdAt, u.userId
ORDER BY c.createdAt;

-- 4.5 Find the existing conversation between me and the item's seller
SELECT c.conversationId
FROM Conversation c
WHERE c.itemId = @itemId
  AND EXISTS (SELECT 1 FROM ConversationParticipant p WHERE p.conversationId = c.conversationId AND p.userId = @userId)
  AND EXISTS (SELECT 1 FROM ConversationParticipant p WHERE p.conversationId = c.conversationId
              AND p.userId = (SELECT sellerId FROM SecondhandItem WHERE itemId = @itemId));

-- ============================================================
-- 5. Orders, reviews and reports (UC-4401 to UC-4501, UC-1501)
-- ============================================================

-- 5.1 UC-4401 Order detail for one order
SELECT t.transactionId, t.status, i.title, i.askingPrice, pr.offeredPrice, t.agreedPrice,
       CONCAT(b.firstName, ' ', b.lastName) AS buyer,
       CONCAT(s.firstName, ' ', s.lastName) AS seller,
       t.transactionDate, t.pickupDateTime, t.completedAt, t.cancelledAt,
       pp.pickupPointName, CONCAT(a.streetAddress, ', ', a.city) AS pickupAddress,
       bc.campusId <> sc.campusId AS crossCampus
FROM TransactionOrder t
JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
JOIN SecondhandItem i   ON i.itemId = pr.itemId
JOIN `User` b  ON b.userId = pr.buyerId
JOIN `User` s  ON s.userId = i.sellerId
JOIN Campus bc ON bc.campusId = b.campusId
JOIN Campus sc ON sc.campusId = s.campusId
JOIN PickupPoint pp ON pp.pickupPointId = t.pickupPointId
JOIN Address a      ON a.addressId = pp.addressId
WHERE t.transactionId = @transactionId;

-- 5.2 UC-4501 Completed orders where the review in one direction is still missing
SELECT t.transactionId, i.title, t.completedAt,
       CONCAT(b.firstName, ' ', b.lastName) AS buyer,
       CONCAT(s.firstName, ' ', s.lastName) AS seller,
       NOT EXISTS (SELECT 1 FROM BuyerReview  x WHERE x.transactionId = t.transactionId) AS sellerMayReviewBuyer,
       NOT EXISTS (SELECT 1 FROM SellerReview x WHERE x.transactionId = t.transactionId) AS buyerMayReviewSeller
FROM TransactionOrder t
JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
JOIN SecondhandItem i   ON i.itemId = pr.itemId
JOIN `User` b ON b.userId = pr.buyerId
JOIN `User` s ON s.userId = i.sellerId
WHERE t.status = 'COMPLETED'
  AND (NOT EXISTS (SELECT 1 FROM BuyerReview  x WHERE x.transactionId = t.transactionId)
    OR NOT EXISTS (SELECT 1 FROM SellerReview x WHERE x.transactionId = t.transactionId))
ORDER BY t.completedAt DESC;

-- 5.3 UC-4501 Both reviews of one order (review of the buyer, review of the seller)
SELECT 'buyer' AS reviewOf, r.reviewId, r.rating, r.comment,
       CONCAT(a.firstName, ' ', a.lastName) AS author
FROM BuyerReview br
JOIN TransactionReview r ON r.reviewId = br.reviewId
JOIN `User` a ON a.userId = r.authorId
WHERE br.transactionId = @reviewedTransactionId
UNION ALL
SELECT 'seller', r.reviewId, r.rating, r.comment, CONCAT(a.firstName, ' ', a.lastName)
FROM SellerReview sr
JOIN TransactionReview r ON r.reviewId = sr.reviewId
JOIN `User` a ON a.userId = r.authorId
WHERE sr.transactionId = @reviewedTransactionId;

-- 5.4 UC-1501 Reports I filed, with their target and progress (the reported
SELECT r.reportId, r.reportDate, r.reason, r.status,
       IF(ir.reportId IS NOT NULL, 'item', 'order') AS targetType,
       COALESCE(ii.title, ti.title) AS targetItem,
       r.resolutionNote
FROM Report r
LEFT JOIN ItemReport ir ON ir.reportId = r.reportId
LEFT JOIN SecondhandItem ii ON ii.itemId = ir.itemId
LEFT JOIN TransactionReport tr ON tr.reportId = r.reportId
LEFT JOIN TransactionOrder t   ON t.transactionId = tr.transactionId
LEFT JOIN PurchaseRequest p    ON p.purchaseRequestId = t.purchaseRequestId
LEFT JOIN SecondhandItem ti    ON ti.itemId = p.itemId
WHERE r.reporterId = (SELECT reporterId FROM Report WHERE reportId = @reportId)
ORDER BY r.reportDate DESC;

-- 5.5 UC-5501 Report queue for administrators: open reports with target, seller and reporter
SELECT r.reportId, r.reportDate, r.reason, r.status,
       IF(ir.reportId IS NOT NULL, 'item', 'order') AS targetType,
       COALESCE(ir.itemId, p.itemId) AS itemId,
       COALESCE(ii.title, ti.title) AS itemTitle,
       t.transactionId,
       CONCAT(su.firstName, ' ', su.lastName) AS sellerOfItem,
       su.accountStatus AS sellerAccount,
       CONCAT(rp.firstName, ' ', rp.lastName) AS reporter,
       DATEDIFF('2026-10-30', r.reportDate) AS daysWaiting
FROM Report r
JOIN `User` rp ON rp.userId = r.reporterId
LEFT JOIN ItemReport ir ON ir.reportId = r.reportId
LEFT JOIN SecondhandItem ii ON ii.itemId = ir.itemId
LEFT JOIN TransactionReport tr ON tr.reportId = r.reportId
LEFT JOIN TransactionOrder t   ON t.transactionId = tr.transactionId
LEFT JOIN PurchaseRequest p    ON p.purchaseRequestId = t.purchaseRequestId
LEFT JOIN SecondhandItem ti    ON ti.itemId = p.itemId
JOIN `User` su ON su.userId = COALESCE(ii.sellerId, ti.sellerId)
WHERE r.status IN ('RECEIVED', 'UNDER_REVIEW')
ORDER BY FIELD(r.status, 'RECEIVED', 'UNDER_REVIEW'), r.reportDate;

-- ============================================================
-- 6. Changes (each block runs inside a transaction and is rolled back)
-- ============================================================

-- 6.1 UC-3201 Publish an item with photos and tags
START TRANSACTION;
INSERT INTO SecondhandItem
  (title, description, askingPrice, listingDate, status, brand, model, `condition`, yearAcquired, categoryId, sellerId)
VALUES ('Desk fan', 'Quiet 3-speed fan.', 12.00, CURDATE(), 'AVAILABLE', 'Honeywell', 'HT-900', 'GOOD', 2022, 9, @sellerId);
SET @newItem = LAST_INSERT_ID();
INSERT INTO ItemPhoto (itemId, photoURL, displayOrder) VALUES
  (@newItem, 'https://example.com/photos/desk-fan-1.jpg', 1),
  (@newItem, 'https://example.com/photos/desk-fan-2.jpg', 2);
INSERT INTO ItemTags (itemId, tagId) VALUES (@newItem, 1), (@newItem, 4);
SELECT i.itemId, i.title, i.status, COUNT(DISTINCT p.photoId) AS photos, COUNT(DISTINCT it.tagId) AS tags
FROM SecondhandItem i
LEFT JOIN ItemPhoto p ON p.itemId = i.itemId
LEFT JOIN ItemTags it ON it.itemId = i.itemId
WHERE i.itemId = @newItem GROUP BY i.itemId;
ROLLBACK;

-- 6.2 UC-2202 Save an item (repeating it does not duplicate), then un-save it
START TRANSACTION;
INSERT INTO SavedItem (dateSaved, itemId, userId) VALUES (CURDATE(), 33, @userId)
  ON DUPLICATE KEY UPDATE dateSaved = dateSaved;
INSERT INTO SavedItem (dateSaved, itemId, userId) VALUES (CURDATE(), 33, @userId)
  ON DUPLICATE KEY UPDATE dateSaved = dateSaved;
SELECT COUNT(*) AS rowsForThisUserAndItem FROM SavedItem WHERE userId = @userId AND itemId = 33;
DELETE FROM SavedItem WHERE userId = @userId AND itemId = 33;
SELECT COUNT(*) AS rowsAfterUnsave FROM SavedItem WHERE userId = @userId AND itemId = 33;
ROLLBACK;

-- 6.3 UC-2401 Send a purchase request (only for an item that is available and not my own)
START TRANSACTION;
INSERT INTO PurchaseRequest (purchaseRequestDate, offeredPrice, message, status, buyerId, itemId)
SELECT CURDATE(), 20.00, 'Can I pick it up this week?', 'PENDING', @userId, i.itemId
FROM SecondhandItem i
WHERE i.itemId = 38 AND i.status = 'AVAILABLE' AND i.sellerId <> @userId;
SELECT ROW_COUNT() AS requestsCreated;
SELECT purchaseRequestId, itemId, offeredPrice, status FROM PurchaseRequest
WHERE buyerId = @userId AND itemId = 38;
ROLLBACK;

-- 6.4 UC-3401 / UC-4401 Accept a request: create the order, reserve the item, reject
START TRANSACTION;
SET @requestId = 30;
SET @acceptedItem = (SELECT itemId FROM PurchaseRequest WHERE purchaseRequestId = @requestId);
SET @pickupPointId = (SELECT pp.pickupPointId FROM PickupPoint pp
                      JOIN SecondhandItem i ON i.sellerId = pp.ownerId
                      WHERE i.itemId = @acceptedItem AND pp.activeStatus = 1
                      ORDER BY pp.pickupPointId LIMIT 1);
SELECT itemId, status FROM SecondhandItem WHERE itemId = @acceptedItem FOR UPDATE;
INSERT INTO TransactionOrder
  (agreedPrice, transactionDate, pickupDateTime, status, purchaseRequestId, pickupPointId)
SELECT pr.offeredPrice, CURDATE(), DATE_ADD(NOW(), INTERVAL 3 DAY), 'PENDING', pr.purchaseRequestId, @pickupPointId
FROM PurchaseRequest pr
JOIN SecondhandItem i ON i.itemId = pr.itemId
WHERE pr.purchaseRequestId = @requestId AND pr.status = 'PENDING' AND i.status = 'AVAILABLE';
SET @orderId = LAST_INSERT_ID();
UPDATE PurchaseRequest
   SET status = IF(purchaseRequestId = @requestId, 'ACCEPTED', 'REJECTED')
 WHERE itemId = @acceptedItem AND status = 'PENDING';
UPDATE SecondhandItem SET status = 'RESERVED' WHERE itemId = @acceptedItem AND status = 'AVAILABLE';
SELECT t.transactionId, t.status AS orderStatus, i.status AS itemStatus, pr.status AS requestStatus
FROM TransactionOrder t
JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
JOIN SecondhandItem i   ON i.itemId = pr.itemId
WHERE t.transactionId = @orderId;
ROLLBACK;

-- 6.5 UC-3403 The seller confirms the order is complete (the item becomes SOLD)
START TRANSACTION;
UPDATE TransactionOrder SET status = 'COMPLETED', completedAt = NOW()
 WHERE transactionId = @transactionId AND status = 'PENDING';
UPDATE SecondhandItem i
  JOIN PurchaseRequest pr ON pr.itemId = i.itemId
  JOIN TransactionOrder t ON t.purchaseRequestId = pr.purchaseRequestId
   SET i.status = 'SOLD'
 WHERE t.transactionId = @transactionId AND t.status = 'COMPLETED';
SELECT t.transactionId, t.status AS orderStatus, t.completedAt, i.status AS itemStatus
FROM TransactionOrder t
JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
JOIN SecondhandItem i   ON i.itemId = pr.itemId
WHERE t.transactionId = @transactionId;
ROLLBACK;

-- 6.6 UC-4403 Cancel a pending order (the item is open for new requests again)
START TRANSACTION;
SET @cancelId = 26;
UPDATE TransactionOrder SET status = 'CANCELLED', cancelledAt = NOW()
 WHERE transactionId = @cancelId AND status = 'PENDING';
UPDATE SecondhandItem i
  JOIN PurchaseRequest pr ON pr.itemId = i.itemId
  JOIN TransactionOrder t ON t.purchaseRequestId = pr.purchaseRequestId
   SET i.status = 'AVAILABLE'
 WHERE t.transactionId = @cancelId AND t.status = 'CANCELLED' AND i.status = 'RESERVED';
SELECT t.transactionId, t.status AS orderStatus, t.cancelledAt, i.status AS itemStatus
FROM TransactionOrder t
JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
JOIN SecondhandItem i   ON i.itemId = pr.itemId
WHERE t.transactionId = @cancelId;
ROLLBACK;

-- 6.7 UC-4501 The seller of completed order 13 reviews the buyer (a BuyerReview).
START TRANSACTION;
SET @reviewTx = 13;
INSERT INTO TransactionReview (reviewDate, rating, comment, reviewStatus, authorId, recipientId)
SELECT CURDATE(), 5, 'Prompt and polite.', 'PUBLISHED', i.sellerId, pr.buyerId
FROM TransactionOrder t
JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
JOIN SecondhandItem i   ON i.itemId = pr.itemId
WHERE t.transactionId = @reviewTx AND t.status = 'COMPLETED'
  AND NOT EXISTS (SELECT 1 FROM BuyerReview b WHERE b.transactionId = t.transactionId);
SET @newReview = LAST_INSERT_ID();
INSERT INTO BuyerReview (reviewId, transactionId) VALUES (@newReview, @reviewTx);
SELECT br.transactionId, r.reviewId, r.rating, r.authorId AS sellerId, r.recipientId AS buyerId
FROM BuyerReview br JOIN TransactionReview r ON r.reviewId = br.reviewId
WHERE br.transactionId = @reviewTx;
ROLLBACK;

-- 6.8 UC-1501 Report an item, and report an order as one of its parties
START TRANSACTION;
INSERT INTO Report (reason, description, reportDate, status, reporterId)
VALUES ('WRONG_DESCRIPTION', 'The photos do not match the listing.', CURDATE(), 'RECEIVED', @userId);
INSERT INTO ItemReport (reportId, itemId) VALUES (LAST_INSERT_ID(), 33);
INSERT INTO Report (reason, description, reportDate, status, reporterId)
VALUES ('HARASSMENT', 'Abusive messages after the order.', CURDATE(), 'RECEIVED', 3);
INSERT INTO TransactionReport (reportId, transactionId) VALUES (LAST_INSERT_ID(), 18);
SELECT r.reportId, r.reason, r.status, IF(ir.reportId IS NOT NULL, 'item', 'order') AS targetType
FROM Report r
LEFT JOIN ItemReport ir ON ir.reportId = r.reportId
WHERE r.reportId >= LAST_INSERT_ID() - 1;
ROLLBACK;

-- 6.9 UC-3202 / UC-5501 Remove an item: it is taken down and its pending requests are rejected
START TRANSACTION;
UPDATE SecondhandItem SET status = 'REMOVED' WHERE itemId = 35 AND status = 'AVAILABLE';
UPDATE PurchaseRequest SET status = 'REJECTED' WHERE itemId = 35 AND status = 'PENDING';
SELECT i.itemId, i.status AS itemStatus, pr.purchaseRequestId, pr.status AS requestStatus
FROM SecondhandItem i JOIN PurchaseRequest pr ON pr.itemId = i.itemId
WHERE i.itemId = 35;
ROLLBACK;

-- 6.10 UC-5501 Handle a report: start review, resolve it, take the item down and suspend the seller
START TRANSACTION;
UPDATE Report SET status = 'UNDER_REVIEW', handledById = @adminId
 WHERE reportId = @reportId AND status = 'RECEIVED';
UPDATE Report SET status = 'RESOLVED', handledById = @adminId, handledAt = NOW(),
                  resolutionNote = 'Item taken down and seller suspended.'
 WHERE reportId = @reportId AND status = 'UNDER_REVIEW';
SET @reportedItem = (SELECT itemId FROM ItemReport WHERE reportId = @reportId);
UPDATE SecondhandItem SET status = 'REMOVED' WHERE itemId = @reportedItem;
UPDATE `User` SET accountStatus = 'SUSPENDED'
 WHERE userId = (SELECT sellerId FROM SecondhandItem WHERE itemId = @reportedItem);
SELECT r.reportId, r.status, r.handledById, r.handledAt, r.resolutionNote,
       i.itemId, i.status AS itemStatus, u.userId AS sellerId, u.accountStatus AS sellerAccount
FROM Report r
JOIN ItemReport ir ON ir.reportId = r.reportId
JOIN SecondhandItem i ON i.itemId = ir.itemId
JOIN `User` u ON u.userId = i.sellerId
WHERE r.reportId = @reportId;
ROLLBACK;

-- 6.11 UC-5201 Switch a tag off (it stays on old items but is no longer offered)
START TRANSACTION;
UPDATE ItemTag SET activeStatus = 0 WHERE tagId = 3;
SELECT t.tagId, t.tagName, t.activeStatus, COUNT(it.itemId) AS itemsWithTag
FROM ItemTag t LEFT JOIN ItemTags it ON it.tagId = t.tagId
WHERE t.tagId = 3 GROUP BY t.tagId;
ROLLBACK;

-- ============================================================
-- 7. Administrator overview (UC-5201, UC-5501, UC-5601)
-- ============================================================

-- 7.1 Tags with usage and whether they are switched on
SELECT t.tagId, t.tagName, t.activeStatus, COUNT(it.itemId) AS items,
       SUM(i.status = 'AVAILABLE') AS availableItems
FROM ItemTag t
LEFT JOIN ItemTags it ON it.tagId = t.tagId
LEFT JOIN SecondhandItem i ON i.itemId = it.itemId
GROUP BY t.tagId, t.tagName, t.activeStatus
ORDER BY items DESC, t.tagName;

-- 7.2 UC-5601 Listings, requests and orders by status
SELECT 'items' AS what, status, COUNT(*) AS n FROM SecondhandItem GROUP BY status
UNION ALL SELECT 'requests', status, COUNT(*) FROM PurchaseRequest GROUP BY status
UNION ALL SELECT 'orders', status, COUNT(*) FROM TransactionOrder GROUP BY status
UNION ALL SELECT 'reports', status, COUNT(*) FROM Report GROUP BY status
ORDER BY what, status;

-- 7.3 UC-5601 Activity by month: new listings, orders created and completed, value traded
SELECT m.month,
       (SELECT COUNT(*) FROM SecondhandItem i WHERE DATE_FORMAT(i.listingDate, '%Y-%m') = m.month) AS newListings,
       (SELECT COUNT(*) FROM TransactionOrder t WHERE DATE_FORMAT(t.transactionDate, '%Y-%m') = m.month) AS ordersCreated,
       (SELECT COUNT(*) FROM TransactionOrder t
         WHERE t.status = 'COMPLETED' AND DATE_FORMAT(t.completedAt, '%Y-%m') = m.month) AS ordersCompleted,
       (SELECT COALESCE(SUM(t.agreedPrice), 0) FROM TransactionOrder t
         WHERE t.status = 'COMPLETED' AND DATE_FORMAT(t.completedAt, '%Y-%m') = m.month) AS valueTraded
FROM (SELECT DATE_FORMAT(listingDate, '%Y-%m') AS month FROM SecondhandItem
      UNION SELECT DATE_FORMAT(transactionDate, '%Y-%m') FROM TransactionOrder) m
ORDER BY m.month;

-- 7.4 UC-5601 Campus comparison: users, listings, and completed sales by seller campus
SELECT c.campusName,
       COUNT(DISTINCT u.userId) AS users,
       COUNT(DISTINCT i.itemId) AS listings,
       COUNT(DISTINCT CASE WHEN t.status = 'COMPLETED' THEN t.transactionId END) AS completedSales,
       COALESCE(SUM(CASE WHEN t.status = 'COMPLETED' THEN t.agreedPrice END), 0) AS salesValue
FROM Campus c
LEFT JOIN `User` u ON u.campusId = c.campusId
LEFT JOIN SecondhandItem i ON i.sellerId = u.userId
LEFT JOIN PurchaseRequest pr ON pr.itemId = i.itemId
LEFT JOIN TransactionOrder t ON t.purchaseRequestId = pr.purchaseRequestId
GROUP BY c.campusId, c.campusName
ORDER BY completedSales DESC, c.campusName;

-- 7.5 UC-5601 Top sellers: completed sales, revenue and average rating received
SELECT u.userId, CONCAT(u.firstName, ' ', u.lastName) AS seller,
       COUNT(t.transactionId) AS completedSales,
       SUM(t.agreedPrice) AS revenue,
       (SELECT ROUND(AVG(r.rating), 2) FROM TransactionReview r WHERE r.recipientId = u.userId) AS avgRatingReceived
FROM TransactionOrder t
JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
JOIN SecondhandItem i   ON i.itemId = pr.itemId
JOIN `User` u           ON u.userId = i.sellerId
WHERE t.status = 'COMPLETED'
GROUP BY u.userId, u.firstName, u.lastName
ORDER BY completedSales DESC, revenue DESC, u.userId
LIMIT 5;

-- 7.6 UC-5601 Categories by sales and by how many request an item receives on average
SELECT c.categoryName,
       COUNT(DISTINCT i.itemId) AS items,
       COUNT(DISTINCT CASE WHEN i.status = 'SOLD' THEN i.itemId END) AS sold,
       ROUND(COUNT(pr.purchaseRequestId) / COUNT(DISTINCT i.itemId), 2) AS requestsPerItem,
       ROUND(AVG(i.askingPrice), 2) AS avgAskingPrice
FROM ItemCategory c
JOIN SecondhandItem i ON i.categoryId = c.categoryId
LEFT JOIN PurchaseRequest pr ON pr.itemId = i.itemId
GROUP BY c.categoryId, c.categoryName
ORDER BY sold DESC, items DESC;

-- 7.7 UC-5601 Request-to-order conversion and discount against the asking price
SELECT COUNT(*) AS requests,
       SUM(pr.status = 'ACCEPTED') AS accepted,
       ROUND(SUM(pr.status = 'ACCEPTED') / COUNT(*) * 100, 1) AS acceptedPercent,
       ROUND(AVG(CASE WHEN pr.status = 'ACCEPTED'
                      THEN (1 - pr.offeredPrice / NULLIF(i.askingPrice, 0)) * 100 END), 1) AS avgDiscountPercent
FROM PurchaseRequest pr
JOIN SecondhandItem i ON i.itemId = pr.itemId;

-- 7.8 UC-5601 Active users: what each user did (users with no activity show zeros)
SELECT u.userId, CONCAT(u.firstName, ' ', u.lastName) AS user, u.accountStatus,
       (SELECT COUNT(*) FROM SecondhandItem i WHERE i.sellerId = u.userId)  AS listings,
       (SELECT COUNT(*) FROM PurchaseRequest pr WHERE pr.buyerId = u.userId) AS requests,
       (SELECT COUNT(*) FROM Message m WHERE m.authorId = u.userId)         AS messages,
       (SELECT COUNT(*) FROM TransactionReview r WHERE r.authorId = u.userId) AS reviewsWritten
FROM `User` u
ORDER BY listings + requests DESC, messages DESC, u.userId
LIMIT 10;

-- 7.9 UC-5501 Report statistics: by reason and type, with handling time
SELECT r.reason,
       IF(ir.reportId IS NOT NULL, 'item', 'order') AS targetType,
       COUNT(*) AS reports,
       SUM(r.status IN ('RECEIVED', 'UNDER_REVIEW')) AS stillOpen,
       ROUND(AVG(DATEDIFF(r.handledAt, r.reportDate)), 1) AS avgDaysToHandle
FROM Report r
LEFT JOIN ItemReport ir ON ir.reportId = r.reportId
GROUP BY r.reason, targetType
ORDER BY reports DESC, r.reason;

-- 7.10 UC-5501 Users who were reported most (as the seller of the item or order)
SELECT u.userId, CONCAT(u.firstName, ' ', u.lastName) AS user, u.accountStatus,
       COUNT(*) AS reportsAgainst,
       SUM(r.status = 'RESOLVED') AS resolved
FROM Report r
LEFT JOIN ItemReport ir        ON ir.reportId = r.reportId
LEFT JOIN SecondhandItem ii    ON ii.itemId = ir.itemId
LEFT JOIN TransactionReport tr ON tr.reportId = r.reportId
LEFT JOIN TransactionOrder t   ON t.transactionId = tr.transactionId
LEFT JOIN PurchaseRequest p    ON p.purchaseRequestId = t.purchaseRequestId
LEFT JOIN SecondhandItem ti    ON ti.itemId = p.itemId
JOIN `User` u ON u.userId = COALESCE(ii.sellerId, ti.sellerId)
GROUP BY u.userId, u.firstName, u.lastName, u.accountStatus
ORDER BY reportsAgainst DESC, u.userId
LIMIT 5;

-- ============================================================
-- 8. Data health checks (every query should return 0)
-- ============================================================
SELECT 'order status does not match item status' AS `check`, COUNT(*) AS violations
FROM TransactionOrder t
JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
JOIN SecondhandItem i   ON i.itemId = pr.itemId
WHERE (t.status = 'COMPLETED' AND i.status <> 'SOLD')
   OR (t.status = 'PENDING'   AND i.status <> 'RESERVED')
   OR (t.status = 'CANCELLED' AND i.status <> 'AVAILABLE')
UNION ALL
SELECT 'buyer is also the seller', COUNT(*)
FROM PurchaseRequest pr JOIN SecondhandItem i ON i.itemId = pr.itemId
WHERE pr.buyerId = i.sellerId
UNION ALL
SELECT 'item with more than one active order', COUNT(*) FROM (
  SELECT pr.itemId FROM TransactionOrder t
  JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
  WHERE t.status <> 'CANCELLED' GROUP BY pr.itemId HAVING COUNT(*) > 1) x
UNION ALL
SELECT 'pending request on an item that is not available', COUNT(*)
FROM PurchaseRequest pr JOIN SecondhandItem i ON i.itemId = pr.itemId
WHERE pr.status = 'PENDING' AND i.status IN ('SOLD', 'REMOVED')
UNION ALL
SELECT 'review on an order that is not completed', COUNT(*) FROM (
  SELECT transactionId FROM BuyerReview UNION ALL SELECT transactionId FROM SellerReview) x
JOIN TransactionOrder t ON t.transactionId = x.transactionId WHERE t.status <> 'COMPLETED'
UNION ALL
SELECT 'buyer review not written by the seller about the buyer', COUNT(*)
FROM BuyerReview b JOIN TransactionReview r ON r.reviewId = b.reviewId
JOIN TransactionOrder t ON t.transactionId = b.transactionId
JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
JOIN SecondhandItem i ON i.itemId = pr.itemId
WHERE r.authorId <> i.sellerId OR r.recipientId <> pr.buyerId
UNION ALL
SELECT 'seller review not written by the buyer about the seller', COUNT(*)
FROM SellerReview s JOIN TransactionReview r ON r.reviewId = s.reviewId
JOIN TransactionOrder t ON t.transactionId = s.transactionId
JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
JOIN SecondhandItem i ON i.itemId = pr.itemId
WHERE r.authorId <> pr.buyerId OR r.recipientId <> i.sellerId
UNION ALL
SELECT 'review that is neither buyer nor seller review', COUNT(*)
FROM TransactionReview r
WHERE r.reviewId NOT IN (SELECT reviewId FROM BuyerReview)
  AND r.reviewId NOT IN (SELECT reviewId FROM SellerReview)
UNION ALL
SELECT 'report that is neither item nor order report', COUNT(*)
FROM Report r
WHERE r.reportId NOT IN (SELECT reportId FROM ItemReport)
  AND r.reportId NOT IN (SELECT reportId FROM TransactionReport)
UNION ALL
SELECT 'handled report without handler or note, or open report with note', COUNT(*)
FROM Report
WHERE (status IN ('RESOLVED', 'DISMISSED') AND (handledById IS NULL OR handledAt IS NULL OR resolutionNote IS NULL))
   OR (status = 'RECEIVED' AND (handledById IS NOT NULL OR handledAt IS NOT NULL OR resolutionNote IS NOT NULL))
UNION ALL
SELECT 'message written by a non-participant', COUNT(*)
FROM Message m
WHERE NOT EXISTS (SELECT 1 FROM ConversationParticipant p
                  WHERE p.conversationId = m.conversationId AND p.userId = m.authorId)
UNION ALL
SELECT 'conversation without the item seller as participant', COUNT(*)
FROM Conversation c JOIN SecondhandItem i ON i.itemId = c.itemId
WHERE NOT EXISTS (SELECT 1 FROM ConversationParticipant p
                  WHERE p.conversationId = c.conversationId AND p.userId = i.sellerId)
UNION ALL
SELECT 'order pickup point is not owned by the order seller', COUNT(*)
FROM TransactionOrder t
JOIN PurchaseRequest pr ON pr.purchaseRequestId = t.purchaseRequestId
JOIN SecondhandItem i   ON i.itemId = pr.itemId
JOIN PickupPoint pp     ON pp.pickupPointId = t.pickupPointId
WHERE pp.ownerId <> i.sellerId
UNION ALL
SELECT 'user e-mail domain differs from the campus domain', COUNT(*)
FROM `User` u JOIN Campus c ON c.campusId = u.campusId
WHERE SUBSTRING_INDEX(u.email, '@', -1) <> c.emailDomain;
