-- Delete-rule tests for marketplace.sql

USE seattle_marketplace;

DROP PROCEDURE IF EXISTS _try_delete;
DROP TEMPORARY TABLE IF EXISTS _delete_results;
CREATE TEMPORARY TABLE _delete_results (
  seq        INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  rule_name  VARCHAR(90) NOT NULL,
  expected   VARCHAR(10) NOT NULL,
  actual     VARCHAR(10) NOT NULL,
  leftover   INT NULL
) ENGINE=InnoDB;

DELIMITER //
CREATE PROCEDURE _try_delete(IN p_rule VARCHAR(90), IN p_expected VARCHAR(10),
                             IN p_delete TEXT, IN p_leftover TEXT)
BEGIN
  DECLARE v_blocked INT DEFAULT 0;
  DECLARE CONTINUE HANDLER FOR SQLSTATE '23000' SET v_blocked = 1;
  SET @_sql = p_delete;
  PREPARE _st FROM @_sql; EXECUTE _st; DEALLOCATE PREPARE _st;
  SET @_left = NULL;
  IF v_blocked = 0 AND p_leftover IS NOT NULL THEN
    SET @_sql = p_leftover;
    PREPARE _st FROM @_sql; EXECUTE _st; DEALLOCATE PREPARE _st;
  END IF;
  INSERT INTO _delete_results (rule_name, expected, actual, leftover)
  VALUES (p_rule, p_expected, IF(v_blocked = 1, 'blocked', 'allowed'), @_left);
END//
DELIMITER ;

START TRANSACTION;

CALL _try_delete('User with listings (SecondhandItem.sellerId)', 'blocked',
  'DELETE FROM `User` WHERE userId = 12', NULL);
CALL _try_delete('User who wrote messages (Message.authorId)', 'blocked',
  'DELETE FROM `User` WHERE userId = (SELECT authorId FROM Message WHERE messageId = 1)', NULL);
CALL _try_delete('User who wrote a review (TransactionReview.authorId)', 'blocked',
  'DELETE FROM `User` WHERE userId = (SELECT authorId FROM TransactionReview WHERE reviewId = 1)', NULL);
CALL _try_delete('User who filed a report (Report.reporterId)', 'blocked',
  'DELETE FROM `User` WHERE userId = (SELECT reporterId FROM Report WHERE reportId = 1)', NULL);
CALL _try_delete('User who handled a report (Report.handledById)', 'blocked',
  'DELETE FROM `User` WHERE userId = (SELECT handledById FROM Report WHERE handledById IS NOT NULL LIMIT 1)', NULL);
CALL _try_delete('Campus with users (User.campusId)', 'blocked',
  'DELETE FROM Campus WHERE campusId = 1', NULL);
CALL _try_delete('Role that is a primary role (User.primaryRoleId)', 'blocked',
  'DELETE FROM `Role` WHERE roleId = 1', NULL);
CALL _try_delete('Role that users hold (UserHasRole.roleId)', 'blocked',
  'DELETE FROM `Role` WHERE roleId = 5', NULL);
CALL _try_delete('Category that has subcategories (ItemCategory.parentCategoryId)', 'blocked',
  'DELETE FROM ItemCategory WHERE categoryId = 7', NULL);
CALL _try_delete('Category that has items (SecondhandItem.categoryId)', 'blocked',
  'DELETE FROM ItemCategory WHERE categoryId = 2', NULL);
CALL _try_delete('Tag that is used (ItemTags.tagId)', 'blocked',
  'DELETE FROM ItemTag WHERE tagId = 1', NULL);
CALL _try_delete('Item with purchase requests (PurchaseRequest.itemId)', 'blocked',
  'DELETE FROM SecondhandItem WHERE itemId = 1', NULL);
CALL _try_delete('Item with conversations (Conversation.itemId)', 'blocked',
  'DELETE FROM SecondhandItem WHERE itemId = 10', NULL);
CALL _try_delete('Item that was reported (ItemReport.itemId)', 'blocked',
  'DELETE FROM SecondhandItem WHERE itemId = (SELECT itemId FROM ItemReport WHERE reportId = 1)', NULL);
CALL _try_delete('Purchase request that became an order (TransactionOrder.purchaseRequestId)', 'blocked',
  'DELETE FROM PurchaseRequest WHERE purchaseRequestId = 1', NULL);
CALL _try_delete('Pickup point used by an order (TransactionOrder.pickupPointId)', 'blocked',
  'DELETE FROM PickupPoint WHERE pickupPointId = (SELECT pickupPointId FROM TransactionOrder WHERE transactionId = 1)', NULL);
CALL _try_delete('Address used by a pickup point (PickupPoint.addressId)', 'blocked',
  'DELETE FROM Address WHERE addressId = 1', NULL);
CALL _try_delete('Order that has reviews (BuyerReview.transactionId)', 'blocked',
  'DELETE FROM TransactionOrder WHERE transactionId = (SELECT transactionId FROM BuyerReview LIMIT 1)', NULL);
CALL _try_delete('Order that was reported (TransactionReport.transactionId)', 'blocked',
  'DELETE FROM TransactionOrder WHERE transactionId = (SELECT transactionId FROM TransactionReport LIMIT 1)', NULL);
CALL _try_delete('Conversation that has messages (Message.conversationId)', 'blocked',
  'DELETE FROM Conversation WHERE conversationId = 1', NULL);

INSERT INTO `User` (userId, firstName, lastName, email, accountStatus, campusId, primaryRoleId)
VALUES (90001, 'Temp', 'Seller', 'temp.seller@example.edu', 'ACTIVE', 1, 1);
INSERT INTO UserHasRole (userId, roleId) VALUES (90001, 1);
INSERT INTO PickupPoint (pickupPointId, pickupPointName, addressId, activeStatus, ownerId)
VALUES (90001, 'Temp spot', 1, 1, 90001);
INSERT INTO SecondhandItem (itemId, title, askingPrice, status, `condition`, categoryId, sellerId)
VALUES (90001, 'Temp item', 5, 'AVAILABLE', 'GOOD', 1, 90001);
INSERT INTO ItemPhoto (itemId, photoURL, displayOrder) VALUES (90001, 'https://example.com/tmp.jpg', 1);
INSERT INTO ItemTags (itemId, tagId) VALUES (90001, 1);
INSERT INTO SavedItem (dateSaved, itemId, userId) VALUES (CURDATE(), 90001, 2), (CURDATE(), 1, 90001);
INSERT INTO Conversation (conversationId, createdAt, itemId, creatorId) VALUES (90001, NOW(), 1, 2);
INSERT INTO ConversationParticipant (conversationId, userId) VALUES (90001, 2), (90001, 3);

CALL _try_delete('Item takes its photos, tag links and saves with it', 'allowed',
  'DELETE FROM SecondhandItem WHERE itemId = 90001',
  'SELECT (SELECT COUNT(*) FROM ItemPhoto WHERE itemId = 90001) + (SELECT COUNT(*) FROM ItemTags WHERE itemId = 90001) + (SELECT COUNT(*) FROM SavedItem WHERE itemId = 90001) INTO @_left');
CALL _try_delete('User takes role links, saved items and unused pickup points with it', 'allowed',
  'DELETE FROM `User` WHERE userId = 90001',
  'SELECT (SELECT COUNT(*) FROM UserHasRole WHERE userId = 90001) + (SELECT COUNT(*) FROM SavedItem WHERE userId = 90001) + (SELECT COUNT(*) FROM PickupPoint WHERE ownerId = 90001) INTO @_left');
CALL _try_delete('Empty conversation takes its participants with it', 'allowed',
  'DELETE FROM Conversation WHERE conversationId = 90001',
  'SELECT COUNT(*) INTO @_left FROM ConversationParticipant WHERE conversationId = 90001');

SET @buyerReview = (SELECT MIN(reviewId) FROM BuyerReview);
SET @sellerReview = (SELECT MIN(reviewId) FROM SellerReview);
CALL _try_delete('Review takes its BuyerReview row with it', 'allowed',
  'DELETE FROM TransactionReview WHERE reviewId = @buyerReview',
  'SELECT COUNT(*) INTO @_left FROM BuyerReview WHERE reviewId = @buyerReview');
CALL _try_delete('Review takes its SellerReview row with it', 'allowed',
  'DELETE FROM TransactionReview WHERE reviewId = @sellerReview',
  'SELECT COUNT(*) INTO @_left FROM SellerReview WHERE reviewId = @sellerReview');

SET @itemReport = (SELECT MIN(reportId) FROM ItemReport);
SET @txReport = (SELECT MIN(reportId) FROM TransactionReport);
CALL _try_delete('Report takes its ItemReport row with it', 'allowed',
  'DELETE FROM Report WHERE reportId = @itemReport',
  'SELECT COUNT(*) INTO @_left FROM ItemReport WHERE reportId = @itemReport');
CALL _try_delete('Report takes its TransactionReport row with it', 'allowed',
  'DELETE FROM Report WHERE reportId = @txReport',
  'SELECT COUNT(*) INTO @_left FROM TransactionReport WHERE reportId = @txReport');

SELECT seq, rule_name, expected, actual, leftover,
       IF(expected = actual AND COALESCE(leftover, 0) = 0, 'PASS', 'FAIL') AS result
FROM _delete_results ORDER BY seq;
SELECT SUM(expected = actual AND COALESCE(leftover, 0) = 0) AS passed,
       SUM(NOT (expected = actual AND COALESCE(leftover, 0) = 0)) AS failed
FROM _delete_results;

ROLLBACK;
DROP PROCEDURE _try_delete;
DROP TEMPORARY TABLE _delete_results;
