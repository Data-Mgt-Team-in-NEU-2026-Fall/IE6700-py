-- ================= DIAGRAM 1: User identity =================
-- D1.1  All users with their campus and primary role
SELECT u.userId, u.firstName, u.lastName, u.email,
       c.campusName, r.roleName AS primaryRole
FROM `User` u
JOIN Campus c   ON c.campusId = u.campusId
JOIN UserRole r ON r.roleId = u.primaryRoleId
ORDER BY u.userId;

-- D1.2  All roles of one user (:userId)
SELECT r.roleId, r.roleName
FROM UserHasRole uh
JOIN UserRole r ON r.roleId = uh.roleId
WHERE uh.userId = :userId;

-- D1.3  Number of users per campus
SELECT c.campusId, c.campusName, COUNT(u.userId) AS userCount
FROM Campus c
LEFT JOIN `User` u ON u.campusId = c.campusId
GROUP BY c.campusId, c.campusName
ORDER BY userCount DESC;

-- D1.4  Users who hold more than one role
SELECT u.userId, u.firstName, u.lastName, COUNT(uh.roleId) AS roleCount
FROM `User` u
JOIN UserHasRole uh ON uh.userId = u.userId
GROUP BY u.userId, u.firstName, u.lastName
HAVING COUNT(uh.roleId) > 1;

-- D1.5  All users on one campus (:campusId)
SELECT userId, firstName, lastName, email
FROM `User`
WHERE campusId = :campusId
ORDER BY lastName, firstName;

-- ================= DIAGRAM 3: Messaging =================
-- D3.1  All conversations about one item (:itemId), with the creator
SELECT c.conversationId, c.createdAt, u.firstName AS creatorFirstName, u.lastName AS creatorLastName
FROM Conversation c
JOIN `User` u ON u.userId = c.creatorId
WHERE c.itemId = :itemId
ORDER BY c.createdAt;

-- D3.2  All messages in one conversation (:conversationId), with authors, oldest first
SELECT m.messageId, m.content, m.sentAt, u.firstName, u.lastName
FROM Message m
JOIN `User` u ON u.userId = m.authorId
WHERE m.conversationId = :conversationId
ORDER BY m.sentAt;

-- D3.3  All participants of one conversation (:conversationId)
SELECT u.userId, u.firstName, u.lastName,
       CASE WHEN u.userId = c.creatorId THEN 'creator' ELSE 'participant' END AS roleInConversation
FROM ConversationParticipant cp
JOIN `User` u ON u.userId = cp.userId
JOIN Conversation c ON c.conversationId = cp.conversationId
WHERE cp.conversationId = :conversationId;

-- D3.4  All conversations one user participates in (:userId), with message counts
SELECT c.conversationId, c.createdAt, c.itemId, COUNT(m.messageId) AS messageCount
FROM ConversationParticipant cp
JOIN Conversation c ON c.conversationId = cp.conversationId
LEFT JOIN Message m ON m.conversationId = c.conversationId
WHERE cp.userId = :userId
GROUP BY c.conversationId, c.createdAt, c.itemId
ORDER BY c.createdAt DESC;

-- D3.5  Conversations between two specified users (:userA, :userB) for a target product (:itemId)
SELECT c.conversationId, c.createdAt, c.creatorId
FROM Conversation c
WHERE c.itemId = :itemId
  AND EXISTS (SELECT 1 FROM ConversationParticipant cp
              WHERE cp.conversationId = c.conversationId AND cp.userId = :userA)
  AND EXISTS (SELECT 1 FROM ConversationParticipant cp
              WHERE cp.conversationId = c.conversationId AND cp.userId = :userB);

-- ================= DIAGRAM 4: Reviews and reports =================
-- D4.1  All reviews written by one user (:userId)
SELECT tr.reviewId, tr.reviewDate, tr.rating, tr.comment,
       tr.recipientId, tr.reviewStatus
FROM TransactionReview tr
WHERE tr.authorId = :userId
ORDER BY tr.reviewDate DESC;

-- D4.2  All reviews received by one user (:userId), with average rating
SELECT tr.reviewId, tr.reviewDate, tr.rating, tr.comment, tr.authorId
FROM TransactionReview tr
WHERE tr.recipientId = :userId
ORDER BY tr.reviewDate DESC;

SELECT AVG(rating) AS averageRatingReceived, COUNT(*) AS reviewCount
FROM TransactionReview
WHERE recipientId = :userId;

-- D4.3  Buyer review and seller review of one transaction (:transactionId)
SELECT 'buyer' AS reviewType, tr.reviewId, tr.rating, tr.comment, tr.authorId, tr.recipientId
FROM BuyerReview br
JOIN TransactionReview tr ON tr.reviewId = br.reviewId
WHERE br.transactionId = :transactionId
UNION ALL
SELECT 'seller' AS reviewType, tr.reviewId, tr.rating, tr.comment, tr.authorId, tr.recipientId
FROM SellerReview sr
JOIN TransactionReview tr ON tr.reviewId = sr.reviewId
WHERE sr.transactionId = :transactionId;

-- D4.4  Total review count of one transaction (:transactionId)
SELECT (SELECT COUNT(*) FROM BuyerReview WHERE transactionId = :transactionId)
     + (SELECT COUNT(*) FROM SellerReview WHERE transactionId = :transactionId)
       AS totalReviews;

-- D4.5  All product (item) reports
SELECT ir.reportId, r.reason, r.reportDate, r.status, r.reporterId, ir.itemId
FROM ItemReport ir
JOIN Report r ON r.reportId = ir.reportId
ORDER BY r.reportDate DESC;

-- D4.6  Total number of product reports in the system
SELECT COUNT(*) AS totalProductReports FROM ItemReport;

-- D4.7  Transaction reports that still require admin handling (status = Pending)
SELECT tr.reportId, r.reason, r.reportDate, r.reporterId, tr.transactionId
FROM TransactionReport tr
JOIN Report r ON r.reportId = tr.reportId
WHERE r.status = 'Pending'
ORDER BY r.reportDate;

SELECT COUNT(*) AS transactionReportsNeedingAdmin
FROM TransactionReport tr
JOIN Report r ON r.reportId = tr.reportId
WHERE r.status = 'Pending';

-- D4.8  All reports submitted by one user (:userId), split by type
SELECT r.reportId, r.reason, r.status, r.reportDate,
       CASE WHEN ir.reportId IS NOT NULL THEN 'item'
            WHEN tr.reportId IS NOT NULL THEN 'transaction' END AS reportType
FROM Report r
LEFT JOIN ItemReport ir ON ir.reportId = r.reportId
LEFT JOIN TransactionReport tr ON tr.reportId = r.reportId
WHERE r.reporterId = :userId
ORDER BY r.reportDate DESC;
